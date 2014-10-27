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

from tornado.web import authenticated, HTTPError
from wtforms import (Form, StringField, SelectField, BooleanField,
                     SelectMultipleField, TextAreaField, validators)

from os import listdir
from os.path import exists, join, basename

from .base_handlers import BaseHandler

from qiita_core.qiita_settings import qiita_config

from qiita_ware.context import submit
from qiita_ware.util import metadata_stats_from_sample_and_prep_templates
from qiita_ware.demux import stats as demux_stats
from qiita_ware.dispatchable import submit_to_ebi
from qiita_db.metadata_template import (SampleTemplate, PrepTemplate,
                                        load_template_to_dataframe)
from qiita_db.study import Study, StudyPerson
from qiita_db.user import User
from qiita_db.util import get_study_fp, convert_to_id, get_filepath_types
from qiita_db.ontology import Ontology
from qiita_db.data import PreprocessedData
from qiita_db.exceptions import (QiitaDBColumnError, QiitaDBExecutionError,
                                 QiitaDBDuplicateError, QiitaDBUnknownIDError)
from qiita_db.data import RawData


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
    def display_template(self, study_id, msg):
        """Simple function to avoid duplication of code"""

        # processing paths
        fp = get_study_fp(study_id)
        if exists(fp):
            fs = [f for f in listdir(fp)]
        else:
            fs = []
        fts = [k.split('_', 1)[1].replace('_', ' ')
               for k in get_filepath_types() if k.startswith('raw_')]

        # getting the raw_data
        study = Study(study_id)
        valid_ssb = []
        for rdi in study.raw_data():
            rd = RawData(rdi)
            ex = PrepTemplate.exists(rd)
            if ex:
                valid_ssb.append(rdi)

        # get the prep template id and force to choose the first one
        # see issue https://github.com/biocore/qiita/issues/415
        if valid_ssb:
            prep_template_id = valid_ssb[0]
            split_libs_status = RawData(
                prep_template_id).preprocessing_status.replace('\n', '<br/>')

            # getting EBI status
            sppd = study.preprocessed_data()
            if sppd:
                ebi_status = PreprocessedData(
                    sppd[-1]).submitted_to_insdc_status()
            else:
                ebi_status = None
        else:
            prep_template_id = None
            split_libs_status = None
            ebi_status = None

        valid_ssb = ','.join(map(str, valid_ssb))
        ssb = len(valid_ssb) > 0

        # getting the ontologies
        ena = Ontology(convert_to_id('ENA', 'ontology'))
        user = User(self.current_user)
        self.render('study_description.html', user=self.current_user,
                    study_title=study.title, study_info=study.info,
                    study_id=study_id, files=fs, ssb=ssb, vssb=valid_ssb,
                    max_upload_size=qiita_config.max_upload_size,
                    sls=split_libs_status, filetypes=fts,
                    investigation_types=ena.terms, ebi_status=ebi_status,
                    prep_template_id=prep_template_id, user_level=user.level,
                    msg=msg)

    @authenticated
    def get(self, study_id):
        self.display_template(int(study_id), "")

    @authenticated
    def post(self, study_id):
        raw_sample_template = self.get_argument('raw_sample_template', None)
        raw_prep_template = self.get_argument('raw_prep_template', None)
        barcodes = self.get_argument('barcodes', "").split(',')
        forward_seqs = self.get_argument('forward_seqs', "").split(',')
        reverse_seqs = self.get_argument('reverse_seqs', "").split(',')
        investigation_type = self.get_argument('investigation-type', "")

        if raw_sample_template is None or raw_prep_template is None:
            raise HTTPError(400, "This function needs a sample template: "
                            "%s and a prep template: %s" %
                            (raw_sample_template, raw_prep_template))
        fp_rsp = join(get_study_fp(study_id), raw_sample_template)
        fp_rpt = join(get_study_fp(study_id), raw_prep_template)
        if not exists(fp_rsp):
            raise HTTPError(400, "This file doesn't exist: %s" % fp_rsp)
        if not exists(fp_rpt):
            raise HTTPError(400, "This file doesn't exist: %s" % fp_rpt)

        ena = Ontology(convert_to_id('ENA', 'ontology'))
        if (not investigation_type or investigation_type == "" or
                investigation_type not in ena.terms):
            raise HTTPError(400, "You need to have an investigation type")

        study_id = int(study_id)
        study = Study(study_id)

        # deleting previous uploads
        for rd in study.raw_data():
            if PrepTemplate.exists(RawData(rd)):
                PrepTemplate.delete(rd)
        if SampleTemplate.exists(study):
            SampleTemplate.delete(study_id)

        try:
            # inserting sample template
            SampleTemplate.create(load_template_to_dataframe(fp_rsp), study)
        except (TypeError, QiitaDBColumnError, QiitaDBExecutionError,
                QiitaDBDuplicateError, IOError), e:
            msg = ('<b>An error occurred parsing the sample template: '
                   '%s</b><br/>%s' % (basename(fp_rsp), e))
            self.display_template(int(study_id), msg)
            return

        # inserting raw data
        fp = get_study_fp(study_id)
        filepaths = []
        if barcodes and barcodes[0] != "":
            filepaths.extend([(join(fp, t), "raw_barcodes") for t in barcodes])
        if forward_seqs and forward_seqs[0] != "":
            filepaths.extend([(join(fp, t), "raw_forward_seqs")
                              for t in forward_seqs])
        if reverse_seqs and reverse_seqs[0] != "":
            filepaths.extend([(join(fp, t), "raw_reverse_seqs")
                              for t in reverse_seqs])

        # currently hardcoding the filetypes, see issue
        # https://github.com/biocore/qiita/issues/391
        filetype = 2

        try:
            # currently hardcoding the study_ids to be an array but not sure
            # if this will ever be an actual array via the web interface
            raw_data = RawData.create(filetype, [study], 1, filepaths,
                                      investigation_type)
        except (TypeError, QiitaDBColumnError, QiitaDBExecutionError,
                IOError), e:
            fps = ', '.join([basename(f[0]) for f in filepaths])
            msg = ('<b>An error occurred parsing the raw files: '
                   '%s</b><br/>%s' % (basename(fps), e))
            self.display_template(int(study_id), msg)
            return

        try:
            # inserting prep templates
            PrepTemplate.create(load_template_to_dataframe(fp_rpt), raw_data,
                                study)
        except (TypeError, QiitaDBColumnError, QiitaDBExecutionError,
                IOError), e:
            msg = ('<b>An error occurred parsing the prep template: '
                   '%s</b><br/>%s' % (basename(fp_rpt), e))
            self.display_template(int(study_id), msg)
            return

        msg = "Your samples were processed"
        self.display_template(int(study_id), msg)


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

        # TODO: change this redirect to something more sensible
        self.redirect('/')


class CreateStudyAJAX(BaseHandler):
    @authenticated
    def get(self):
        study_title = self.get_argument('study_title', None)
        if study_title is None:
            self.write('False')
            return

        self.write('False' if Study.exists(study_title) else 'True')


class MetadataSummaryHandler(BaseHandler):
    @authenticated
    def get(self, arguments):
        study_id = int(self.get_argument('sample_template'))
        st = SampleTemplate(study_id)
        pt = PrepTemplate(int(self.get_argument('prep_template')))

        stats = metadata_stats_from_sample_and_prep_templates(st, pt)

        self.render('metadata_summary.html', user=self.current_user,
                    study_title=Study(st.id).title, stats=stats,
                    study_id=study_id)


class EBISubmitHandler(BaseHandler):
    def display_template(self, study, sample_template, preprocessed_data,
                         error):
        """Simple function to avoid duplication of code"""

        if not study:
            study_title = 'This study DOES NOT exist'
            study_id = 'This study DOES NOT exist'
        else:
            study_title = study.title
            study_id = study.id

        if not error:
            stats = [('Number of samples', len(sample_template)),
                     ('Number of metadata headers',
                      len(sample_template.metadata_headers()))]

            demux = [path for path, ftype in preprocessed_data.get_filepaths()
                     if ftype == 'preprocessed_demux']

            if not len(demux):
                error = ("Study does not appear to have demultiplexed "
                         "sequences associated")
            elif len(demux) > 1:
                error = ("Study appears to have multiple demultiplexed files!")
            else:
                error = ""
                demux_file = demux[0]
                demux_file_stats = demux_stats(demux_file)
                stats.append(('Number of sequences', demux_file_stats.n))

            error = None
        else:
            stats = []

        self.render('ebi_submission.html', user=self.current_user,
                    study_title=study_title, stats=stats, error=error,
                    study_id=study_id)

    @authenticated
    def get(self, study_id):
        preprocessed_data = None
        sample_template = None
        error = None

        # this could be done with exists but it works on the title and
        # we do not have that
        try:
            study = Study(int(study_id))
        except (QiitaDBUnknownIDError):
            study = None
            error = 'There is no study %s' % study_id

        if study:
            try:
                sample_template = SampleTemplate(study.sample_template)
            except:
                sample_template = None
                error = 'There is no sample template for study: %s' % study_id

            try:
                # TODO: only supporting a single prep template right now, which
                # should be the last item
                preprocessed_data = PreprocessedData(
                    study.preprocessed_data()[-1])
            except:
                preprocessed_data = None
                error = ('There is no preprocessed data for study: '
                         '%s' % study_id)

        self.display_template(study, sample_template, preprocessed_data, error)

    @authenticated
    def post(self, study_id):
        # make sure user is admin and can therefore actually submit to EBI
        if User(self.current_user).level != 'admin':
            raise HTTPError(403, "User %s cannot submit to EBI!" %
                            self.current_user)

        channel = self.current_user
        job_id = submit(channel, submit_to_ebi, int(study_id))

        self.render('compute_wait.html', user=self.current_user,
                    job_id=job_id, title='EBI Submission',
                    completion_redirect='/compute_complete/%s/' % job_id)
