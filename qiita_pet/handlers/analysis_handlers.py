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
from tempfile import mkstemp
from os import close

from tornado.web import authenticated, asynchronous
from collections import defaultdict

from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_ware.run import run_analysis
from qiita_db.user import User
from qiita_db.analysis import Analysis
from qiita_db.study import Study
from qiita_db.data import ProcessedData
from qiita_db.metadata_template import SampleTemplate
from qiita_db.job import Job
from qiita_db.util import get_db_files_base_dir
# login code modified from https://gist.github.com/guillaumevincent/4771570


class CreateAnalysisHandler(BaseHandler):
    """Analysis creation"""
    @authenticated
    def get(self):
        self.render('create_analysis.html', user=self.get_current_user())


class SelectStudiesHandler(BaseHandler):
    """Study selection"""
    @authenticated
    def post(self):
        name = self.get_argument('name')
        description = self.get_argument('description')
        user = self.get_current_user()
        # create list of studies
        study_ids = {s.id for s in Study.get_public()}
        userobj = User(user)
        [study_ids.add(x) for x in userobj.private_studies]
        [study_ids.add(x) for x in userobj.shared_studies]

        studies = [Study(i) for i in study_ids]
        analysis = Analysis.create(User(user), name, description)

        self.render('select_studies.html', user=user, aid=analysis.id,
                    studies=studies)


class SelectCommandsHandler(BaseHandler):
    """Select commands to be executed"""
    @authenticated
    def post(self):
        analysis_id = self.get_argument('analysis-id')
        study_args = self.get_arguments('studies')
        split = [x.split("#") for x in study_args]

        # build dictionary of studies and datatypes selected
        # as well a set of unique datatypes selected
        study_dts = defaultdict(list)
        data_types = set()
        for study_id, data_type in split:
            study_dts[study_id].append(data_type)
            data_types.add(data_type)

        # sort the elements to have 16S be the first tho show on the tabs
        data_types = sorted(list(data_types))

        # FIXME: Pull out from the database, see #111
        commands = {'16S': ['Alpha Rarefaction', 'Beta Diversity',
                            'Summarize Taxa'],
                    '18S': ['Alpha Rarefaction', 'Beta Diversity',
                            'Summarize Taxa'],
                    'Metabolomic': ['Summarize Taxa']}

        self.render('select_commands.html', user=self.get_current_user(),
                    commands=commands, data_types=data_types, aid=analysis_id)

        analysis = Analysis(analysis_id)

        for study_id in study_dts:
            study = Study(study_id)
            processed_data = {ProcessedData(pid).data_type: pid for pid in
                              study.processed_data}

            sample_ids = SampleTemplate(study.id).keys()
            for data_type in study_dts[study.id]:
                samples = [(processed_data[data_type], sid) for sid in
                           sample_ids]
                analysis.add_samples(samples)


class AnalysisWaitHandler(BaseHandler):
    @authenticated
    def get(self, analysis_id):
        analysis = Analysis(analysis_id)
        commands = []
        for job in analysis.jobs:
            jobject = Job(job)
            commands.append("%s:%s" % (jobject.datatype, jobject.command[0]))

        self.render("analysis_waiting.html", user=self.get_current_user(),
                    aid=analysis_id, aname=analysis.name,
                    commands=commands)

    @authenticated
    @asynchronous
    def post(self, analysis_id):
        command_args = self.get_arguments("commands")
        split = [x.split("#") for x in command_args]
        analysis = Analysis(analysis_id)

        commands = []
        # HARD CODED HACKY THING FOR DEMO, FIX  Issue #164
        fp, mapping_file = mkstemp(suffix="_map_file.txt")
        close(fp)
        SampleTemplate(1).to_file(mapping_file)
        study_fps = {}
        for pd in Study(1).processed_data:
            processed = ProcessedData(pd)
            study_fps[processed.data_type] = processed.get_filepaths()[0][0]
        for data_type, command in split:

            opts = {
                "--otu_table_fp": study_fps[data_type],
                "--mapping_fp": mapping_file
            }

            Job.create(data_type, command, opts, analysis)
            commands.append("%s: %s" % (data_type, command))
        user = self.get_current_user()
        self.render("analysis_waiting.html", user=user,
                    aid=analysis_id, aname=analysis.name,
                    commands=commands)
        # fire off analysis run here
        # currently synch run so redirect done here. Will remove after demo
        run_analysis(user, analysis)


class AnalysisResultsHandler(BaseHandler):
    @authenticated
    def get(self, aid):
        analysis = Analysis(aid)
        jobres = defaultdict(list)
        for job in analysis.jobs:
            jobject = Job(job)
            jobres[jobject.datatype].append((jobject.command[0],
                                             jobject.results))

        self.render("analysis_results.html", user=self.get_current_user(),
                    jobres=jobres, aname=analysis.name,
                    basefolder=get_db_files_base_dir())


class ShowAnalysesHandler(BaseHandler):
    """Shows the user's analyses"""
    def get(self):
        user_id = self.get_current_user()
        user = User(user_id)

        analyses = [Analysis(a) for a in
                    user.shared_analyses + user.private_analyses]

        self.render("show_analyses.html", user=user_id, analyses=analyses)
