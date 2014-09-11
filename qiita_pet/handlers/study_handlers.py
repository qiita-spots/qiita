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

from tornado.web import authenticated, asynchronous, HTTPError
from wtforms import (Form, StringField, SelectField, BooleanField,
                     SelectMultipleField, TextAreaField, validators)

from .base_handlers import BaseHandler

from qiita_db.study import Study, StudyPerson
from qiita_db.user import User


class CreateStudyForm(Form):
    study_title = StringField('Study Title', [validators.required()])
    study_alias = StringField('Study Alias', [validators.required()])
    pubmed_id = StringField('PubMed ID')
    # TODO:This can be filled from the database
    # in oracle, this is in controlled_vocabs (ID 2)
    investigation_type = SelectField(
        'Investigation Type',
        [validators.required()], coerce=lambda x: x,
        choices=[('eukaryote', 'eukaryote'),
                 ('bacteria_archaea_genome',
                  'bacteria/archaea (complete genome)'),
                 ('plasmid_genome', 'plasmid (complete genome)'),
                 ('virus_genome', 'virus (complete genome)'),
                 ('organelle_genome', 'organelle (complete genome)'),
                 ('metagenome', 'metagenome'),
                 ('mimarks_survey', 'mimarks-survey (e.g. 16S rRNA)')])
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

        # TODO: set the choices attributes on the investigation_type field
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
        # TODO: Metadata complete: always true, right?
        info = {
            'timeseries_type_id': 1,
            'portal_type_id': 1,
            'lab_person_id': lab_person,
            'principal_investigator_id': PI,
            'metadata_complete': True,
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
