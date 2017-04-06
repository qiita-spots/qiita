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

from moi import r_client
from os import stat, makedirs, rename
from os.path import join, relpath, exists
from time import strftime, localtime
import matplotlib.pyplot as plt
import matplotlib as mpl
from base64 import b64encode
from urllib import quote
from StringIO import StringIO
from future.utils import viewitems
from datetime import datetime
from tarfile import open as topen, TarInfo
from hashlib import md5

from qiita_core.qiita_settings import qiita_config
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
            (SELECT array_agg(job_id)
             FROM qiita.job_results_filepath
             WHERE filepath_id = {0}) AS job_results,
            (SELECT array_agg(analysis_id)
             FROM qiita.analysis_filepath
             WHERE filepath_id = {0}) AS analysis""".format(filepath_id)
        TRN.add(sql)

        arid, sid, pid, jid, anid = TRN.execute_fetchflatten()

        # artifacts
        if arid:
            # [0] cause we should only have 1
            artifact = qdb.artifact.Artifact(arid[0])
            if artifact.visibility == 'public':
                return True
            else:
                # let's take the visibility via the Study
                return artifact.study.has_access(user)
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
        elif anid or jid:
            if jid:
                # [0] cause we should only have 1
                sql = """SELECT analysis_id FROM qiita.analysis_job
                         WHERE job_id = {0}""".format(jid[0])
                TRN.add(sql)
                aid = TRN.execute_fetchlast()
            else:
                aid = anid[0]
            # [0] cause we should only have 1
            analysis = qdb.analysis.Analysis(aid)
            if analysis.status == 'public':
                return True
            else:
                return analysis in (
                    user.private_analyses | user.shared_analyses)


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

    lat_longs = get_lat_longs()

    num_studies_ebi = len([k for k, v in viewitems(ebi_samples_prep)
                           if v >= 1])
    number_samples_ebi_prep = sum([v for _, v in viewitems(ebi_samples_prep)])

    # generating file size stats
    stats = []
    missing_files = []
    for k, sts in viewitems(studies):
        for s in sts:
            for a in s.artifacts():
                for _, fp, dt in a.filepaths:
                    try:
                        s = stat(fp)
                        stats.append((dt, s.st_size, strftime('%Y-%m',
                                      localtime(s.st_ctime))))
                    except OSError:
                        missing_files.append(fp)

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
    plt.xlabel('Date')
    plt.ylabel('Storage space per data type')

    plot = StringIO()
    plt.savefig(plot, format='png')
    plot.seek(0)
    img = 'data:image/png;base64,' + quote(b64encode(plot.buf))

    time = datetime.now().strftime('%m-%d-%y %H:%M:%S')

    portal = qiita_config.portal
    vals = [
        ('number_studies', number_studies, r_client.hmset),
        ('number_of_samples', number_of_samples, r_client.hmset),
        ('num_users', num_users, r_client.set),
        ('lat_longs', lat_longs, r_client.set),
        ('num_studies_ebi', num_studies_ebi, r_client.set),
        ('num_samples_ebi', num_samples_ebi, r_client.set),
        ('number_samples_ebi_prep', number_samples_ebi_prep, r_client.set),
        ('img', img, r_client.set),
        ('time', time, r_client.set)]
    for k, v, f in vals:
        redis_key = '%s:stats:%s' % (portal, k)
        # important to "flush" variables to avoid errors
        r_client.delete(redis_key)
        f(redis_key, v)

    return missing_files


def get_lat_longs():
    """Retrieve the latitude and longitude of all the samples in the DB

    Returns
    -------
    list of [float, float]
        The latitude and longitude for each sample in the database
    """
    portal_table_ids = [
        s.id for s in qdb.portal.Portal(qiita_config.portal).get_studies()]

    with qdb.sql_connection.TRN:
        # getting all tables in the portal
        sql = """SELECT DISTINCT table_name
                 FROM information_schema.columns
                 WHERE table_name SIMILAR TO 'sample_[0-9]+'
                    AND table_schema = 'qiita'
                    AND column_name IN ('latitude', 'longitude')
                    AND SPLIT_PART(table_name, '_', 2)::int IN %s;"""
        qdb.sql_connection.TRN.add(sql, [tuple(portal_table_ids)])

        sql = [('SELECT CAST(latitude AS FLOAT), '
                '       CAST(longitude AS FLOAT) '
                'FROM qiita.%s '
                'WHERE isnumeric(latitude) AND isnumeric(longitude) '
                "AND latitude <> 'NaN' "
                "AND longitude <> 'NaN' " % s)
               for s in qdb.sql_connection.TRN.execute_fetchflatten()]
        sql = ' UNION '.join(sql)
        qdb.sql_connection.TRN.add(sql)

        return qdb.sql_connection.TRN.execute_fetchindex()


def generate_biom_and_metadata_release(study_status='public'):
    """Generate a list of biom/meatadata filepaths and a tgz of those files

    Parameters
    ----------
    study_status : str, optional
        The study status to search for. Note that this should always be set
        to 'public' but having this exposed as helps with testing. The other
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
            if a.processing_parameters is None:
                continue

            cmd_name = a.processing_parameters.command.name

            # this loop is necessary as in theory an artifact can be
            # generated from multiple prep info files
            human_cmd = []
            for p in a.parents:
                pp = p.processing_parameters
                pp_cmd_name = pp.command.name
                if pp_cmd_name == 'Trimming':
                    human_cmd.append('%s @ %s' % (
                        cmd_name, str(pp.values['length'])))
                else:
                    human_cmd.append('%s, %s' % (cmd_name, pp_cmd_name))
            human_cmd = ', '.join(human_cmd)

            for _, fp, fp_type in a.filepaths:
                if fp_type != 'biom' or 'only-16s' in fp:
                    continue
                fp = relpath(fp, bdir)
                # format: (biom_fp, sample_fp, prep_fp, qiita_artifact_id,
                #          human readable name)
                for pt in a.prep_templates:
                    for _, prep_fp in pt.get_filepaths():
                        if 'qiime' not in prep_fp:
                            break
                    prep_fp = relpath(prep_fp, bdir)
                    data.append((fp, sample_fp, prep_fp, a.id, human_cmd))

    # writing text and tgz file
    ts = datetime.now().strftime('%m%d%y-%H%M%S')
    tgz_dir = join(working_dir, 'releases')
    if not exists(tgz_dir):
        makedirs(tgz_dir)
    tgz_name = join(tgz_dir, '%s-%s-building.tgz' % (portal, study_status))
    tgz_name_final = join(tgz_dir, '%s-%s.tgz' % (portal, study_status))
    txt_hd = StringIO()
    with topen(tgz_name, "w|gz") as tgz:
        # writing header for txt
        txt_hd.write(
            "biom_fp\tsample_fp\tprep_fp\tqiita_artifact_id\tcommand\n")
        for biom_fp, sample_fp, prep_fp, artifact_id, human_cmd in data:
            txt_hd.write("%s\t%s\t%s\t%s\t%s\n" % (
                biom_fp, sample_fp, prep_fp, artifact_id, human_cmd))
            tgz.add(join(bdir, biom_fp), arcname=biom_fp, recursive=False)
            tgz.add(join(bdir, sample_fp), arcname=sample_fp, recursive=False)
            tgz.add(join(bdir, prep_fp), arcname=prep_fp, recursive=False)

        txt_hd.seek(0)
        info = TarInfo(name='%s-%s-%s.txt' % (portal, study_status, ts))
        info.size = len(txt_hd.buf)
        tgz.addfile(tarinfo=info, fileobj=txt_hd)

    with open(tgz_name, "rb") as f:
        md5sum = md5()
        for c in iter(lambda: f.read(4096), b""):
            md5sum.update(c)

    rename(tgz_name, tgz_name_final)

    vals = [
        ('filepath', tgz_name_final[len(working_dir) + 1:], r_client.set),
        ('md5sum', md5sum.hexdigest(), r_client.set),
        ('time', time, r_client.set)]
    for k, v, f in vals:
        redis_key = '%s:release:%s:%s' % (portal, study_status, k)
        # important to "flush" variables to avoid errors
        r_client.delete(redis_key)
        f(redis_key, v)
