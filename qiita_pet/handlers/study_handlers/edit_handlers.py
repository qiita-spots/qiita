# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

from tornado.web import authenticated, HTTPError
from wtforms import (Form, StringField, SelectField, SelectMultipleField,
                     TextAreaField, validators)

from qiita_core.qiita_settings import qiita_config
from qiita_db.study import Study, StudyPerson
from qiita_db.util import get_timeseries_types, get_environmental_packages
from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.util import check_access
from qiita_core.util import execute_as_transaction


class StudyEditorForm(Form):
    r"""Reduced WTForm for editing the study information

    Allows editing any study information that will not require a metadata
    changes

    Attributes
    ----------
    study_title
    study_alias
    pubmed_id
    study_abstract
    study_description
    principal_investigator
    lab_person

    Parameters
    ----------
    study : Study, optional
        The study to be modified. If not provided, the Form will not be
        prepopulated and can be used for study creation

    See Also
    --------
    StudyEditorExtendedForm
    wtforms.Form
    """
    study_title = StringField('Study Title', [validators.Required()])
    study_alias = StringField('Study Alias', [validators.Required()])
    publication_doi = StringField(
        'DOI', description=('Just values, no links, comma separated values'))
    publication_pid = StringField(
        'PUBMED ID', description=('Just values, no links, comma '
                                  'separated values'))
    study_abstract = TextAreaField('Study Abstract', [validators.Required()])
    study_description = StringField('Study Description',
                                    [validators.Required()])
    # The choices for these "people" fields will be filled from the database
    principal_investigator = SelectField('Principal Investigator',
                                         [validators.Required()],
                                         coerce=lambda x: x)

    lab_person = SelectField('Lab Person', coerce=lambda x: x)

    @execute_as_transaction
    def __init__(self, study=None, **kwargs):
        super(StudyEditorForm, self).__init__(**kwargs)

        # Get people from the study_person table to populate the PI and
        # lab_person fields
        choices = [(sp.id, u"%s, %s"
                    % (sp.name.decode('utf-8'),
                       sp.affiliation.decode('utf-8')))
                   for sp in StudyPerson.iter()]
        choices.insert(0, ('', ''))

        self.lab_person.choices = choices
        self.principal_investigator.choices = choices

        # If a study is provided, put its values in the form
        if study:
            study_info = study.info

            self.study_title.data = study.title.decode('utf-8')
            self.study_alias.data = study_info['study_alias'].decode('utf-8')
            dois = []
            pids = []
            for p, is_doi in study.publications:
                if is_doi:
                    dois.append(p)
                else:
                    pids.append(p)
            self.publication_doi.data = ",".join(dois).decode('utf-8')
            self.publication_pid.data = ",".join(pids).decode('utf-8')
            self.study_abstract.data = study_info[
                'study_abstract'].decode('utf-8')
            self.study_description.data = study_info[
                'study_description'].decode('utf-8')
            self.principal_investigator.data = study_info[
                'principal_investigator'].id
            self.lab_person.data = (study_info['lab_person'].id
                                    if study_info['lab_person'] else None)


class StudyEditorExtendedForm(StudyEditorForm):
    r"""Extended WTForm for editing the study information

    Allows editing all the study information

    Attributes
    ----------
    environmental_packages
    timeseries

    Parameters
    ----------
    study : Study, optional
        The study to be modified. If not provided, the Form will not be
        prepopulated and can be used for study creation

    See Also
    --------
    StudyEditorForm
    wtforms.Form
    """
    environmental_packages = SelectMultipleField('Environmental Packages',
                                                 [validators.Required()])
    timeseries = SelectField('Event-Based Data', coerce=lambda x: x)

    @execute_as_transaction
    def __init__(self, study=None, **kwargs):
        super(StudyEditorExtendedForm, self).__init__(study=study, **kwargs)

        # Populate the choices for the environmental packages
        # Get environmental packages returns a list of tuples of the form
        # (env package name, table name), but we need a list of
        # (table name, env package name) so the actual environmental package
        # name is displayed on the GUI
        self.environmental_packages.choices = [
            (name, name) for name, table in get_environmental_packages()]

        # Get the available timeseries types to populate the timeseries field
        choices = [[time_id, '%s, %s' % (int_t, time_t)]
                   for time_id, time_t, int_t in get_timeseries_types()]
        # Change None, None to 'No timeseries', just for GUI purposes
        choices[0][1] = 'No timeseries'
        self.timeseries.choices = choices

        # If a study is provided, put its values in the form
        if study:
            study_info = study.info

            self.environmental_packages.data = study.environmental_packages
            self.timeseries.data = study_info['timeseries_type_id']


class StudyEditHandler(BaseHandler):
    @execute_as_transaction
    def _check_study_exists_and_user_access(self, study_id):
        try:
            study = Study(int(study_id))
        except QiitaDBUnknownIDError:
            # Study not in database so fail nicely
            raise HTTPError(404, "Study %s does not exist" % study_id)

        # We need to check if the user has access to the study
        check_access(self.current_user, study)
        return study

    def _get_study_person_id(self, index, new_people_info):
        """Returns the id of the study person, creating if needed

        If index < 0, means that we need to create a new study person, and its
        information is stored in new_people_info[index]

        Parameters
        ----------
        index : int
            The index of the study person
        new_people_info : list of tuples
            The information of the new study persons added through the
            interface

        Returns
        -------
        int
            the study person id
        """
        # If the ID is less than 0, then this is a new person
        if index < 0:
            return StudyPerson.create(*new_people_info[index]).id

        return index

    @authenticated
    @execute_as_transaction
    def get(self, study_id=None):
        study = None
        form_factory = StudyEditorExtendedForm
        if study_id:
            # Check study and user access
            study = self._check_study_exists_and_user_access(study_id)
            # If the study is not sandboxed, we use the short
            # version of the form
            if study.status != 'sandbox':
                form_factory = StudyEditorForm

        creation_form = form_factory(study=study)

        self.render('edit_study.html',
                    creation_form=creation_form, study=study)

    @authenticated
    @execute_as_transaction
    def post(self, study=None):
        the_study = None
        form_factory = StudyEditorExtendedForm
        if study:
            # Check study and user access
            the_study = self._check_study_exists_and_user_access(study)
            # If the study is not sandbox, we use the short version
            if the_study.status != 'sandbox':
                form_factory = StudyEditorForm

        # Get the form data from the request arguments
        form_data = form_factory()
        form_data.process(data=self.request.arguments)

        # Get information about new people that need to be added to the DB
        # Phones and addresses are optional, so make sure that we have None
        # values instead of empty strings
        new_people_info = [
            (name, email, affiliation, phone or None, address or None)
            for name, email, affiliation, phone, address in
            zip(self.get_arguments('new_people_names'),
                self.get_arguments('new_people_emails'),
                self.get_arguments('new_people_affiliations'),
                self.get_arguments('new_people_phones'),
                self.get_arguments('new_people_addresses'))]

        # New people will be indexed with negative numbers, so we reverse
        # the list here
        new_people_info.reverse()

        index = int(form_data.data['principal_investigator'][0])
        PI = self._get_study_person_id(index, new_people_info)

        if form_data.data['lab_person'][0]:
            index = int(form_data.data['lab_person'][0])
            lab_person = self._get_study_person_id(index, new_people_info)
        else:
            lab_person = None

        # TODO: MIXS compliant?  Always true, right?
        info = {
            'lab_person_id': lab_person,
            'principal_investigator_id': PI,
            'metadata_complete': False,
            'mixs_compliant': True,
            'study_description': form_data.data['study_description'][0],
            'study_alias': form_data.data['study_alias'][0],
            'study_abstract': form_data.data['study_abstract'][0]}

        if 'timeseries' in form_data.data and form_data.data['timeseries']:
            info['timeseries_type_id'] = form_data.data['timeseries'][0]

        study_title = form_data.data['study_title'][0]

        if the_study:
            # We are under editing, so just update the values
            the_study.title = study_title
            the_study.info = info

            msg = ('Study <a href="%s/study/description/%d">%s</a> '
                   'successfully updated' %
                   (qiita_config.portal_dir, the_study.id,
                    form_data.data['study_title'][0]))
        else:
            # create the study
            # TODO: Fix this EFO once ontology stuff from emily is added
            the_study = Study.create(self.current_user, study_title,
                                     efo=[1], info=info)

            msg = ('Study <a href="%s/study/description/%d">%s</a> '
                   'successfully created' %
                   (qiita_config.portal_dir, the_study.id,
                    form_data.data['study_title'][0]))

        # Add the environmental packages, this attribute can only be edited
        # if the study is not public, otherwise this cannot be changed
        if isinstance(form_data, StudyEditorExtendedForm):
            the_study.environmental_packages = form_data.data[
                'environmental_packages']

        pubs = []
        dois = form_data.data['publication_doi']
        if dois and dois[0]:
            # The user can provide a comma-seprated list
            dois = dois[0].split(',')
            # Make sure that we strip the spaces from the pubmed ids
            pubs.extend([(doi.strip(), True) for doi in dois])
        pids = form_data.data['publication_pid']
        if pids and pids[0]:
            # The user can provide a comma-seprated list
            pids = pids[0].split(',')
            # Make sure that we strip the spaces from the pubmed ids
            pubs.extend([(pid.strip(), False) for pid in pids])
        the_study.publications = pubs

        self.render('index.html', message=msg, level='success')


class CreateStudyAJAX(BaseHandler):
    @authenticated
    def get(self):
        study_title = self.get_argument('study_title', None)
        old_study_title = self.get_argument('old_study_title', None)

        if study_title is None:
            to_write = False
        elif study_title == old_study_title:
            to_write = True
        else:
            to_write = False if Study.exists(study_title) else True

        self.write(str(to_write))
