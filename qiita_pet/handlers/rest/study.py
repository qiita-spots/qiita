# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from tornado.escape import json_decode

from qiita_db.handlers.oauth2 import authenticate_oauth
from qiita_db.study import StudyPerson, Study
from qiita_db.user import User
from .rest_handler import RESTHandler


class StudyHandler(RESTHandler):
    # /api/v1/study/<int>

    @authenticate_oauth
    def get(self, study_id):
        study = self.study_boilerplate(study_id)
        if study is None:
            return

        info = study.info
        pi = info['principal_investigator']
        lp = info['lab_person']
        self.write({'title': study.title,
                    'contacts': {'principal_investigator': [
                                     pi.name,
                                     pi.affiliation,
                                     pi.email],
                                 'lab_person': [
                                     lp.name,
                                     lp.affiliation,
                                     lp.email]},
                    'study_abstract': info['study_abstract'],
                    'study_description': info['study_description'],
                    'study_alias': info['study_alias'],
                    'efo': study.efo})
        self.finish()


class StudyCreatorHandler(RESTHandler):
    @authenticate_oauth
    def post(self, *args, **kwargs):
        try:
            payload = json_decode(self.request.body)
        except ValueError:
            self.set_status(400)
            self.write({'message': 'Could not parse body'})
            self.finish()
            return

        required = {'title', 'study_abstract', 'study_description',
                    'study_alias', 'owner', 'efo', 'contacts'}

        if not required.issubset(payload):
            self.set_status(400)
            self.write({'message': 'Not all required arguments provided'})
            self.finish()
            return

        title = payload['title']
        study_abstract = payload['study_abstract']
        study_desc = payload['study_description']
        study_alias = payload['study_alias']

        owner = payload['owner']
        if not User.exists(owner):
            self.set_status(403)
            self.write({'message': 'Unknown user'})
            self.finish()
            return
        else:
            owner = User(owner)

        efo = payload['efo']
        contacts = payload['contacts']

        if Study.exists(title):
            self.set_status(409)
            self.write({'message': 'Study title already exists'})
            self.finish()
            return

        pi_name = contacts['principal_investigator'][0]
        pi_aff = contacts['principal_investigator'][1]
        if not StudyPerson.exists(pi_name, pi_aff):
            self.set_status(403)
            self.write({'message': 'Unknown principal investigator'})
            self.finish()
            return
        else:
            pi = StudyPerson.from_name_and_affiliation(pi_name, pi_aff)

        lp_name = contacts['lab_person'][0]
        lp_aff = contacts['lab_person'][1]
        if not StudyPerson.exists(lp_name, lp_aff):
            self.set_status(403)
            self.write({'message': 'Unknown lab person'})
            self.finish()
            return
        else:
            lp = StudyPerson.from_name_and_affiliation(lp_name, lp_aff)

        info = {'lab_person_id': lp,
                'principal_investigator_id': pi,
                'study_abstract': study_abstract,
                'study_description': study_desc,
                'study_alias': study_alias,

                # TODO: we believe it is accurate that mixs is false and
                # metadata completion is false as these cannot be known
                # at study creation here no matter what.
                # we do not know what should be done with the timeseries.
                'mixs_compliant': False,
                'metadata_complete': False,
                'timeseries_type_id': 1}
        study = Study.create(owner, title, efo, info)

        self.set_status(201)
        self.write({'id': study.id})
        self.finish()


class StudyStatusHandler(RESTHandler):
    pass
