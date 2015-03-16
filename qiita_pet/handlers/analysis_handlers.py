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
from collections import defaultdict, Counter
from os.path import join, sep, commonprefix

from tornado.web import authenticated, HTTPError, StaticFileHandler
from pyparsing import ParseException
from moi import ctx_default, r_client
from moi.job import submit
from moi.group import get_id_from_user, create_info

from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.exceptions import QiitaPetAuthorizationError
from qiita_ware.dispatchable import run_analysis
from qiita_db.analysis import Analysis
from qiita_db.data import ProcessedData
from qiita_db.metadata_template import SampleTemplate
from qiita_db.job import Job, Command
from qiita_db.util import (get_db_files_base_dir,
                           check_access_to_analysis_result,
                           get_table_cols,
                           filepath_ids_to_rel_paths)
from qiita_ware.search import search, count_metadata
from qiita_db.exceptions import (
    QiitaDBIncompatibleDatatypeError, QiitaDBUnknownIDError)

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


class SearchStudiesHandler(BaseHandler):
    def _selected_parser(self, analysis):
        """builds dictionaries of selected samples from analysis object"""
        selsamples = {}
        selproc_data = defaultdict(list)
        for proc_data_id, samps in viewitems(analysis.samples):
            study = ProcessedData(proc_data_id).study
            selproc_data[study].append(proc_data_id)
            selsamples[study] = set(samps)
        return selproc_data, selsamples

    def _parse_form_select(self):
        """parses selected checkboxes and yields the selected ones in
        format accepted by Analysis.add_samples()
        """
        # get the selected studies and datatypes for studies
        for s in self.get_arguments("availstudies"):
            study_id, proc_data_id = s.split("#", 1)
            proc_data_id = int(proc_data_id)
            # get new selected samples for each study and yield with proc id
            for sample in self.get_arguments(study_id):
                yield (proc_data_id, sample)

    def _parse_form_deselect(self):
        """parses selected checkboxes and returns the selected ones in
        format accepted by Analysis.remove_samples()
        """
        studyinfo = self.get_arguments("selstudies")
        proc_data = []
        samples = []
        for sid in studyinfo:
            # get the processed data ids and add it to the study
            proc_data.extend(self.get_arguments("dt%s" % sid))
            # get new selected samples for each study and add to study
            samples.extend(self.get_arguments("sel%s" % sid))
        return proc_data, samples

    @authenticated
    def get(self):
        userobj = self.current_user
        analysis = Analysis(int(self.get_argument("aid")))
        # make sure user has access to the analysis
        check_analysis_access(userobj, analysis)

        # get the dictionaries of selected samples and data types
        selproc_data, selsamples = self._selected_parser(analysis)

        self.render('search_studies.html', aid=analysis.id,
                    selsamples=selsamples, selproc_data=selproc_data,
                    counts={}, fullcounts={}, searchmsg="", query="",
                    results={}, availmeta=SampleTemplate.metadata_headers() +
                    get_table_cols("study"))

    @authenticated
    def post(self):
        user = self.current_user
        action = self.get_argument("action")
        # set required template variables
        results = {}
        meta_headers = []
        counts = {}
        fullcounts = {}
        query = ""
        searchmsg = ""
        selsamples = {}
        selproc_data = {}
        # get analysis and selected samples if exists, or create if necessary
        if action == "create":
            name = self.get_argument('name')
            description = self.get_argument('description')
            analysis = Analysis.create(user, name, description)
            analysis_id = analysis.id
            # set to second step since this page is second step in workflow
            analysis.step = SELECT_SAMPLES
        else:
            analysis_id = int(self.get_argument("analysis-id"))
            analysis = Analysis(analysis_id)
            check_analysis_access(user, analysis)
            selproc_data, selsamples = self._selected_parser(analysis)

        # run through action requested
        if action == "search":
            query = str(self.get_argument("query"))
            try:
                results, meta_headers = search(query, user)
            except ParseException:
                searchmsg = "Malformed search query, please read search help."
            except QiitaDBIncompatibleDatatypeError as e:
                searchmsg = ''.join(e)

            if not results and not searchmsg:
                searchmsg = "No results found."
            else:
                fullcounts, counts = count_metadata(results, meta_headers)

        elif action == "select":
            analysis.add_samples(self._parse_form_select())

            # rebuild the selected from database to reflect changes
            selproc_data, selsamples = self._selected_parser(analysis)

        elif action == "deselect":
            proc_data, samples = self._parse_form_deselect()
            if proc_data:
                analysis.remove_samples(proc_data=proc_data)
            if samples:
                analysis.remove_samples(samples=samples)
            if not proc_data and not samples:
                searchmsg = "Must select samples to remove from analysis!"

            # rebuild the selected from database to reflect changes
            selproc_data, selsamples = self._selected_parser(analysis)

        self.render('search_studies.html', user=user, aid=analysis_id,
                    results=results, meta_headers=meta_headers,
                    selsamples=selsamples, selproc_data=selproc_data,
                    counts=counts, fullcounts=fullcounts, searchmsg=searchmsg,
                    query=query, availmeta=SampleTemplate.metadata_headers() +
                    get_table_cols("study"))


class SelectCommandsHandler(BaseHandler):
    """Select commands to be executed"""
    @authenticated
    def get(self):
        analysis_id = int(self.get_argument('aid'))
        analysis = Analysis(analysis_id)
        check_analysis_access(self.current_user, analysis)

        data_types = analysis.data_types
        commands = Command.get_commands_by_datatype()

        self.render('select_commands.html',
                    commands=commands, data_types=data_types, aid=analysis.id)

    @authenticated
    def post(self):
        analysis = Analysis(int(self.get_argument('analysis-id')))
        # set to third step since this page is third step in workflow
        analysis.step = SELECT_COMMANDS
        data_types = analysis.data_types
        commands = Command.get_commands_by_datatype()
        self.render('select_commands.html',
                    commands=commands, data_types=data_types, aid=analysis.id)


class AnalysisWaitHandler(BaseHandler):
    @authenticated
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
    def post(self, analysis_id):
        analysis_id = int(analysis_id)
        rarefaction_depth = self.get_argument('rarefaction-depth')
        # convert to integer if rarefaction level given
        if rarefaction_depth:
            rarefaction_depth = int(rarefaction_depth)
        else:
            rarefaction_depth = None
        analysis = Analysis(analysis_id)
        check_analysis_access(self.current_user, analysis)

        command_args = self.get_arguments("commands")
        split = [x.split("#") for x in command_args]

        moi_user_id = get_id_from_user(self.current_user.id)
        moi_group = create_info(analysis_id, 'group', url='/analysis/',
                                parent=moi_user_id, store=True)
        moi_name = 'Creating %s' % analysis.name
        moi_result_url = '/analysis/results/%d' % analysis_id

        submit(ctx_default, moi_group['id'], moi_name,
               moi_result_url, run_analysis, analysis_id, split,
               rarefaction_depth=rarefaction_depth)

        r_client.hset('analyis-map', analysis_id, moi_group['id'])

        self.render("analysis_waiting.html",
                    group_id=moi_group['id'], aname=analysis.name)


class AnalysisResultsHandler(BaseHandler):
    @authenticated
    def get(self, analysis_id):
        analysis_id = int(analysis_id.split("/")[0])
        analysis = Analysis(analysis_id)
        check_analysis_access(self.current_user, analysis)

        jobres = defaultdict(list)
        for job in analysis.jobs:
            jobject = Job(job)
            jobres[jobject.datatype].append((jobject.command[0],
                                             jobject.results))

        dropped = {}
        dropped_samples = analysis.dropped_samples
        if dropped_samples:
            for proc_data_id, samples in viewitems(dropped_samples):
                proc_data = ProcessedData(proc_data_id)
                key = "Data type %s, Study: %s" % (proc_data.data_type(),
                                                   proc_data.study)
                dropped[key] = samples

        self.render("analysis_results.html",
                    jobres=jobres, aname=analysis.name, dropped=dropped,
                    basefolder=get_db_files_base_dir())


class ShowAnalysesHandler(BaseHandler):
    """Shows the user's analyses"""
    @authenticated
    def get(self):
        user = self.current_user

        analyses = [Analysis(a) for a in
                    user.shared_analyses + user.private_analyses]

        self.render("show_analyses.html", analyses=analyses)


class ResultsHandler(StaticFileHandler, BaseHandler):
    def validate_absolute_path(self, root, absolute_path):
        """Overrides StaticFileHandler's method to include authentication
        """
        # Get the filename (or the base directory) of the result
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
