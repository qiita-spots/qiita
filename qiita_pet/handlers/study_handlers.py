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
                     SelectMultipleField, TextAreaField)

from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_db.study import Study

class CreateStudyForm(Form):
    study_name = StringField('Study Name')
    study_title = StringField('Study Title')
    study_alias = StringField('Study Alias')
    pubmed_id = StringField('PubMed ID')
    # This can be filled from the database
    # in oracle, this is in controlled_vocabs (ID 2)
    investigation_type = SelectField('Investigation Type',
        choices=[('eukaryote', 'eukaryote'),
                 ('bacteria_archaea_genome',
                  'bacteria/archaea (complete genome)'),
                 ('plasmid_genome', 'plasmid (complete genome)'),
                 ('virus_genome', 'virus (complete genome)'),
                 ('organelle_genome', 'organelle (complete genome)'),
                 ('metagenome', 'metagenome'),
                 ('mimarks_survey', 'mimarks-survey (e.g. 16S rRNA)')])
    # This can be filled from the database
    # in oracle, this is in controlled_vocabs (ID 1),
    #                       controlled_vocab_values with CVV IDs >= 0
    environmental_packages = SelectMultipleField('Environmental Packages',
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
    study_abstract = TextAreaField('Study Abstract')
    study_description = StringField('Study Description')
    # The choices for these "people" fields will be filled from the database
    principal_investigator = SelectField('Principal Investigator',
        choices=[('1', 'some guy'),
                 ('2', 'some gal')])
    lab_person = SelectField('Lab Person',
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

        # doing this instead of using WTForms "required" validator so that
        # the form can be checked client-side
        creation_form.study_name.required = True
        creation_form.study_title.required = True
        creation_form.study_alias.required = True
        creation_form.pubmed_id.required = False
        creation_form.investigation_type.required = True
        creation_form.environmental_packages.required = True
        creation_form.is_timeseries.required = False
        creation_form.study_abstract.required = True
        creation_form.study_description.required = True
        creation_form.principal_investigator.required = False
        creation_form.lab_person.required = False

        # TODO: set the choices attribute on the PI field
        # TODO: set the choices attribute on the lab_person field
        # TODO: set the choices attributes on the investigation_type field
        # TODO: set the choices attributes on the environmental_package field
        self.render('create_study.html', user=self.current_user,
                    creation_form=creation_form)

    def post(self):
        form_data = CreateStudyForm(self.request.body_arguments)
        # TODO: change this render
        self.render('index.html', user=self.current_user)
