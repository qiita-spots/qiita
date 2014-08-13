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
from tempfile import mkstemp
from os import close
from os.path import join
from itertools import product

from tornado.web import authenticated, asynchronous, HTTPError
from collections import defaultdict, Counter
from pyparsing import ParseException

from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_ware.run import run_analysis
from qiita_db.user import User
from qiita_db.analysis import Analysis
from qiita_db.study import Study
from qiita_db.data import ProcessedData
from qiita_db.metadata_template import SampleTemplate
from qiita_db.job import Job, Command
from qiita_db.util import get_db_files_base_dir, get_table_cols
from qiita_db.search import QiitaStudySearch
from qiita_core.exceptions import IncompetentQiitaDeveloperError


def check_analysis_access(user, analysis_id):
    """Checks whether user has access to an analysis

    Parameters
    ----------
    user : User object
        User to check
    analysis_id : int
        Analysis to check access for

    Raises
    ------
    RuntimeError
        Tried to access analysis that user does not have access to
    """
    if analysis_id not in Analysis.get_public() + user.shared_analyses + \
            user.private_analyses:
        raise RuntimeError("Analysis access denied to %s" % (analysis_id))


class SearchStudiesHandler(BaseHandler):
    def _parse_search_results(self, results, selsamples, meta_headers):
        """remove already selected samples from results and count metadata"""
        counts = {}
        fullcounts = {meta: defaultdict(int) for meta in meta_headers}
        for study, samples in viewitems(results):
            counts[study] = {meta: Counter()
                             for meta in meta_headers}
            topop = []
            for pos, sample in enumerate(samples):
                if study in selsamples and sample[0] in selsamples[study]:
                    topop.append(pos)
                    # still add to full counts, but not study counts
                    for pos, meta in enumerate(meta_headers):
                        fullcounts[meta][sample[pos+1]] += 1
                else:
                    for pos, meta in enumerate(meta_headers):
                        counts[study][meta][sample[pos+1]] += 1
                        fullcounts[meta][sample[pos+1]] += 1
            # remove already selected samples
            topop.sort(reverse=True)
            for pos in topop:
                samples.pop(pos)
        return results, counts, fullcounts

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
        studyinfo = self.get_arguments("availstudies")
        for s in studyinfo:
            study_id, datatype = s.split("#")
            # get the processed data ids for the study
            # get new selected samples for each study and yield with proc id
            for proc_samp_combo in product(self.get_arguments(s),
                                           self.get_arguments(study_id)):
                yield proc_samp_combo

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
        user = self.current_user
        analysis = Analysis(int(self.get_argument("aid")))
        # make sure user has access to the analysis
        userobj = User(user)
        try:
            check_analysis_access(userobj, analysis.id)
        except RuntimeError:
            # trying to access someone else's analysis, so throw 403 error
            raise HTTPError(403)
        # get the dictionaries of selected samples and data types
        selproc_data, selsamples = self._selected_parser(analysis)

        self.render('search_studies.html', user=user, aid=analysis.id,
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
            analysis = Analysis.create(User(user), name, description)
            aid = analysis.id
            # fill example studies by running query for specific studies
            search = QiitaStudySearch()
            def_query = 'study_id = 1 OR study_id = 2 OR study_id = 3'
            results, meta_headers = search(def_query, user)
            results, counts, fullcounts = self._parse_search_results(
                results, selsamples, meta_headers)
        else:
            aid = int(self.get_argument("analysis-id"))
            analysis = Analysis(aid)
            selproc_data, selsamples = self._selected_parser(analysis)

        # run through action requested
        if action == "search":
            search = QiitaStudySearch()
            query = str(self.get_argument("query"))
            try:
                results, meta_headers = search(query, user)
            except ParseException:
                searchmsg = "Malformed search query, please read search help."

            if not results and not searchmsg:
                searchmsg = "No results found."
            else:
                results, counts, fullcounts = self._parse_search_results(
                    results, selsamples, meta_headers)

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

        self.render('search_studies.html', user=user, aid=aid, results=results,
                    meta_headers=meta_headers, selsamples=selsamples,
                    selproc_data=selproc_data, counts=counts,
                    fullcounts=fullcounts, searchmsg=searchmsg, query=query,
                    availmeta=SampleTemplate.metadata_headers() +
                    get_table_cols("study"))


class SelectCommandsHandler(BaseHandler):
    """Select commands to be executed"""
    @authenticated
    def post(self):
        analysis = Analysis(int(self.get_argument('analysis-id')))
        data_types = analysis.data_types
        # sort the elements to have 16S be the first tho show on the tabs
        data_types.sort()

        # FIXME: Pull out from the database, see #111
        commands = Command.get_commands_by_datatype()

        self.render('select_commands.html', user=self.current_user,
                    commands=commands, data_types=data_types, aid=analysis.id)


class AnalysisWaitHandler(BaseHandler):
    @authenticated
    def get(self, analysis_id):
        user = self.current_user
        analysis_id = int(analysis_id)
        check_analysis_access(User(user), analysis_id)

        analysis = Analysis(analysis_id)
        commands = []
        for job in analysis.jobs:
            jobject = Job(job)
            commands.append("%s:%s" % (jobject.datatype, jobject.command[0]))

        self.render("analysis_waiting.html", user=user,
                    aid=analysis_id, aname=analysis.name,
                    commands=commands)

    @authenticated
    @asynchronous
    def post(self, analysis_id):
        user = self.current_user
        analysis_id = int(analysis_id)
        check_analysis_access(User(user), analysis_id)

        command_args = self.get_arguments("commands")
        split = [x.split("#") for x in command_args]
        analysis = Analysis(analysis_id)

        commands = []
        # HARD CODED HACKY THING FOR DEMO, FIX  Issue #164
        fp, mapping_file = mkstemp(suffix="_map_file.txt")
        close(fp)
        SampleTemplate(1).to_file(mapping_file)
        study_fps = {}
        for pd in Study(1).processed_data():
            processed = ProcessedData(pd)
            study_fps[processed.data_type()] = processed.get_filepaths()[0][0]
        for data_type, command in split:
            opts = {
                "--otu_table_fp": study_fps[data_type],
                "--mapping_fp": mapping_file
            }
            if command == "Beta Diversity" and data_type in {'16S', '18S'}:
                opts["--tree_fp"] = join(get_db_files_base_dir(), "reference",
                                         "gg_97_otus_4feb2011.tre")
            elif command == "Beta Diversity":
                opts["--parameter_fp"] = join(get_db_files_base_dir(),
                                              "reference", "params_qiime.txt")
            job = Job.create(data_type, command, analysis)
            job.options = opts
            commands.append("%s: %s" % (data_type, command))
        user = self.current_user
        self.render("analysis_waiting.html", user=user, aid=analysis_id,
                    aname=analysis.name, commands=commands)
        # fire off analysis run here
        # currently synch run so redirect done here. Will remove after demo
        run_analysis(user, analysis)


class AnalysisResultsHandler(BaseHandler):
    @authenticated
    def get(self, analysis_id):
        user = self.current_user
        analysis_id = int(analysis_id)
        check_analysis_access(User(user), analysis_id)

        analysis = Analysis(analysis_id)
        jobres = defaultdict(list)
        for job in analysis.jobs:
            jobject = Job(job)
            jobres[jobject.datatype].append((jobject.command[0],
                                             jobject.results))

        self.render("analysis_results.html", user=self.current_user,
                    jobres=jobres, aname=analysis.name,
                    basefolder=get_db_files_base_dir())


class ShowAnalysesHandler(BaseHandler):
    """Shows the user's analyses"""
    @authenticated
    def get(self):
        user_id = self.current_user
        user = User(user_id)

        analyses = [Analysis(a) for a in
                    user.shared_analyses + user.private_analyses]

        self.render("show_analyses.html", user=user_id, analyses=analyses)
