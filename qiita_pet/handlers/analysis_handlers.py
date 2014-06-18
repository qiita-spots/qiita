from tornado.web import authenticated
from collections import defaultdict

from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_db.user import User
from qiita_db.analysis import Analysis
from qiita_db.study import Study
from qiita_db.data import ProcessedData
from qiita_db.metadata_template import SampleTemplate
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

        # make sure the data types are unique
        data_types = list(data_types)
        data_types.sort()

        # FIXME: Pull out from the database!!
        commands = {'16S' : ['Alpha Diversity', 'Beta Diversity',
                             'Summarize Taxa'],
                    '18S' : ['Alpha Diversity', 'Beta Diversity',
                             'Summarize Taxa'],
                    'Metabolomic' : ['Summarize Taxa']}

        self.render('select_commands.html', user=self.get_current_user(),
                    commands=commands, data_types=data_types)

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

