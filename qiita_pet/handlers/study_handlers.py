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

from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_db.study import Study


class CreateStudyForm(Form):
    study_name = StringField('Study Name', [validators.required()])
    study_title = StringField('Study Title', [validators.required()])
    study_alias = StringField('Study Alias', [validators.required()])
    pubmed_id = StringField('PubMed ID')
    # TODO:This can be filled from the database
    # in oracle, this is in controlled_vocabs (ID 2)
    investigation_type = SelectField('Investigation Type',
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
    environmental_packages = SelectMultipleField('Environmental Packages',
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
        coerce=lambda x: x,
        choices=[('1', 'some guy'),
                 ('2', 'some gal')])
    lab_person = SelectField('Lab Person',
        coerce=lambda x: x,
        choices=[('1', 'some guy'),
                 ('2', 'some gal')])


def check_study_access(user, study_id):
    """Checks whether user has access to a study

    Parameters
    ----------
    user : User object
        User to check
    study_id : int
        Study to check access for

    Raises
    ------
    RuntimeError
        Tried to access analysis that user does not have access to
    """
    if study_id not in Study.get_public() + user.shared_studies + \
            user.private_studies:
        raise HTTPError(403, "Study access denied to %s" % (study_id))

class CreateStudyHandler(BaseHandler):
    @authenticated
    def get(self):
        creation_form = CreateStudyForm()

        # TODO: set the choices attribute on the PI field
        # TODO: set the choices attribute on the lab_person field
        # TODO: set the choices attributes on the investigation_type field
        # TODO: set the choices attributes on the environmental_package field
        self.render('create_study.html', user=self.current_user,
                    creation_form=creation_form)

    def post(self):
        # Get the form data from the request arguments
        form_data = CreateStudyForm(data=self.request.arguments)

        # "process" the form data, and put it in a nicer structure
        form_data_dict = {}
        for element in form_data:
            element.process_formdata(element.data)
            form_data_dict[elelement.label.text] = element.data

        # create the study
        info = {
            'timeseries_type_id': form_data_dict['Includes Event-Based Data'],
            'metadata_complete': True,
            'mixs_compliant': True}

        Study.create(self.current_user, form_data_dict['Study Title'],
                     efo=[1], info=info)

        # TODO: change this redirect
        self.redirect('/')
