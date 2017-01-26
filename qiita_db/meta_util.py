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

    get_accessible_filepath_ids
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
from os import stat
from time import strftime, localtime
import matplotlib.pyplot as plt
import matplotlib as mpl
from base64 import b64encode
from urllib import quote
from StringIO import StringIO
from future.utils import viewitems
from datetime import datetime

from qiita_core.qiita_settings import qiita_config
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


def get_accessible_filepath_ids(user):
    """Gets all filepaths that this user should have access to

    This gets all raw, preprocessed, and processed filepaths, for studies
    that the user has access to, as well as all the mapping files and biom
    tables associated with the analyses that the user has access to.

    Parameters
    ----------
    user : User object
        The user we are interested in


    Returns
    -------
    set
        A set of filepath ids

    Notes
    -----
    Admins have access to all files, so all filepath ids are returned for
    admins
    """
    with qdb.sql_connection.TRN:
        if user.level == "admin":
            # admins have access all files
            qdb.sql_connection.TRN.add(
                "SELECT filepath_id FROM qiita.filepath")
            return set(qdb.sql_connection.TRN.execute_fetchflatten())

        # First, the studies
        # There are private and shared studies
        studies = user.user_studies | user.shared_studies

        filepath_ids = set()
        for study in studies:
            # Add the sample template files
            if study.sample_template:
                filepath_ids.update(
                    {fid for fid, _ in study.sample_template.get_filepaths()})

            # Add the prep template filepaths
            for pt in study.prep_templates():
                filepath_ids.update({fid for fid, _ in pt.get_filepaths()})

            # Add the artifact filepaths
            for artifact in study.artifacts():
                filepath_ids.update({fid for fid, _, _ in artifact.filepaths})

        # Next, the public artifacts
        for artifact in qdb.artifact.Artifact.iter_public():
            # Add the filepaths of the artifact
            filepath_ids.update({fid for fid, _, _ in artifact.filepaths})

            # Then add the filepaths of the prep templates
            for pt in artifact.prep_templates:
                filepath_ids.update({fid for fid, _ in pt.get_filepaths()})

            # Then add the filepaths of the sample template
            filepath_ids.update(
                {fid
                 for fid, _ in artifact.study.sample_template.get_filepaths()})

        # Next, analyses
        # Same as before, there are public, private, and shared
        analyses = qdb.analysis.Analysis.get_by_status('public') | \
            user.private_analyses | user.shared_analyses

        for analysis in analyses:
            filepath_ids.update(analysis.all_associated_filepath_ids)

        return filepath_ids


def update_redis_stats():
    """Generate the system stats and save them in redis

    Returns
    -------
    list of str
        artifact filepaths that are not present in the file system
    """
    STUDY = qdb.study.Study
    studies = {'public': STUDY.get_by_status('private'),
               'private': STUDY.get_by_status('public'),
               'sanbox': STUDY.get_by_status('sandbox')}
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

    num_studies_ebi = len(ebi_samples_prep)
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
                    except:
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
    keys = [
        'number_studies', 'number_of_samples', 'num_users', 'lat_longs',
        'num_studies_ebi', 'num_samples_ebi', 'number_samples_ebi_prep',
        'img', 'time']

    for k in keys:
        redis_key = '%s:stats:%s' % (portal, k)
        # important to "flush" variable to avoid errors
        r_client.delete(redis_key)

        # storing dicts
        if k == 'number_studies':
            r_client.hmset(redis_key, number_studies)
        elif k == 'number_of_samples':
            r_client.hmset(redis_key, number_of_samples)
        # single values
        elif k == 'num_users':
            r_client.set(redis_key, num_users)
        elif k == 'num_studies_ebi':
            r_client.set(redis_key, num_studies_ebi)
        elif k == 'num_samples_ebi':
            r_client.set(redis_key, num_samples_ebi)
        elif k == 'number_samples_ebi_prep':
            r_client.set(redis_key, number_samples_ebi_prep)
        elif k == 'img':
            r_client.set(redis_key, img)
        elif k == 'time':
            r_client.set(redis_key, time)
        # storing tuples
        elif k == 'lat_longs':
            r_client.set(redis_key, lat_longs)

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
