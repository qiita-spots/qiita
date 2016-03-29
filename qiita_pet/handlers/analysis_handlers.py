r"""
Qitta analysis handlers for the Tornado webserver.

"""
# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division
from future.utils import viewitems
from collections import defaultdict
from os.path import join, sep, commonprefix, basename, dirname
from json import dumps
from functools import partial

from tornado.web import authenticated, HTTPError, StaticFileHandler
from moi import ctx_default, r_client
from moi.job import submit
from moi.group import get_id_from_user, create_info

from qiita_pet.util import is_localhost
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.util import download_link_or_path
from qiita_pet.exceptions import QiitaPetAuthorizationError
from qiita_ware.dispatchable import run_analysis
from qiita_db.analysis import Analysis
from qiita_db.artifact import Artifact
from qiita_db.job import Command
from qiita_db.util import (get_db_files_base_dir,
                           check_access_to_analysis_result,
                           filepath_ids_to_rel_paths, get_filepath_id)
from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_db.logger import LogEntry
from qiita_db.reference import Reference
from qiita_core.util import execute_as_transaction

SELECT_SAMPLES = 2
SELECT_COMMANDS = 3


def check_analysis_access(user, analysis):
    """Checks whether user has access to an analysis

    Parameters
    ----------
    user : User object
        User to check
    analysis : Analysis object
        Analysis to check access for

    Raises
    ------
    RuntimeError
        Tried to access analysis that user does not have access to
    """
    if not analysis.has_access(user):
        raise HTTPError(403, "Analysis access denied to %s" % (analysis.id))


class SelectCommandsHandler(BaseHandler):
    """Select commands to be executed"""
    @authenticated
    @execute_as_transaction
    def get(self):
        analysis_id = int(self.get_argument('aid'))
        analysis = Analysis(analysis_id)
        check_analysis_access(self.current_user, analysis)

        data_types = analysis.data_types
        commands = Command.get_commands_by_datatype()

        self.render('select_commands.html',
                    commands=commands, data_types=data_types, aid=analysis.id)

    @authenticated
    @execute_as_transaction
    def post(self):
        name = self.get_argument('name')
        desc = self.get_argument('description')
        analysis = Analysis.create(self.current_user, name, desc,
                                   from_default=True)
        # set to third step since this page is third step in workflow
        analysis.step = SELECT_COMMANDS
        data_types = analysis.data_types
        commands = Command.get_commands_by_datatype()
        self.render('select_commands.html',
                    commands=commands, data_types=data_types, aid=analysis.id)


class AnalysisWaitHandler(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self, analysis_id):
        analysis_id = int(analysis_id)
        try:
            analysis = Analysis(analysis_id)
        except QiitaDBUnknownIDError:
            raise HTTPError(404, "Analysis %d does not exist" % analysis_id)
        else:
            check_analysis_access(self.current_user, analysis)

        group_id = r_client.hget('analyis-map', analysis_id)
        self.render("analysis_waiting.html",
                    group_id=group_id, aname=analysis.name)

    @authenticated
    @execute_as_transaction
    def post(self, analysis_id):
        analysis_id = int(analysis_id)
        rarefaction_depth = self.get_argument('rarefaction-depth')
        mdsi = self.get_argument('merge-duplicated-sample-ids', default=False)
        if mdsi == 'on':
            mdsi = True

        # convert to integer if rarefaction level given
        if rarefaction_depth:
            rarefaction_depth = int(rarefaction_depth)
        else:
            rarefaction_depth = None
        analysis = Analysis(analysis_id)
        check_analysis_access(self.current_user, analysis)

        command_args = self.get_arguments("commands")
        cmd_split = [x.split("#") for x in command_args]

        moi_user_id = get_id_from_user(self.current_user.id)
        moi_group = create_info(analysis_id, 'group', url='/analysis/',
                                parent=moi_user_id, store=True)
        moi_name = ("Creating %s... When finished, please click the 'Success' "
                    "link to the right" % analysis.name)
        moi_result_url = '/analysis/results/%d' % analysis_id

        submit(ctx_default, moi_group['id'], moi_name,
               moi_result_url, run_analysis, analysis_id, cmd_split,
               rarefaction_depth=rarefaction_depth,
               merge_duplicated_sample_ids=mdsi)

        r_client.hset('analyis-map', analysis_id, moi_group['id'])

        self.render("analysis_waiting.html",
                    group_id=moi_group['id'], aname=analysis.name)


class AnalysisResultsHandler(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self, analysis_id):
        analysis_id = int(analysis_id.split("/")[0])
        analysis = Analysis(analysis_id)
        check_analysis_access(self.current_user, analysis)

        jobres = defaultdict(list)
        for jobject in analysis.jobs:
            results = []
            for res in jobject.results:
                name = basename(res)
                if name.startswith('index'):
                    name = basename(dirname(res)).replace('_', ' ')
                results.append((res, name))
            jobres[jobject.datatype].append((jobject.command[0],
                                             results))

        dropped_samples = analysis.dropped_samples
        dropped = defaultdict(list)
        for proc_data_id, samples in viewitems(dropped_samples):
            if not samples:
                continue
            proc_data = Artifact(proc_data_id)
            data_type = proc_data.data_type
            dropped[data_type].append((proc_data.study.title, len(samples),
                                       ', '.join(samples)))

        self.render("analysis_results.html", analysis_id=analysis_id,
                    jobres=jobres, aname=analysis.name, dropped=dropped,
                    basefolder=get_db_files_base_dir())

    @authenticated
    @execute_as_transaction
    def post(self, analysis_id):
        analysis_id = int(analysis_id.split("/")[0])
        analysis_id_sent = int(self.get_argument('analysis_id'))
        action = self.get_argument('action')

        if analysis_id != analysis_id_sent or action != 'delete_analysis':
            raise QiitaPetAuthorizationError(
                self.current_user.id,
                'analysis/results/%d-delete' % analysis_id)

        analysis = Analysis(analysis_id)
        analysis_name = analysis.name
        check_analysis_access(self.current_user, analysis)

        try:
            Analysis.delete(analysis_id)
            msg = ("Analysis <b><i>%s</i></b> has been deleted." % (
                analysis_name))
            level = "success"
        except Exception as e:
            e = str(e)
            msg = ("Couldn't remove <b><i>%s</i></b> analysis: %s" % (
                analysis_name, e))
            level = "danger"
            LogEntry.create('Runtime', "Couldn't remove analysis ID %d: %s" %
                            (analysis_id, e))

        self.redirect(u"/analysis/show/?level=%s&message=%s" % (level, msg))


class ShowAnalysesHandler(BaseHandler):
    """Shows the user's analyses"""
    @authenticated
    @execute_as_transaction
    def get(self):
        message = self.get_argument('message', '')
        level = self.get_argument('level', '')
        user = self.current_user

        analyses = user.shared_analyses | user.private_analyses

        is_local_request = is_localhost(self.request.headers['host'])
        gfi = partial(get_filepath_id, 'analysis')
        dlop = partial(download_link_or_path, is_local_request)
        mappings = {}
        bioms = {}
        tgzs = {}
        for analysis in analyses:
            _id = analysis.id
            # getting mapping file
            mapping = analysis.mapping_file
            if mapping is not None:
                mappings[_id] = dlop(mapping, gfi(mapping), 'mapping file')
            else:
                mappings[_id] = ''
            # getting biom tables
            links = [dlop(f, gfi(f), l)
                     for l, f in viewitems(analysis.biom_tables)]
            bioms[_id] = '\n'.join(links)
            # getting tgz file
            tgz = analysis.tgz
            if tgz is not None:
                tgzs[_id] = dlop(tgz, gfi(tgz), 'tgz file')
            else:
                tgzs[_id] = ''

        self.render("show_analyses.html", analyses=analyses, message=message,
                    level=level, is_local_request=is_local_request,
                    mappings=mappings, bioms=bioms, tgz=tgzs)

    @authenticated
    @execute_as_transaction
    def post(self):
        analysis_id = int(self.get_argument('analysis_id'))
        analysis = Analysis(analysis_id)
        analysis_name = analysis.name

        check_analysis_access(self.current_user, analysis)

        try:
            Analysis.delete(analysis_id)
            msg = ("Analysis <b><i>%s</i></b> has been deleted." % (
                analysis_name))
            level = "success"
        except Exception as e:
            e = str(e)
            msg = ("Couldn't remove <b><i>%s</i></b> analysis: %s" % (
                analysis_name, e))
            level = "danger"
            LogEntry.create('Runtime', "Couldn't remove analysis ID %d: %s" %
                            (analysis_id, e))

        self.redirect(u"/analysis/show/?level=%s&message=%s" % (level, msg))


class ResultsHandler(StaticFileHandler, BaseHandler):
    @execute_as_transaction
    def validate_absolute_path(self, root, absolute_path):
        """Overrides StaticFileHandler's method to include authentication
        """
        # Get the filename (or the base directory) of the result
        if root[-1] != '/':
            root = "%s/" % root
        len_prefix = len(commonprefix([root, absolute_path]))
        base_requested_fp = absolute_path[len_prefix:].split(sep, 1)[0]

        current_user = self.current_user

        # If the user is an admin, then allow access
        if current_user.level == 'admin':
            return super(ResultsHandler, self).validate_absolute_path(
                root, absolute_path)

        # otherwise, we have to check if they have access to the requested
        # resource
        user_id = current_user.id
        accessible_filepaths = check_access_to_analysis_result(
            user_id, base_requested_fp)

        # Turn these filepath IDs into absolute paths
        db_files_base_dir = get_db_files_base_dir()
        relpaths = filepath_ids_to_rel_paths(accessible_filepaths)

        accessible_filepaths = {join(db_files_base_dir, relpath)
                                for relpath in relpaths.values()}

        # check if the requested resource is a file (or is in a directory) that
        # the user has access to
        if join(root, base_requested_fp) in accessible_filepaths:
            return super(ResultsHandler, self).validate_absolute_path(
                root, absolute_path)
        else:
            raise QiitaPetAuthorizationError(user_id, absolute_path)


class SelectedSamplesHandler(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self):
        # Format sel_data to get study IDs for the processed data
        sel_data = defaultdict(dict)
        proc_data_info = {}
        sel_samps = self.current_user.default_analysis.samples
        for pid, samps in viewitems(sel_samps):
            proc_data = Artifact(pid)
            sel_data[proc_data.study][pid] = samps
            # Also get processed data info
            parameters = proc_data.processing_parameters
            reference = Reference(parameters.values['reference'])

            proc_data_info[pid] = {
                'processed_date': str(proc_data.timestamp),
                'algorithm': parameters.command.name,
                'reference_name': reference.name,
                'reference_version': reference.version,
                'sequence_filepath': reference.sequence_fp,
                'taxonomy_filepath': reference.taxonomy_fp,
                'tree_filepath': reference.tree_fp,
                'data_type': proc_data.data_type}

        self.render("analysis_selected.html", sel_data=sel_data,
                    proc_info=proc_data_info)


class AnalysisSummaryAJAX(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self):
        info = self.current_user.default_analysis.summary_data()
        self.write(dumps(info))
