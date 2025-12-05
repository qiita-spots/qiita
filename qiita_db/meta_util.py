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
from base64 import b64encode
from collections import Counter, defaultdict
from datetime import datetime
from hashlib import md5
from io import BytesIO
from json import dump, dumps, loads
from os import stat
from os.path import basename, join, relpath
from re import sub
from shutil import move
from tarfile import TarInfo
from tarfile import open as topen
from time import localtime, strftime
from urllib.parse import quote

import matplotlib as mpl
import matplotlib.pyplot as plt

import qiita_db as qdb
from qiita_core.configuration_manager import ConfigurationManager
from qiita_core.qiita_settings import qiita_config, r_client
from qiita_db.util import (
    create_nested_path,
    resource_allocation_plot,
    retrieve_resource_data,
)

# global constant list used in resource_allocation_page
COLUMNS = [
    "sName",
    "sVersion",
    "cID",
    "cName",
    "processing_job_id",
    "parameters",
    "samples",
    "columns",
    "input_size",
    "extra_info",
    "MaxRSSRaw",
    "ElapsedRaw",
    "Start",
    "node_name",
    "node_model",
]
RAW_DATA_ARTIFACT_TYPE = {"SFF", "FASTQ", "FASTA", "FASTA_Sanger", "per_sample_FASTQ"}


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

            if artifact.visibility == "public":
                # TODO: https://github.com/biocore/qiita/issues/1724
                if artifact.artifact_type in RAW_DATA_ARTIFACT_TYPE:
                    study = artifact.study
                    has_access = study.has_access(user, no_public=True)
                    if not study.public_raw_download and not has_access:
                        return False
                return True
            else:
                study = artifact.study
                if study:
                    # let's take the visibility via the Study
                    return artifact.study.has_access(user)
                else:
                    analysis = artifact.analysis
                    return analysis in (user.private_analyses | user.shared_analyses)
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
            pt = qdb.metadata_template.prep_template.PrepTemplate(pid[0])
            a = pt.artifact
            # however, the prep info file could not have any artifacts attached
            # , in that case we will use the study access level
            if a is None:
                return qdb.study.Study(pt.study_id).has_access(user)
            else:
                if a.visibility == "public" or a.study.has_access(user):
                    return True
                else:
                    for c in a.descendants.nodes():
                        if c.visibility == "public" or c.study.has_access(user):
                            return True
            return False
        # analyses
        elif anid:
            # [0] cause we should only have 1
            aid = anid[0]
            analysis = qdb.analysis.Analysis(aid)
            return analysis.is_public | (
                analysis in (user.private_analyses | user.shared_analyses)
            )
        return False


def update_redis_stats():
    """Generate the system stats and save them in redis

    Returns
    -------
    list of str
        artifact filepaths that are not present in the file system
    """
    STUDY = qdb.study.Study

    number_studies = {"public": 0, "private": 0, "sandbox": 0}
    number_of_samples = {"public": 0, "private": 0, "sandbox": 0}
    num_studies_ebi = 0
    num_samples_ebi = 0
    number_samples_ebi_prep = 0
    stats = []
    missing_files = []
    per_data_type_stats = Counter()
    for study in STUDY.iter():
        st = study.sample_template
        if st is None:
            continue

        # counting samples submitted to EBI-ENA
        len_samples_ebi = sum(
            [esa is not None for esa in st.ebi_sample_accessions.values()]
        )
        if len_samples_ebi != 0:
            num_studies_ebi += 1
            num_samples_ebi += len_samples_ebi

        samples_status = defaultdict(set)
        for pt in study.prep_templates():
            pt_samples = list(pt.keys())
            pt_status = pt.status
            if pt_status == "public":
                per_data_type_stats[pt.data_type()] += len(pt_samples)
            samples_status[pt_status].update(pt_samples)
            # counting experiments (samples in preps) submitted to EBI-ENA
            number_samples_ebi_prep += sum(
                [esa is not None for esa in pt.ebi_experiment_accessions.values()]
            )

        # counting studies
        if "public" in samples_status:
            number_studies["public"] += 1
        elif "private" in samples_status:
            number_studies["private"] += 1
        else:
            # note that this is a catch all for other status; at time of
            # writing there is status: awaiting_approval
            number_studies["sandbox"] += 1

        # counting samples; note that some of these lines could be merged with
        # the block above but I decided to split it in 2 for clarity
        if "public" in samples_status:
            number_of_samples["public"] += len(samples_status["public"])
        if "private" in samples_status:
            number_of_samples["private"] += len(samples_status["private"])
        if "sandbox" in samples_status:
            number_of_samples["sandbox"] += len(samples_status["sandbox"])

        # processing filepaths
        for artifact in study.artifacts():
            for adata in artifact.filepaths:
                try:
                    s = stat(adata["fp"])
                except OSError:
                    missing_files.append(adata["fp"])
                else:
                    stats.append(
                        (
                            adata["fp_type"],
                            s.st_size,
                            strftime("%Y-%m", localtime(s.st_mtime)),
                        )
                    )

    num_users = qdb.util.get_count("qiita.qiita_user")
    num_processing_jobs = qdb.util.get_count("qiita.processing_job")

    lat_longs = dumps(get_lat_longs())

    summary = {}
    all_dates = []
    # these are some filetypes that are too small to plot alone so we'll merge
    # in other
    group_other = {
        "html_summary",
        "tgz",
        "directory",
        "raw_fasta",
        "log",
        "raw_sff",
        "raw_qual",
        "qza",
        "html_summary_dir",
        "qza",
        "plain_text",
        "raw_barcodes",
    }
    for ft, size, ym in stats:
        if ft in group_other:
            ft = "other"
        if ft not in summary:
            summary[ft] = {}
        if ym not in summary[ft]:
            summary[ft][ym] = 0
            all_dates.append(ym)
        summary[ft][ym] += size
    all_dates = sorted(set(all_dates))

    # sorting summaries
    ordered_summary = {}
    for dt in summary:
        new_list = []
        current_value = 0
        for ad in all_dates:
            if ad in summary[dt]:
                current_value += summary[dt][ad]
            new_list.append(current_value)
        ordered_summary[dt] = new_list

    plot_order = sorted(
        [(k, ordered_summary[k][-1]) for k in ordered_summary], key=lambda x: x[1]
    )

    # helper function to generate y axis, modified from:
    # http://stackoverflow.com/a/1094933
    def sizeof_fmt(value, position):
        number = None
        for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
            if abs(value) < 1024.0:
                number = "%3.1f%s" % (value, unit)
                break
            value /= 1024.0
        if number is None:
            number = "%.1f%s" % (value, "Yi")
        return number

    all_dates_axis = range(len(all_dates))
    plt.locator_params(axis="y", nbins=10)
    plt.figure(figsize=(20, 10))
    for k, v in plot_order:
        plt.plot(all_dates_axis, ordered_summary[k], linewidth=2, label=k)

    plt.xticks(all_dates_axis, all_dates)
    plt.legend()
    plt.grid()
    ax = plt.gca()
    ax.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(sizeof_fmt))
    plt.xticks(rotation=90)
    plt.xlabel("Date")
    plt.ylabel("Storage space per data type")

    plot = BytesIO()
    plt.savefig(plot, format="png")
    plot.seek(0)
    img = "data:image/png;base64," + quote(b64encode(plot.getbuffer()))

    time = datetime.now().strftime("%m-%d-%y %H:%M:%S")

    portal = qiita_config.portal
    # making sure per_data_type_stats has some data so hmset doesn't fail
    if per_data_type_stats == {}:
        per_data_type_stats["No data"] = 0

    vals = [
        ("number_studies", number_studies, r_client.hmset),
        ("number_of_samples", number_of_samples, r_client.hmset),
        ("per_data_type_stats", dict(per_data_type_stats), r_client.hmset),
        ("num_users", num_users, r_client.set),
        ("lat_longs", (lat_longs), r_client.set),
        ("num_studies_ebi", num_studies_ebi, r_client.set),
        ("num_samples_ebi", num_samples_ebi, r_client.set),
        ("number_samples_ebi_prep", number_samples_ebi_prep, r_client.set),
        ("img", img, r_client.set),
        ("time", time, r_client.set),
        ("num_processing_jobs", num_processing_jobs, r_client.set),
    ]
    for k, v, f in vals:
        redis_key = "%s:stats:%s" % (portal, k)
        # important to "flush" variables to avoid errors
        r_client.delete(redis_key)
        f(redis_key, v)

    # preparing vals to insert into DB
    vals = dumps(dict([x[:-1] for x in vals]))
    sql = """INSERT INTO qiita.stats_daily (stats, stats_timestamp)
             VALUES (%s, NOW())"""
    qdb.sql_connection.perform_as_transaction(sql, [vals])

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
        studies = qdb.study.Study.get_by_status("public")

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
            sql = " UNION ".join(sql)
            qdb.sql_connection.TRN.add(sql)

            # note that we are returning set to remove duplicates
            results = qdb.sql_connection.TRN.execute_fetchindex()

        return results


def generate_biom_and_metadata_release(study_status="public"):
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
    time = datetime.now().strftime("%m-%d-%y %H:%M:%S")

    data = []
    for s in studies:
        # [0] latest is first, [1] only getting the filepath
        sample_fp = relpath(s.sample_template.get_filepaths()[0][1], bdir)

        for a in s.artifacts(artifact_type="BIOM"):
            if a.processing_parameters is None or a.visibility != study_status:
                continue

            merging_schemes, parent_softwares = a.merging_scheme
            software = a.processing_parameters.command.software
            software = "%s v%s" % (software.name, software.version)

            for x in a.filepaths:
                if x["fp_type"] != "biom" or "only-16s" in x["fp"]:
                    continue
                fp = relpath(x["fp"], bdir)
                for pt in a.prep_templates:
                    categories = pt.categories
                    platform = ""
                    target_gene = ""
                    if "platform" in categories:
                        platform = ", ".join(set(pt.get_category("platform").values()))
                    if "target_gene" in categories:
                        target_gene = ", ".join(
                            set(pt.get_category("target_gene").values())
                        )
                    for _, prep_fp in pt.get_filepaths():
                        if "qiime" not in prep_fp:
                            break
                    prep_fp = relpath(prep_fp, bdir)
                    # format: (biom_fp, sample_fp, prep_fp, qiita_artifact_id,
                    #          platform, target gene, merging schemes,
                    #          artifact software/version,
                    #          parent sofware/version)
                    data.append(
                        (
                            fp,
                            sample_fp,
                            prep_fp,
                            a.id,
                            platform,
                            target_gene,
                            merging_schemes,
                            software,
                            parent_softwares,
                        )
                    )

    # writing text and tgz file
    ts = datetime.now().strftime("%m%d%y-%H%M%S")
    tgz_dir = join(working_dir, "releases")
    create_nested_path(tgz_dir)
    tgz_name = join(tgz_dir, "%s-%s-building.tgz" % (portal, study_status))
    tgz_name_final = join(tgz_dir, "%s-%s.tgz" % (portal, study_status))
    txt_lines = [
        "biom fp\tsample fp\tprep fp\tqiita artifact id\tplatform\t"
        "target gene\tmerging scheme\tartifact software\tparent software"
    ]
    with topen(tgz_name, "w|gz") as tgz:
        for biom_fp, sample_fp, prep_fp, aid, pform, tg, ms, asv, psv in data:
            txt_lines.append(
                "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s"
                % (biom_fp, sample_fp, prep_fp, aid, pform, tg, ms, asv, psv)
            )
            tgz.add(join(bdir, biom_fp), arcname=biom_fp, recursive=False)
            tgz.add(join(bdir, sample_fp), arcname=sample_fp, recursive=False)
            tgz.add(join(bdir, prep_fp), arcname=prep_fp, recursive=False)
        info = TarInfo(name="%s-%s-%s.txt" % (portal, study_status, ts))
        txt_hd = BytesIO()
        txt_hd.write(bytes("\n".join(txt_lines), "ascii"))
        txt_hd.seek(0)
        info.size = len(txt_hd.read())
        txt_hd.seek(0)
        tgz.addfile(tarinfo=info, fileobj=txt_hd)

    with open(tgz_name, "rb") as f:
        md5sum = md5()
        for c in iter(lambda: f.read(4096), b""):
            md5sum.update(c)

    move(tgz_name, tgz_name_final)

    vals = [
        ("filepath", tgz_name_final[len(working_dir) :], r_client.set),
        ("md5sum", md5sum.hexdigest(), r_client.set),
        ("time", time, r_client.set),
    ]
    for k, v, f in vals:
        redis_key = "%s:release:%s:%s" % (portal, study_status, k)
        # important to "flush" variables to avoid errors
        r_client.delete(redis_key)
        f(redis_key, v)


def generate_plugin_releases():
    """Generate releases for plugins"""
    ARCHIVE = qdb.archive.Archive
    qiita_config = ConfigurationManager()
    working_dir = qiita_config.working_dir

    commands = [
        c
        for s in qdb.software.Software.iter(active=True)
        for c in s.commands
        if c.post_processing_cmd is not None
    ]

    tnow = datetime.now()
    ts = tnow.strftime("%m%d%y-%H%M%S")
    tgz_dir = join(working_dir, "releases", "archive")
    create_nested_path(tgz_dir)
    tgz_dir_release = join(tgz_dir, ts)
    create_nested_path(tgz_dir_release)
    for cmd in commands:
        cmd_name = cmd.name
        mschemes = [v for _, v in ARCHIVE.merging_schemes().items() if cmd_name in v]
        for ms in mschemes:
            ms_name = sub("[^0-9a-zA-Z]+", "", ms)
            ms_fp = join(tgz_dir_release, ms_name)
            create_nested_path(ms_fp)

            pfp = join(ms_fp, "archive.json")
            archives = {
                k: loads(v)
                for k, v in ARCHIVE.retrieve_feature_values(
                    archive_merging_scheme=ms
                ).items()
                if v != ""
            }
            with open(pfp, "w") as f:
                dump(archives, f)

            # now let's run the post_processing_cmd
            ppc = cmd.post_processing_cmd

            # concatenate any other parameters into a string
            params = " ".join(
                ["%s=%s" % (k, v) for k, v in ppc["script_params"].items()]
            )
            # append archives file and output dir parameters
            params = "%s --fp_archive=%s --output_dir=%s" % (params, pfp, ms_fp)

            ppc_cmd = "%s %s %s" % (ppc["script_env"], ppc["script_path"], params)
            p_out, p_err, rv = qdb.processing_job._system_call(ppc_cmd)
            p_out = p_out.rstrip()
            if rv != 0:
                raise ValueError("Error %d: %s" % (rv, p_out))
            p_out = loads(p_out)

    # tgz-ing all files
    tgz_name = join(tgz_dir, "archive-%s-building.tgz" % ts)
    tgz_name_final = join(tgz_dir, "archive.tgz")
    with topen(tgz_name, "w|gz") as tgz:
        tgz.add(tgz_dir_release, arcname=basename(tgz_dir_release))
    # getting the release md5
    with open(tgz_name, "rb") as f:
        md5sum = md5()
        for c in iter(lambda: f.read(4096), b""):
            md5sum.update(c)
    move(tgz_name, tgz_name_final)
    vals = [
        ("filepath", tgz_name_final[len(working_dir) :], r_client.set),
        ("md5sum", md5sum.hexdigest(), r_client.set),
        ("time", tnow.strftime("%m-%d-%y %H:%M:%S"), r_client.set),
    ]
    for k, v, f in vals:
        redis_key = "release-archive:%s" % k
        # important to "flush" variables to avoid errors
        r_client.delete(redis_key)
        f(redis_key, v)


def get_software_commands(active):
    software_list = [s for s in qdb.software.Software.iter(active=active)]
    software_commands = defaultdict(lambda: defaultdict(list))

    for software in software_list:
        sname = software.name
        sversion = software.version
        commands = software.commands

        for command in commands:
            software_commands[sname][sversion].append(command.name)
        software_commands[sname] = dict(software_commands[sname])

    return dict(software_commands)


def update_resource_allocation_redis(active=True):
    """Updates redis with plots and information about current software.

    Parameters
    ----------
    active: boolean, optional
        Defaults to True. Should only be False when testing.

    """
    time = datetime.now().strftime("%m-%d-%y")
    scommands = get_software_commands(active)
    redis_key = "resources:commands"
    r_client.set(redis_key, str(scommands))

    for sname, versions in scommands.items():
        for version, commands in versions.items():
            for cname in commands:
                col_name = "samples * columns"
                df = retrieve_resource_data(cname, sname, version, COLUMNS)
                if len(df) == 0:
                    continue

                fig, axs = resource_allocation_plot(df, col_name)
                titles = [0, 0]
                images = [0, 0]

                # Splitting 1 image plot into 2 separate for better layout.
                for i, ax in enumerate(axs):
                    titles[i] = ax.get_title()
                    ax.set_title("")
                    # new_fig, new_ax – copy with either only memory plot or
                    # only time
                    new_fig = plt.figure()
                    new_ax = new_fig.add_subplot(111)
                    line = ax.lines[0]
                    new_ax.plot(
                        line.get_xdata(), line.get_ydata(), linewidth=1, color="orange"
                    )
                    handles, labels = ax.get_legend_handles_labels()
                    for handle, label, scatter_data in zip(
                        handles, labels, ax.collections
                    ):
                        color = handle.get_facecolor()
                        new_ax.scatter(
                            scatter_data.get_offsets()[:, 0],
                            scatter_data.get_offsets()[:, 1],
                            s=scatter_data.get_sizes(),
                            label=label,
                            color=color,
                        )

                    new_ax.set_xscale("log")
                    new_ax.set_yscale("log")
                    new_ax.set_xlabel(ax.get_xlabel())
                    new_ax.set_ylabel(ax.get_ylabel())
                    new_ax.legend(loc="upper left")

                    new_fig.tight_layout()
                    plot = BytesIO()
                    new_fig.savefig(plot, format="png")
                    plot.seek(0)
                    img = "data:image/png;base64," + quote(
                        b64encode(plot.getvalue()).decode("ascii")
                    )
                    images[i] = img
                    plt.close(new_fig)
                plt.close(fig)

                # SID, CID, col_name
                values = [
                    ("img_mem", images[0], r_client.set),
                    ("img_time", images[1], r_client.set),
                    ("time", time, r_client.set),
                    ("title_mem", titles[0], r_client.set),
                    ("title_time", titles[1], r_client.set),
                ]

                for k, v, f in values:
                    redis_key = "resources$#%s$#%s$#%s$#%s:%s" % (
                        cname,
                        sname,
                        version,
                        col_name,
                        k,
                    )
                    r_client.delete(redis_key)
                    f(redis_key, v)
