r"""Qitta study handlers for the Tornado webserver.
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

from tornado.web import authenticated
from wtforms import (Form, StringField, SelectField, BooleanField,
                     SelectMultipleField, TextAreaField, validators)

from os import listdir
from os.path import exists

from .base_handlers import BaseHandler

from qiita_core.qiita_settings import qiita_config

from qiita_ware.util import metadata_stats_from_sample_and_prep_templates

from qiita_db.metadata_template import SampleTemplate, PrepTemplate
from qiita_db.study import Study, StudyPerson
from qiita_db.user import User
from qiita_db.util import get_study_fp, get_filetypes, convert_to_id
from qiita_db.ontology import Ontology


class CreateStudyForm(Form):
    study_title = StringField('Study Title', [validators.required()])
    study_alias = StringField('Study Alias', [validators.required()])
    pubmed_id = StringField('PubMed ID')
    investigation_type = SelectField(
        'Investigation Type',
        [validators.required()], coerce=lambda x: x)

    # TODO:This can be filled from the database
    # in oracle, this is in controlled_vocabs (ID 1),
    #                       controlled_vocab_values with CVV IDs >= 0
    environmental_packages = SelectMultipleField(
        'Environmental Packages',
        [validators.required()],
        choices=[('air', 'air'),
                 ('host_associated', 'host-associated'),
                 ('human_amniotic_fluid', 'human-amniotic-fluid'),
                 ('human_associated', 'human-associated'),
                 ('human_blood', 'human-blood'),
                 ('human_gut', 'human-gut'),
                 ('human_oral', 'human-oral'),
                 ('human_skin', 'human-skin'),
                 ('human_urine', 'human-urine'),
                 ('human_vaginal', 'human-vaginal'),
                 ('biofilm', 'microbial mat/biofilm'),
                 ('misc_env',
                  'miscellaneous natural or artificial environment'),
                 ('plant_associated', 'plant-associated'),
                 ('sediment', 'sediment'),
                 ('soil', 'soil'),
                 ('wastewater_sludge', 'wastewater/sludge'),
                 ('water', 'water')])
    is_timeseries = BooleanField('Includes Event-Based Data')
    study_abstract = TextAreaField('Study Abstract', [validators.required()])
    study_description = StringField('Study Description',
                                    [validators.required()])
    # The choices for these "people" fields will be filled from the database
    principal_investigator = SelectField('Principal Investigator',
                                         [validators.required()],
                                         coerce=lambda x: x)
    lab_person = SelectField('Lab Person', coerce=lambda x: x)


class PrivateStudiesHandler(BaseHandler):
    @authenticated
    def get(self):
        self.write(self.render_string('waiting.html'))
        self.flush()
        u = User(self.current_user)
        user_studies = [Study(s_id) for s_id in u.private_studies]
        share_dict = {s.id: s.shared_with for s in user_studies}
        shared_studies = [Study(s_id) for s_id in u.shared_studies]
        self.render('private_studies.html', user=self.current_user,
                    user_studies=user_studies, shared_studies=shared_studies,
                    share_dict=share_dict)

    @authenticated
    def post(self):
        pass


class PublicStudiesHandler(BaseHandler):
    @authenticated
    def get(self):
        self.write(self.render_string('waiting.html'))
        self.flush()
        public_studies = [Study(s_id) for s_id in Study.get_public()]
        self.render('public_studies.html', user=self.current_user,
                    public_studies=public_studies)

    @authenticated
    def post(self):
        pass


class StudyDescriptionHandler(BaseHandler):
    @authenticated
    def get(self, study_id):
        fp = get_study_fp(study_id)

        if exists(fp):
            fs = [f for f in listdir(fp)]
        else:
            fs = []

        fts = [' '.join(k.split('_')[1:])
               for k in get_filetypes().keys() if k.startswith('raw_')]

        self.render('study_description.html', user=self.current_user,
                    study_info=Study(study_id).info, study_id=study_id,
                    files=fs, max_upoad_size=qiita_config.max_upoad_size,
                    filetypes=fts)

    @authenticated
    def post(self):
        pass


class CreateStudyHandler(BaseHandler):
    @authenticated
    def get(self):
        creation_form = CreateStudyForm()

        # Get people from the study_person table to populate the PI and
        # lab_person fields
        choices = [('', '')]
        for study_person in StudyPerson.iter():
            person = "{}, {}".format(study_person.name,
                                     study_person.affiliation)
            choices.append((study_person.id, person))

        creation_form.lab_person.choices = choices
        creation_form.principal_investigator.choices = choices

        ena = Ontology(convert_to_id('ENA', 'ongology'))
        ena_terms = ena.terms
        creation_form.investigation_type.choices = [(t, t) for t in ena_terms]

        # TODO: set the choices attributes on the environmental_package field
        self.render('create_study.html', user=self.current_user,
                    creation_form=creation_form)

    @authenticated
    def post(self):
        # Get the form data from the request arguments
        form_data = CreateStudyForm()
        form_data.process(data=self.request.arguments)

        # Get information about new people that need to be added to the DB
        new_people_info = zip(self.get_arguments('new_people_names'),
                              self.get_arguments('new_people_emails'),
                              self.get_arguments('new_people_affiliations'),
                              self.get_arguments('new_people_phones'),
                              self.get_arguments('new_people_addresses'))

        # New people will be indexed with negative numbers, so we reverse
        # the list here
        new_people_info.reverse()

        index = int(form_data.data['principal_investigator'][0])
        if index < 0:
            # If the ID is less than 0, then this is a new person
            PI = StudyPerson.create(
                new_people_info[index][0],
                new_people_info[index][1],
                new_people_info[index][2],
                new_people_info[index][3] or None,
                new_people_info[index][4] or None).id
        else:
            PI = index

        if form_data.data['lab_person'][0]:
            index = int(form_data.data['lab_person'][0])
            if index < 0:
                # If the ID is less than 0, then this is a new person
                lab_person = StudyPerson.create(
                    new_people_info[index][0],
                    new_people_info[index][1],
                    new_people_info[index][2],
                    new_people_info[index][3] or None,
                    new_people_info[index][4] or None).id
            else:
                lab_person = index
        else:
            lab_person = None

        # create the study
        # TODO: Get the portal type from... somewhere
        # TODO: Time series types; right now it's True/False; from emily?
        # TODO: MIXS compliant?  Always true, right?
        info = {
            'timeseries_type_id': 1,
            'portal_type_id': 1,
            'lab_person_id': lab_person,
            'principal_investigator_id': PI,
            'metadata_complete': False,
            'mixs_compliant': True,
            'study_description': form_data.data['study_description'][0],
            'study_alias': form_data.data['study_alias'][0],
            'study_abstract': form_data.data['study_abstract'][0]}

        # TODO: Fix this EFO once ontology stuff from emily is added
        theStudy = Study.create(User(self.current_user),
                                form_data.data['study_title'][0],
                                efo=[1], info=info)

        if form_data.data['pubmed_id'][0]:
            theStudy.add_pmid(form_data.data['pubmed_id'][0])

        # TODO: change this redirect to something more sensible
        self.redirect('/')


class MetadataSummaryHandler(BaseHandler):
    @authenticated
    def get(self, arguments):
        st = SampleTemplate(int(self.get_argument('sample_template')))
        pt = PrepTemplate(int(self.get_argument('prep_template')))

        stats = metadata_stats_from_sample_and_prep_templates(st, pt)

        self.render('metadata_summary.html', user=self.current_user,
                    study_title=Study(st.id).title, stats=stats)
