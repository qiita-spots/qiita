# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division
from os import remove
from os.path import exists, join, basename
from future.utils import viewitems
from collections import defaultdict

from tornado.web import authenticated, HTTPError
from tornado.gen import coroutine, Task
from pandas.parser import CParserError

from qiita_core.qiita_settings import qiita_config
from qiita_db.study import Study
from qiita_db.user import User
from qiita_db.data import RawData, PreprocessedData
from qiita_db.ontology import Ontology
from qiita_db.metadata_template import (PrepTemplate, SampleTemplate,
                                        load_template_to_dataframe)
from qiita_db.util import convert_to_id, get_mountpoint
from qiita_db.exceptions import (QiitaDBUnknownIDError, QiitaDBColumnError,
                                 QiitaDBExecutionError, QiitaDBDuplicateError,
                                 QiitaDBDuplicateHeaderError)
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.util import check_access

html_error_message = "<b>An error occurred %s %s</b></br>%s"


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
            rd = RawData(rd)
            for pt in rd.prep_templates:
                if PrepTemplate.exists(pt):
                    PrepTemplate.delete(pt)
        if SampleTemplate.exists(study_id):
            SampleTemplate.delete(study_id)

        SampleTemplate.create(load_template_to_dataframe(fp_rsp),
                              Study(study_id))
        remove(fp_rsp)

        callback()

    def remove_add_prep_template(self, fp_rpt, raw_data_id, study,
                                 data_type_id, investigation_type, callback):
        """add prep templates
        """
        PrepTemplate.create(load_template_to_dataframe(fp_rpt),
                            RawData(raw_data_id), study, int(data_type_id),
                            investigation_type=investigation_type)
        remove(fp_rpt)

        callback()

    @coroutine
    def display_template(self, study, msg, msg_level, tab_to_display=""):
        """Simple function to avoid duplication of code"""
        user = User(self.current_user)
        # getting the RawData and its prep templates
        available_raw_data = yield Task(self.get_raw_data, study.raw_data())
        available_prep_templates = yield Task(self.get_prep_templates,
                                              available_raw_data)
        # set variable holding if we have files attached to all raw data or not
        raw_files = True if available_raw_data else False
        for r in available_raw_data:
            if not r.get_filepaths():
                raw_files = False

        # set variable holding if we have all prep templates or not
        prep_templates = True if available_prep_templates else False
        for key, val in viewitems(available_prep_templates):
            if not val:
                prep_templates = False

        study_status = study.status
        user_level = user.level
        sample_template_exists = SampleTemplate.exists(study.id)

        # The general information of the study can be changed if the study is
        # not public or if the user is an admin, in which case he can always
        # modify the information of the study
        show_edit_btn = study_status != 'public' or user_level == 'admin'

        # Files can be added to a study only if the study is sandboxed
        # or if the user is the admin
        show_upload_btn = study_status == 'sandbox' or user_level == 'admin'

        # The request approval, approve study and make public buttons are
        # mutually exclusive. Only one of them will be shown, depending on the
        # current status of the study
        btn_to_show = None
        if (study_status == 'sandbox' and qiita_config.require_approval
                and sample_template_exists and raw_files and prep_templates):
            # The request approval button only appears if the study is
            # sandboxed, the qiita_config specifies that the approval should
            # be requested and the sample template, raw files and prep
            # prep templates have been added to the study
            btn_to_show = 'request_approval'
        elif (user_level == 'admin' and study_status == 'awaiting_approval'
                and qiita_config.require_approval):
            # The approve study button only appears if the user is an admin,
            # the study is waiting approval and the qiita config requires
            # study approval
            btn_to_show = 'approve_study'
        elif study_status == 'private':
            # The make public button only appers if the study is private
            btn_to_show = 'make_public'

        # The revert to sandbox button only appears if the study is not
        # sandboxed or public
        show_revert_btn = study_status not in {'sandbox', 'public'}

        self.render('study_description.html',
                    user=self.current_user,
                    study=study,
                    study_title=study.title,
                    study_alias=study.info['study_alias'],
                    show_edit_btn=show_edit_btn,
                    show_upload_btn=show_upload_btn,
                    show_revert_btn=show_revert_btn,
                    btn_to_show=btn_to_show,
                    show_data_tabs=sample_template_exists,
                    tab_to_display=tab_to_display)

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

        self.display_template(study, "", 'info',
                              tab_to_display="study_information_tab")

    @authenticated
    @coroutine
    def post(self, study_id):
        study_id = int(study_id)
        user = User(self.current_user)
        try:
            study = Study(study_id)
        except QiitaDBUnknownIDError:
            # Study not in database so fail nicely
            raise HTTPError(404, "Study %d does not exist" % study_id)
        else:
            check_access(User(self.current_user), study,
                         raise_error=True)

        # vars to add sample template
        msg = ''
        msg_level = ''
        tab_to_display = ''
        sample_template = self.get_argument('sample_template', None)
        # vars to add raw data
        filetype = self.get_argument('filetype', None)
        previous_raw_data = self.get_argument('previous_raw_data', None)
        # vars to add prep template
        add_prep_template = self.get_argument('add_prep_template', None)
        raw_data_id = self.get_argument('raw_data_id', None)
        data_type_id = self.get_argument('data_type_id', None)
        make_public = self.get_argument('make_public', False)
        make_sandbox = self.get_argument('make_sandbox', False)
        approve_study = self.get_argument('approve_study', False)
        request_approval = self.get_argument('request_approval', False)
        investigation_type = self.get_argument('investigation-type', None)
        user_defined_investigation_type = self.get_argument(
            'user-defined-investigation-type', None)
        new_investigation_type = self.get_argument('new-investigation-type',
                                                   None)

        # None Selected is the equivalent to the user not specifying the info
        # thus we should make the investigation_type None
        if investigation_type == "" or investigation_type == "None Selected":
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

        # None Selected is the equivalent to the user not specifying the info
        # thus we should make the investigation_type None
        if edit_investigation_type == "" or \
                edit_investigation_type == "None Selected":
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
                    CParserError, QiitaDBDuplicateHeaderError) as e:
                msg = html_error_message % ('parsing the sample template:',
                                            basename(fp_rsp), str(e))
                self.display_template(study, msg, "danger")
                return

            msg = ("The sample template '%s' has been added" %
                   sample_template)
            tab_to_display = ""

        elif request_approval:
            study.status = 'awaiting_approval'
            msg = "Study sent to admin for approval"
            tab_to_display = ""

        elif make_public:
            msg = ''
            study.status = 'public'
            msg = "Study set to public"
            tab_to_display = ""

        elif make_sandbox:
            msg = ''
            study.status = 'sandbox'
            msg = "Study reverted to sandbox"
            tab_to_display = ""

        elif approve_study:
            # make sure user is admin, then make full private study
            if user.level == 'admin' or not qiita_config.require_approval:
                study.status = 'private'
                msg = "Study approved"
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
                    msg = html_error_message % ("creating a new raw data "
                                                "object for study:",
                                                str(study.id), str(e))
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
                yield Task(self.remove_add_prep_template, fp_rpt, raw_data_id,
                           study, data_type_id, investigation_type)
            except (TypeError, QiitaDBColumnError, QiitaDBExecutionError,
                    QiitaDBDuplicateError, IOError, ValueError,
                    CParserError) as e:
                msg = html_error_message % ("parsing the prep template: ",
                                            basename(fp_rpt), str(e))
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
                msg = html_error_message % (", invalid investigation type: ",
                                            investigation_type, str(e))
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

        for fpid, fp, fpt in files_tuples:
            files[fpt].append(fp)

        with open(files['log'][0], 'U') as f:
            contents = f.read()
            contents = contents.replace('\n', '<br/>')
            contents = contents.replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')

        title = ('Preprocessed Data: %d' % ppd_id)

        self.render('text_file.html', title=title, contents=contents,
                    user=self.current_user, back_button_path=back_button_path)
