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
from collections import namedtuple, defaultdict
from json import dumps
from os import remove
from os.path import exists, join, basename
from functools import partial
from operator import itemgetter
from traceback import format_exception_only
from sys import exc_info

from tornado.web import authenticated, HTTPError, asynchronous
from tornado.gen import coroutine, Task
from wtforms import (Form, StringField, SelectField, BooleanField,
                     SelectMultipleField, TextAreaField, validators)
from pandas.parser import CParserError
from future.utils import viewitems

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_ware.context import submit
from qiita_ware.util import dataframe_from_template, stats_from_df
from qiita_ware.demux import stats as demux_stats
from qiita_ware.dispatchable import submit_to_ebi
from qiita_db.metadata_template import (SampleTemplate, PrepTemplate,
                                        load_template_to_dataframe)
from qiita_db.study import Study, StudyPerson
from qiita_db.user import User
from qiita_db.util import (get_filepath_types, get_data_types, get_filetypes,
                           convert_to_id, get_mountpoint,
                           get_files_from_uploads_folders)
from qiita_db.data import PreprocessedData, RawData
from qiita_db.exceptions import (QiitaDBColumnError, QiitaDBExecutionError,
                                 QiitaDBDuplicateError, QiitaDBUnknownIDError)
from qiita_db.ontology import Ontology

from qiita_pet.util import linkify
from .base_handlers import BaseHandler

study_person_linkifier = partial(
    linkify, "<a target=\"_blank\" href=\"mailto:{0}\">{1}</a>")
pubmed_linkifier = partial(
    linkify, "<a target=\"_blank\" href=\"http://www.ncbi.nlm.nih.gov/"
    "pubmed/{0}\">{0}</a>")


def _get_shared_links_for_study(study):
    shared = []
    for person in study.shared_with:
        person = User(person)
        shared.append(study_person_linkifier(
            (person.email, person.info['name'])))
    return ", ".join(shared)


def _build_study_info(studytype, user=None):
        """builds list of namedtuples for study listings"""
        if studytype == "private":
            studylist = user.private_studies
        elif studytype == "shared":
            studylist = user.shared_studies
        elif studytype == "public":
            studylist = Study.get_public()
        else:
            raise IncompetentQiitaDeveloperError("Must use private, shared, "
                                                 "or public!")

        StudyTuple = namedtuple('StudyInfo', 'id title meta_complete '
                                'num_samples_collected shared num_raw_data pi '
                                'pmids owner status')

        infolist = []
        for s_id in studylist:
            study = Study(s_id)
            status = study.status
            # Just passing the email address as the name here, since
            # name is not a required field in qiita.qiita_user
            owner = study_person_linkifier((study.owner, study.owner))
            info = study.info
            PI = StudyPerson(info['principal_investigator_id'])
            PI = study_person_linkifier((PI.email, PI.name))
            pmids = ", ".join([pubmed_linkifier([pmid])
                               for pmid in study.pmids])
            shared = _get_shared_links_for_study(study)
            infolist.append(StudyTuple(study.id, study.title,
                                       info["metadata_complete"],
                                       info["number_samples_collected"],
                                       shared, len(study.raw_data()),
                                       PI, pmids, owner, status))
        return infolist


def check_access(user, study, no_public=False, raise_error=False):
    """make sure user has access to the study requested"""
    if not study.has_access(user, no_public):
        if raise_error:
            raise HTTPError(403, "User %s does not have access to study %d" %
                                 (user.id, study.id))
        else:
            return False
    return True


def _check_owner(user, study):
    """make sure user is the owner of the study requested"""
    if not user == study.owner:
        raise HTTPError(403, "User %s does not own study %d" %
                        (user, study.id))


class CreateStudyForm(Form):
    study_title = StringField('Study Title', [validators.required()])
    study_alias = StringField('Study Alias', [validators.required()])
    pubmed_id = StringField('PubMed ID')

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
    @coroutine
    def get(self):
        self.write(self.render_string('waiting.html'))
        self.flush()
        user = User(self.current_user)
        user_studies = yield Task(self._get_private, user)
        shared_studies = yield Task(self._get_shared, user)
        all_emails_except_current = yield Task(self._get_all_emails)
        all_emails_except_current.remove(self.current_user)
        self.render('private_studies.html', user=self.current_user,
                    user_studies=user_studies, shared_studies=shared_studies,
                    all_emails_except_current=all_emails_except_current)

    def _get_private(self, user, callback):
        callback(_build_study_info("private", user))

    def _get_shared(self, user, callback):
        """builds list of tuples for studies that are shared with user"""
        callback(_build_study_info("shared", user))

    def _get_all_emails(self, callback):
        callback(list(User.iter()))


class PublicStudiesHandler(BaseHandler):
    @authenticated
    @coroutine
    def get(self):
        self.write(self.render_string('waiting.html'))
        self.flush()
        public_studies = yield Task(self._get_public)
        self.render('public_studies.html', user=self.current_user,
                    public_studies=public_studies)

    def _get_public(self, callback):
        """builds list of tuples for studies that are public"""
        callback(_build_study_info("public"))


class PreprocessingSummaryHandler(BaseHandler):
    @authenticated
    def get(self, preprocessed_data_id):
        ppd_id = int(preprocessed_data_id)
        ppd = PreprocessedData(ppd_id)
        study = Study(ppd.study)
        check_access(User(self.current_user), study, raise_error=True)

        back_button_path = self.get_argument(
            'back_button_path', '/study/description/%d' % study.id)

        files_tuples = ppd.get_filepaths()
        files = defaultdict(list)

        for fp, fpt in files_tuples:
            files[fpt].append(fp)

        with open(files['log'][0], 'U') as f:
            contents = f.read()
            contents = contents.replace('\n', '<br/>')
            contents = contents.replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')

        title = ('Preprocessed Data: %d' % ppd_id)

        self.render('text_file.html', title=title, contents=contents,
                    user=self.current_user, back_button_path=back_button_path)


class StudyDescriptionHandler(BaseHandler):
    def get_raw_data(self, rdis, callback):
        """Get all raw data objects from a list of raw_data_ids"""
        callback([RawData(rdi) for rdi in rdis])

    def get_prep_templates(self, raw_data, callback):
        """Get all prep templates for a list of raw data objects"""
        d = {}
        for rd in raw_data:
            # We neeed this so PrepTemplate(p) doesn't fail if that raw
            # doesn't exist but raw data has the row: #554
            prep_templates = sorted(rd.prep_templates)
            d[rd.id] = [PrepTemplate(p) for p in prep_templates
                        if PrepTemplate.exists(p)]
        callback(d)

    def remove_add_study_template(self, raw_data, study_id, fp_rsp, callback):
        """Replace prep templates, raw data, and sample template with a new one
        """
        for rd in raw_data():
            if PrepTemplate.exists((rd)):
                PrepTemplate.delete(rd)
        if SampleTemplate.exists(study_id):
            SampleTemplate.delete(study_id)

        SampleTemplate.create(load_template_to_dataframe(fp_rsp),
                              Study(study_id))
        # TODO: do not remove but move to final storage space
        # and keep there forever, issue #550
        remove(fp_rsp)

        callback()

    def get_raw_data_from_other_studies(self, user, study, callback):
        """Retrieves a tuple of raw_data_id and the last study title for that
        raw_data
        """
        d = {}
        for sid in user.private_studies:
            if sid == study.id:
                continue
            for rdid in Study(sid).raw_data():
                d[rdid] = Study(RawData(rdid).studies[-1]).title
        callback(d)

    @coroutine
    def display_template(self, study, msg, msg_level, tab_to_display=""):
        """Simple function to avoid duplication of code"""
        # getting raw filepath_ types
        fts = [k.split('_', 1)[1].replace('_', ' ')
               for k in get_filepath_types() if k.startswith('raw_')]
        fts = ['<option value="%s">%s</option>' % (f, f) for f in fts]

        user = User(self.current_user)
        # getting the RawData and its prep templates
        available_raw_data = yield Task(self.get_raw_data, study.raw_data())
        available_prep_templates = yield Task(self.get_prep_templates,
                                              available_raw_data)
        # other general vars, note that we create the select options here
        # so we do not have to loop several times over them in the template
        data_types = sorted(viewitems(get_data_types()), key=itemgetter(1))
        data_types = ['<option value="%s">%s</option>' % (v, k)
                      for k, v in data_types]
        filetypes = sorted(viewitems(get_filetypes()), key=itemgetter(1))
        filetypes = ['<option value="%s">%s</option>' % (v, k)
                     for k, v in filetypes]
        other_studies_rd = yield Task(self.get_raw_data_from_other_studies,
                                      user, study)
        other_studies_rd = ['<option value="%s">%s</option>' % (k,
                            "id: %d, study: %s" % (k, v))
                            for k, v in viewitems(other_studies_rd)]

        ontology = Ontology(convert_to_id('ENA', 'ontology'))

        # make "Other" show at the bottom of the drop down menu
        ena_terms = []
        for v in sorted(ontology.terms):
            if v != 'Other':
                ena_terms.append('<option value="%s">%s</option>' % (v, v))
        ena_terms.append('<option value="Other">Other</option>')

        # New Type is for users to add a new user-defined investigation type
        user_defined_terms = ontology.user_defined_terms + ['New Type']
        self.render('study_description.html', user=self.current_user,
                    study_title=study.title, study_info=study.info,
                    study_id=study.id, filetypes=''.join(filetypes),
                    user_level=user.level, data_types=''.join(data_types),
                    available_raw_data=available_raw_data,
                    available_prep_templates=available_prep_templates,
                    ste=SampleTemplate.exists(study.id),
                    filepath_types=''.join(fts), ena_terms=''.join(ena_terms),
                    tab_to_display=tab_to_display,
                    level=msg_level, message=msg,
                    can_upload=check_access(user, study, no_public=True),
                    other_studies_rd=''.join(other_studies_rd),
                    user_defined_terms=user_defined_terms,
                    files=get_files_from_uploads_folders(str(study.id)))

    @authenticated
    def get(self, study_id):
        try:
            study = Study(int(study_id))
        except QiitaDBUnknownIDError:
            # Study not in database so fail nicely
            raise HTTPError(404, "Study %s does not exist" % study_id)
        else:
            check_access(User(self.current_user), study,
                         raise_error=True)

        self.display_template(study, "", 'info')

    @authenticated
    @coroutine
    def post(self, study_id):
        study_id = int(study_id)
        try:
            study = Study(study_id)
        except QiitaDBUnknownIDError:
            # Study not in database so fail nicely
            raise HTTPError(404, "Study %d does not exist" % study_id)
        else:
            check_access(User(self.current_user), study,
                         raise_error=True)

        # vars to add sample template
        sample_template = self.get_argument('sample_template', None)
        # vars to add raw data
        filetype = self.get_argument('filetype', None)
        previous_raw_data = self.get_argument('previous_raw_data', None)
        # vars to add prep template
        add_prep_template = self.get_argument('add_prep_template', None)
        raw_data_id = self.get_argument('raw_data_id', None)
        data_type_id = self.get_argument('data_type_id', None)
        investigation_type = self.get_argument('investigation-type', None)
        user_defined_investigation_type = self.get_argument(
            'user-defined-investigation-type', None)
        new_investigation_type = self.get_argument('new-investigation-type',
                                                   None)

        # non selected is the equivalent to the user not specifying the info
        # thus we should make the investigation_type None
        if investigation_type == "" or investigation_type == "Non selected":
            investigation_type = None

        # to update investigation type
        update_investigation_type = self.get_argument(
            'update_investigation_type', None)
        edit_investigation_type = self.get_argument('edit-investigation-type',
                                                    None)
        edit_user_defined_investigation_type = self.get_argument(
            'edit-user-defined-investigation-type', None)
        edit_new_investigation_type = self.get_argument(
            'edit-new-investigation-type', None)

        # non selected is the equivalent to the user not specifying the info
        # thus we should make the investigation_type None
        if edit_investigation_type == "" or \
                edit_investigation_type == "Non selected":
            edit_investigation_type = None

        msg_level = 'success'
        if sample_template:
            # processing sample templates

            _, base_fp = get_mountpoint("uploads")[0]
            fp_rsp = join(base_fp, str(study_id), sample_template)
            if not exists(fp_rsp):
                raise HTTPError(400, "This file doesn't exist: %s" % fp_rsp)

            try:
                # deleting previous uploads and inserting new one
                yield Task(self.remove_add_study_template,
                           study.raw_data,
                           study_id, fp_rsp)
            except (TypeError, QiitaDBColumnError, QiitaDBExecutionError,
                    QiitaDBDuplicateError, IOError, ValueError, KeyError,
                    CParserError) as e:
                error_msg = ''.join(format_exception_only(e, exc_info()))
                msg = ('<b>An error occurred parsing the sample template: '
                       '%s</b><br/>%s' % (basename(fp_rsp), error_msg))
                self.display_template(study, msg, "danger")
                return

            msg = ("The sample template '%s' has been added" %
                   sample_template)
            tab_to_display = ""

        elif filetype or previous_raw_data:
            # adding blank raw data

            if filetype and previous_raw_data:
                msg = ("You can not specify both a new raw data and a "
                       "previouly used one")
            elif filetype:
                try:
                    RawData.create(filetype, [study])
                except (TypeError, QiitaDBColumnError, QiitaDBExecutionError,
                        QiitaDBDuplicateError, IOError, ValueError, KeyError,
                        CParserError) as e:
                    error_msg = ''.join(format_exception_only(e, exc_info()))
                    msg = ('An error occurred creating a new raw data'
                           'object. %s' % (error_msg))
                    self.display_template(study, msg, "danger")
                    return
                msg = ""
            else:
                raw_data = [RawData(rd) for rd in previous_raw_data]
                study.add_raw_data(raw_data)
                msg = ""
            tab_to_display = ""

        elif add_prep_template and raw_data_id and data_type_id:
            # adding prep templates

            if investigation_type == 'Other' and \
                    user_defined_investigation_type == 'New Type':
                investigation_type = new_investigation_type

                # this is a new user defined investigation type so store it
                ontology = Ontology(convert_to_id('ENA', 'ontology'))
                ontology.add_user_defined_term(investigation_type)
            elif investigation_type == 'Other' and \
                    user_defined_investigation_type != 'New Type':
                investigation_type = user_defined_investigation_type

            raw_data_id = int(raw_data_id)
            _, base_path = get_mountpoint("uploads")[0]
            fp_rpt = join(base_path, str(study_id), add_prep_template)
            if not exists(fp_rpt):
                raise HTTPError(400, "This file doesn't exist: %s" % fp_rpt)

            try:
                # inserting prep templates
                PrepTemplate.create(load_template_to_dataframe(fp_rpt),
                                    RawData(raw_data_id), study,
                                    int(data_type_id),
                                    investigation_type=investigation_type)
            except (TypeError, QiitaDBColumnError, QiitaDBExecutionError,
                    QiitaDBDuplicateError, IOError, ValueError,
                    CParserError) as e:
                error_msg = ''.join(format_exception_only(e, exc_info()))
                msg = ('An error occurred parsing the prep template: '
                       '%s. %s' % (basename(fp_rpt), error_msg))
                self.display_template(study, msg, "danger",
                                      str(raw_data_id))
                return

            msg = "Your prep template was added"
            tab_to_display = str(raw_data_id)

        elif update_investigation_type:
            # updating the prep template investigation type

            pt = PrepTemplate(update_investigation_type)
            investigation_type = edit_investigation_type

            # figure out whether to add it as a user defined term or not
            if edit_investigation_type == 'Other' and \
                    edit_user_defined_investigation_type == 'New Type':
                investigation_type = edit_new_investigation_type

                # this is a new user defined investigation type so store it
                ontology = Ontology(convert_to_id('ENA', 'ontology'))
                ontology.add_user_defined_term(investigation_type)

            elif investigation_type == 'Other' and \
                    user_defined_investigation_type != 'New Type':
                investigation_type = edit_user_defined_investigation_type

            try:
                pt.investigation_type = investigation_type
            except QiitaDBColumnError as e:
                error_msg = ''.join(format_exception_only(e, exc_info()))
                msg = 'Invalid investigation type: %s' % error_msg
                self.display_template(study, msg, "danger",
                                      str(pt.raw_data))
                return

            msg = "The prep template has been updated!"
            tab_to_display = str(pt.raw_data)

        else:
            msg = ("Error, did you select a valid uploaded file or are "
                   "passing the correct parameters?")
            msg_level = 'danger'
            tab_to_display = ""

        self.display_template(study, msg, msg_level, tab_to_display)


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

        msg = 'Study "%s" successfully created' % (
            form_data.data['study_title'][0])

        self.render('index.html', message=msg, level='success',
                    user=self.current_user)


class CreateStudyAJAX(BaseHandler):
    @authenticated
    def get(self):
        study_title = self.get_argument('study_title', None)
        if study_title is None:
            self.write('False')
            return

        self.write('False' if Study.exists(study_title) else 'True')


class ShareStudyAJAX(BaseHandler):
    def _get_shared_for_study(self, study, callback):
        shared_links = _get_shared_links_for_study(study)
        users = study.shared_with
        callback((users, shared_links))

    def _share(self, study, user, callback):
        user = User(user)
        callback(study.share(user))

    def _unshare(self, study, user, callback):
        user = User(user)
        callback(study.unshare(user))

    @authenticated
    @asynchronous
    @coroutine
    def get(self):
        study_id = int(self.get_argument('study_id'))
        study = Study(study_id)
        _check_owner(self.current_user, study)

        selected = self.get_argument('selected', None)
        deselected = self.get_argument('deselected', None)

        if selected is not None:
            yield Task(self._share, study, selected)
        if deselected is not None:
            yield Task(self._unshare, study, deselected)

        users, links = yield Task(self._get_shared_for_study, study)

        self.write(dumps({'users': users, 'links': links}))


class MetadataSummaryHandler(BaseHandler):
    @authenticated
    def get(self, arguments):
        study_id = int(self.get_argument('study_id'))

        # this block is tricky because you can either pass the sample or the
        # prep template and if none is passed then we will let an exception
        # be raised because template will not be declared for the logic below
        if self.get_argument('prep_template', None):
            template = PrepTemplate(int(self.get_argument('prep_template')))
        if self.get_argument('sample_template', None):
            template = None
            tid = int(self.get_argument('sample_template'))
            try:
                template = SampleTemplate(tid)
            except QiitaDBUnknownIDError:
                raise HTTPError(404, "SampleTemplate %d does not exist" % tid)

        study = Study(template.study_id)

        # check whether or not the user has access to the requested information
        if not study.has_access(User(self.current_user)):
            raise HTTPError(403, "You do not have access to access this "
                                 "information.")

        df = dataframe_from_template(template)
        stats = stats_from_df(df)

        self.render('metadata_summary.html', user=self.current_user,
                    study_title=study.title, stats=stats,
                    study_id=study_id)


class EBISubmitHandler(BaseHandler):
    def display_template(self, preprocessed_data_id, msg, msg_level):
        """Simple function to avoid duplication of code"""
        preprocessed_data_id = int(preprocessed_data_id)
        try:
            preprocessed_data = PreprocessedData(preprocessed_data_id)
        except QiitaDBUnknownIDError:
            raise HTTPError(404, "PreprocessedData %d does not exist!" %
                                 preprocessed_data_id)
        else:
            user = User(self.current_user)
            if user.level != 'admin':
                raise HTTPError(403, "No permissions of admin, "
                                     "get/EBISubmitHandler: %s!" % user.id)

        prep_template = PrepTemplate(preprocessed_data.prep_template)
        sample_template = SampleTemplate(preprocessed_data.study)
        study = Study(preprocessed_data.study)
        stats = [('Number of samples', len(prep_template)),
                 ('Number of metadata headers',
                  len(sample_template.metadata_headers()))]

        demux = [path for path, ftype in preprocessed_data.get_filepaths()
                 if ftype == 'preprocessed_demux']

        if not len(demux):
            msg = ("Study does not appear to have demultiplexed "
                   "sequences associated")
            msg_level = 'danger'
        elif len(demux) > 1:
            msg = ("Study appears to have multiple demultiplexed files!")
            msg_level = 'danger'
        elif msg == "":
            demux_file = demux[0]
            demux_file_stats = demux_stats(demux_file)
            stats.append(('Number of sequences', demux_file_stats.n))
            msg_level = 'success'

        self.render('ebi_submission.html', user=self.current_user,
                    study_title=study.title, stats=stats, message=msg,
                    study_id=study.id, level=msg_level,
                    preprocessed_data_id=preprocessed_data_id,
                    investigation_type=prep_template.investigation_type)

    @authenticated
    def get(self, preprocessed_data_id):
        self.display_template(preprocessed_data_id, "", "")

    @authenticated
    def post(self, preprocessed_data_id):
        # make sure user is admin and can therefore actually submit to EBI
        if User(self.current_user).level != 'admin':
            raise HTTPError(403, "User %s cannot submit to EBI!" %
                            self.current_user)
        submission_type = self.get_argument('submission_type')

        if submission_type not in ['ADD', 'MODIFY']:
            raise HTTPError(403, "User: %s, %s is not a recognized submission "
                            "type" % (self.current_user, submission_type))

        msg = ''
        msg_level = 'success'
        preprocessed_data = PreprocessedData(preprocessed_data_id)
        state = preprocessed_data.submitted_to_insdc_status()
        if state == 'submitting':
            msg = "Cannot resubmit! Current state is: %s" % state
            msg_level = 'danger'
        elif state == 'success' and submission_type == "ADD":
            msg = "Cannot resubmit! Current state is: %s, use MODIFY" % state
            msg_level = 'danger'
        else:
            channel = self.current_user
            job_id = submit(channel, submit_to_ebi, int(preprocessed_data_id),
                            submission_type)

            self.render('compute_wait.html', user=self.current_user,
                        job_id=job_id, title='EBI Submission',
                        completion_redirect='/compute_complete/%s' % job_id)
            return

        self.display_template(preprocessed_data_id, msg, msg_level)
