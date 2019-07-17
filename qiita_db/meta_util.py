r"""
Util functions (:mod: `qiita_db.meta_util`)
===========================================

..currentmodule:: qiita_db.meta_util

This module provides utility functions that use the ORM objects. ORM objects
CANNOT import from this file.

Methods
-------

..autosummary::
    :toctree: generated/

    get_lat_longs
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

from os import stat, rename
from os.path import join, relpath, basename
from time import strftime, localtime
import matplotlib.pyplot as plt
import matplotlib as mpl
from base64 import b64encode
from urllib.parse import quote
from io import BytesIO
from future.utils import viewitems
from datetime import datetime
from tarfile import open as topen, TarInfo
from hashlib import md5
from re import sub
from json import loads, dump, dumps

from qiita_db.util import create_nested_path
from qiita_core.qiita_settings import qiita_config, r_client
from qiita_core.configuration_manager import ConfigurationManager
import qiita_db as qdb


def _get_data_fpids(constructor, object_id):
    """Small function for getting filepath IDS associated with data object

    Parameters
    ----------
    constructor : a subclass of BaseData
        E.g., RawData, PreprocessedData, or ProcessedData
    object_id : int
        The ID of the data object

    Returns
    -------
    set of int
    """
    with qdb.sql_connection.TRN:
        obj = constructor(object_id)
        return {fpid for fpid, _, _ in obj.get_filepaths()}


def validate_filepath_access_by_user(user, filepath_id):
    """Validates if the user has access to the filepath_id

    Parameters
    ----------
    user : User object
        The user we are interested in
    filepath_id : int
        The filepath id

    Returns
    -------
    bool
        If the user has access or not to the filepath_id

    Notes
    -----
    Admins have access to all files so True is always returned
    """
    TRN = qdb.sql_connection.TRN
    with TRN:
        if user.level == "admin":
            # admins have access all files
            return True

        sql = """SELECT
            (SELECT array_agg(artifact_id)
             FROM qiita.artifact_filepath
             WHERE filepath_id = {0}) AS artifact,
            (SELECT array_agg(study_id)
             FROM qiita.sample_template_filepath
             WHERE filepath_id = {0}) AS sample_info,
            (SELECT array_agg(prep_template_id)
             FROM qiita.prep_template_filepath
             WHERE filepath_id = {0}) AS prep_info,
            (SELECT array_agg(analysis_id)
             FROM qiita.analysis_filepath
             WHERE filepath_id = {0}) AS analysis""".format(filepath_id)
        TRN.add(sql)

        arid, sid, pid, anid = TRN.execute_fetchflatten()

        # artifacts
        if arid:
            # [0] cause we should only have 1
            artifact = qdb.artifact.Artifact(arid[0])

            if artifact.visibility == 'public':
                # TODO: https://github.com/biocore/qiita/issues/1724
                if artifact.artifact_type in ['SFF', 'FASTQ', 'FASTA',
                                              'FASTA_Sanger',
                                              'per_sample_FASTQ']:
                    study = artifact.study
                    has_access = study.has_access(user, no_public=True)
                    if (not study.public_raw_download and not has_access):
                        return False
                return True
            else:
                study = artifact.study
                if study:
                    # let's take the visibility via the Study
                    return artifact.study.has_access(user)
                else:
                    analysis = artifact.analysis
                    return analysis in (
                        user.private_analyses | user.shared_analyses)
        # sample info files
        elif sid:
            # the visibility of the sample info file is given by the
            # study visibility
            # [0] cause we should only have 1
            return qdb.study.Study(sid[0]).has_access(user)
        # prep info files
        elif pid:
            # the prep access is given by it's artifacts, if the user has
            # access to any artifact, it should have access to the prep
            # [0] cause we should only have 1
            pt = qdb.metadata_template.prep_template.PrepTemplate(
                pid[0])
            a = pt.artifact
            # however, the prep info file could not have any artifacts attached
            # , in that case we will use the study access level
            if a is None:
                return qdb.study.Study(pt.study_id).has_access(user)
            else:
                if (a.visibility == 'public' or a.study.has_access(user)):
                    return True
                else:
                    for c in a.descendants.nodes():
                        if ((c.visibility == 'public' or
                             c.study.has_access(user))):
                            return True
            return False
        # analyses
        elif anid:
            # [0] cause we should only have 1
            aid = anid[0]
            analysis = qdb.analysis.Analysis(aid)
            return analysis in (
                user.private_analyses | user.shared_analyses)
        return False


def update_redis_stats():
    """Generate the system stats and save them in redis

    Returns
    -------
    list of str
        artifact filepaths that are not present in the file system
    """
    STUDY = qdb.study.Study
    studies = {'public': STUDY.get_by_status('public'),
               'private': STUDY.get_by_status('private'),
               'sandbox': STUDY.get_by_status('sandbox')}
    number_studies = {k: len(v) for k, v in viewitems(studies)}

    number_of_samples = {}
    ebi_samples_prep = {}
    num_samples_ebi = 0
    for k, sts in viewitems(studies):
        number_of_samples[k] = 0
        for s in sts:
            st = s.sample_template
            if st is not None:
                number_of_samples[k] += len(list(st.keys()))

            ebi_samples_prep_count = 0
            for pt in s.prep_templates():
                ebi_samples_prep_count += len([
                    1 for _, v in viewitems(pt.ebi_experiment_accessions)
                    if v is not None and v != ''])
            ebi_samples_prep[s.id] = ebi_samples_prep_count

            if s.sample_template is not None:
                num_samples_ebi += len([
                    1 for _, v in viewitems(
                        s.sample_template.ebi_sample_accessions)
                    if v is not None and v != ''])

    num_users = qdb.util.get_count('qiita.qiita_user')
    num_processing_jobs = qdb.util.get_count('qiita.processing_job')

    lat_longs = dumps(get_lat_longs())

    num_studies_ebi = len([k for k, v in viewitems(ebi_samples_prep)
                           if v >= 1])
    number_samples_ebi_prep = sum([v for _, v in viewitems(ebi_samples_prep)])

    # generating file size stats
    stats = []
    missing_files = []
    for k, sts in viewitems(studies):
        for s in sts:
            for a in s.artifacts():
                for x in a.filepaths:
                    try:
                        s = stat(x['fp'])
                        stats.append(
                            (x['fp_type'], s.st_size, strftime('%Y-%m',
                             localtime(s.st_ctime))))
                    except OSError:
                        missing_files.append(x['fp'])

    summary = {}
    all_dates = []
    for ft, size, ym in stats:
        if ft not in summary:
            summary[ft] = {}
        if ym not in summary[ft]:
            summary[ft][ym] = 0
            all_dates.append(ym)
        summary[ft][ym] += size
    all_dates = sorted(set(all_dates))

    # sorting summaries
    rm_from_data = ['html_summary', 'tgz', 'directory', 'raw_fasta', 'log',
                    'biom', 'raw_sff', 'raw_qual']
    ordered_summary = {}
    for dt in summary:
        if dt in rm_from_data:
            continue
        new_list = []
        current_value = 0
        for ad in all_dates:
            if ad in summary[dt]:
                current_value += summary[dt][ad]
            new_list.append(current_value)
        ordered_summary[dt] = new_list

    plot_order = sorted([(k, ordered_summary[k][-1]) for k in ordered_summary],
                        key=lambda x: x[1])

    # helper function to generate y axis, modified from:
    # http://stackoverflow.com/a/1094933
    def sizeof_fmt(value, position):
        number = None
        for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
            if abs(value) < 1024.0:
                number = "%3.1f%s" % (value, unit)
                break
            value /= 1024.0
        if number is None:
            number = "%.1f%s" % (value, 'Yi')
        return number

    all_dates_axis = range(len(all_dates))
    plt.locator_params(axis='y', nbins=10)
    plt.figure(figsize=(20, 10))
    for k, v in plot_order:
        plt.plot(all_dates_axis, ordered_summary[k], linewidth=2, label=k)

    plt.xticks(all_dates_axis, all_dates)
    plt.legend()
    plt.grid()
    ax = plt.gca()
    ax.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(sizeof_fmt))
    plt.xticks(rotation=90)
    plt.xlabel('Date')
    plt.ylabel('Storage space per data type')

    plot = BytesIO()
    plt.savefig(plot, format='png')
    plot.seek(0)
    img = 'data:image/png;base64,' + quote(b64encode(plot.getbuffer()))

    time = datetime.now().strftime('%m-%d-%y %H:%M:%S')

    portal = qiita_config.portal
    vals = [
        ('number_studies', number_studies, r_client.hmset),
        ('number_of_samples', number_of_samples, r_client.hmset),
        ('num_users', num_users, r_client.set),
        ('lat_longs', (lat_longs), r_client.set),
        ('num_studies_ebi', num_studies_ebi, r_client.set),
        ('num_samples_ebi', num_samples_ebi, r_client.set),
        ('number_samples_ebi_prep', number_samples_ebi_prep, r_client.set),
        ('img', img, r_client.set),
        ('time', time, r_client.set),
        ('num_processing_jobs', num_processing_jobs, r_client.set)]
    for k, v, f in vals:
        redis_key = '%s:stats:%s' % (portal, k)
        # important to "flush" variables to avoid errors
        r_client.delete(redis_key)
        f(redis_key, v)

    return missing_files


def get_lat_longs():
    """Retrieve the latitude and longitude of all the public samples in the DB

    Returns
    -------
    list of [float, float]
        The latitude and longitude for each sample in the database
    """
    with qdb.sql_connection.TRN:
        # getting all the public studies
        studies = qdb.study.Study.get_by_status('public')

        results = []
        if studies:
            # we are going to create multiple union selects to retrieve the
            # latigute and longitude of all available studies. Note that
            # UNION in PostgreSQL automatically removes duplicates
            sql_query = """
                SELECT {0}, CAST(sample_values->>'latitude' AS FLOAT),
                       CAST(sample_values->>'longitude' AS FLOAT)
                FROM qiita.sample_{0}
                WHERE sample_values->>'latitude' != 'NaN' AND
                      sample_values->>'longitude' != 'NaN' AND
                      isnumeric(sample_values->>'latitude') AND
                      isnumeric(sample_values->>'longitude')"""
            sql = [sql_query.format(s.id) for s in studies]
            sql = ' UNION '.join(sql)
            qdb.sql_connection.TRN.add(sql)

            # note that we are returning set to remove duplicates
            results = qdb.sql_connection.TRN.execute_fetchindex()

        return results


def generate_biom_and_metadata_release(study_status='public'):
    """Generate a list of biom/meatadata filepaths and a tgz of those files

    Parameters
    ----------
    study_status : str, optional
        The study status to search for. Note that this should always be set
        to 'public' but having this exposed helps with testing. The other
        options are 'private' and 'sandbox'
    """
    studies = qdb.study.Study.get_by_status(study_status)
    qiita_config = ConfigurationManager()
    working_dir = qiita_config.working_dir
    portal = qiita_config.portal
    bdir = qdb.util.get_db_files_base_dir()
    time = datetime.now().strftime('%m-%d-%y %H:%M:%S')

    data = []
    for s in studies:
        # [0] latest is first, [1] only getting the filepath
        sample_fp = relpath(s.sample_template.get_filepaths()[0][1], bdir)

        for a in s.artifacts(artifact_type='BIOM'):
            if a.processing_parameters is None or a.visibility != study_status:
                continue

            merging_schemes, parent_softwares = a.merging_scheme
            software = a.processing_parameters.command.software
            software = '%s v%s' % (software.name, software.version)

            for x in a.filepaths:
                if x['fp_type'] != 'biom' or 'only-16s' in x['fp']:
                    continue
                fp = relpath(x['fp'], bdir)
                for pt in a.prep_templates:
                    categories = pt.categories()
                    platform = ''
                    target_gene = ''
                    if 'platform' in categories:
                        platform = ', '.join(
                            set(pt.get_category('platform').values()))
                    if 'target_gene' in categories:
                        target_gene = ', '.join(
                            set(pt.get_category('target_gene').values()))
                    for _, prep_fp in pt.get_filepaths():
                        if 'qiime' not in prep_fp:
                            break
                    prep_fp = relpath(prep_fp, bdir)
                    # format: (biom_fp, sample_fp, prep_fp, qiita_artifact_id,
                    #          platform, target gene, merging schemes,
                    #          artifact software/version,
                    #          parent sofware/version)
                    data.append((fp, sample_fp, prep_fp, a.id, platform,
                                 target_gene, merging_schemes, software,
                                 parent_softwares))

    # writing text and tgz file
    ts = datetime.now().strftime('%m%d%y-%H%M%S')
    tgz_dir = join(working_dir, 'releases')
    create_nested_path(tgz_dir)
    tgz_name = join(tgz_dir, '%s-%s-building.tgz' % (portal, study_status))
    tgz_name_final = join(tgz_dir, '%s-%s.tgz' % (portal, study_status))
    txt_lines = [
        "biom fp\tsample fp\tprep fp\tqiita artifact id\tplatform\t"
        "target gene\tmerging scheme\tartifact software\tparent software"]
    with topen(tgz_name, "w|gz") as tgz:
        for biom_fp, sample_fp, prep_fp, aid, pform, tg, ms, asv, psv in data:
            txt_lines.append("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (
                biom_fp, sample_fp, prep_fp, aid, pform, tg, ms, asv, psv))
            tgz.add(join(bdir, biom_fp), arcname=biom_fp, recursive=False)
            tgz.add(join(bdir, sample_fp), arcname=sample_fp, recursive=False)
            tgz.add(join(bdir, prep_fp), arcname=prep_fp, recursive=False)
        info = TarInfo(name='%s-%s-%s.txt' % (portal, study_status, ts))
        txt_hd = BytesIO()
        txt_hd.write(bytes('\n'.join(txt_lines), 'ascii'))
        txt_hd.seek(0)
        info.size = len(txt_hd.read())
        txt_hd.seek(0)
        tgz.addfile(tarinfo=info, fileobj=txt_hd)

    with open(tgz_name, "rb") as f:
        md5sum = md5()
        for c in iter(lambda: f.read(4096), b""):
            md5sum.update(c)

    rename(tgz_name, tgz_name_final)

    vals = [
        ('filepath', tgz_name_final[len(working_dir):], r_client.set),
        ('md5sum', md5sum.hexdigest(), r_client.set),
        ('time', time, r_client.set)]
    for k, v, f in vals:
        redis_key = '%s:release:%s:%s' % (portal, study_status, k)
        # important to "flush" variables to avoid errors
        r_client.delete(redis_key)
        f(redis_key, v)


def generate_plugin_releases():
    """Generate releases for plugins
    """
    ARCHIVE = qdb.archive.Archive
    qiita_config = ConfigurationManager()
    working_dir = qiita_config.working_dir

    commands = [c for s in qdb.software.Software.iter(active=True)
                for c in s.commands if c.post_processing_cmd is not None]

    tnow = datetime.now()
    ts = tnow.strftime('%m%d%y-%H%M%S')
    tgz_dir = join(working_dir, 'releases', 'archive')
    create_nested_path(tgz_dir)
    tgz_dir_release = join(tgz_dir, ts)
    create_nested_path(tgz_dir_release)
    for cmd in commands:
        cmd_name = cmd.name
        mschemes = [v for _, v in ARCHIVE.merging_schemes().items()
                    if cmd_name in v]
        for ms in mschemes:
            ms_name = sub('[^0-9a-zA-Z]+', '', ms)
            ms_fp = join(tgz_dir_release, ms_name)
            create_nested_path(ms_fp)

            pfp = join(ms_fp, 'archive.json')
            archives = {k: loads(v)
                        for k, v in ARCHIVE.retrieve_feature_values(
                              archive_merging_scheme=ms).items()
                        if v != ''}
            with open(pfp, 'w') as f:
                dump(archives, f)

            # now let's run the post_processing_cmd
            ppc = cmd.post_processing_cmd

            # concatenate any other parameters into a string
            params = ' '.join(["%s=%s" % (k, v) for k, v in
                              ppc['script_params'].items()])
            # append archives file and output dir parameters
            params = ("%s --fp_archive=%s --output_dir=%s" % (
                params, pfp, ms_fp))

            ppc_cmd = "%s %s %s" % (
                ppc['script_env'], ppc['script_path'], params)
            p_out, p_err, rv = qdb.processing_job._system_call(ppc_cmd)
            p_out = p_out.rstrip()
            if rv != 0:
                raise ValueError('Error %d: %s' % (rv, p_out))
            p_out = loads(p_out)

    # tgz-ing all files
    tgz_name = join(tgz_dir, 'archive-%s-building.tgz' % ts)
    tgz_name_final = join(tgz_dir, 'archive.tgz')
    with topen(tgz_name, "w|gz") as tgz:
        tgz.add(tgz_dir_release, arcname=basename(tgz_dir_release))
    # getting the release md5
    with open(tgz_name, "rb") as f:
        md5sum = md5()
        for c in iter(lambda: f.read(4096), b""):
            md5sum.update(c)
    rename(tgz_name, tgz_name_final)
    vals = [
        ('filepath', tgz_name_final[len(working_dir):], r_client.set),
        ('md5sum', md5sum.hexdigest(), r_client.set),
        ('time', tnow.strftime('%m-%d-%y %H:%M:%S'), r_client.set)]
    for k, v, f in vals:
        redis_key = 'release-archive:%s' % k
        # important to "flush" variables to avoid errors
        r_client.delete(redis_key)
        f(redis_key, v)
