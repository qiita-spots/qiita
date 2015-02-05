# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

import warnings

from os import remove
from os.path import exists, join, basename
from future.utils import viewvalues
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


def _approve(level):
    """Check if the study can be approved based on user level and configuration

    Parameters
    ----------
    level : str
        The level of the current user

    Returns
    -------
    bool
        Whether the study can be approved or not
    """
    return True if not qiita_config.require_approval else level == 'admin'


def _to_int(value):
    """Transforms `value` to an integer

    Parameters
    ----------
    value : str or int
        The value to transform

    Returns
    -------
    int
        `value` as an integer

    Raises
    ------
    HTTPError
        If `value` cannot be transformed to an integer
    """
    try:
        res = int(value)
    except ValueError:
        raise HTTPError(500, "%s cannot be converted to an integer" % value)
    return res


class StudyDescriptionHandler(BaseHandler):

    def _get_sudy_and_check_access(self, study_id):
        """Checks if the current user has access to the study

        First tries to instantiate the study object. Then it checks if the
        current user has access to such study.

        Parameters
        ----------
        study_id : str or int
            The current study

        Returns
        -------
        The study object and the current user object

        Raises
        ------
        HTTPError
            If study_id does not correspond to any study in the system
        """
        user = User(self.current_user)

        try:
            study = Study(_to_int(study_id))
        except (QiitaDBUnknownIDError, HTTPError):
            # Study not in database so fail nicely
            raise HTTPError(404, "Study %s does not exist" % study_id)
        else:
            check_access(user, study, raise_error=True)

        return study, user

    def _process_investigation_type(self, inv_type, user_def_type, new_type):
        """Return the investigation_type and add it to the ontology if needed

        Parameters
        ----------
        inv_type : str
            The investigation type
        user_def_type : str
            The user-defined investigation type
        new_type : str
            The new user-defined investigation_type

        Returns
        -------
        str
            The investigation type chosen by the user
        """
        if inv_type == 'None Selected':
            inv_type = None
        elif inv_type == 'Other' and user_def_type == 'New Type':
            # This is a nre user defined investigation type so store it
            inv_type = new_type
            ontology = Ontology(convert_to_id('ENA', 'ontology'))
            ontology.add_user_defined_term(inv_type)
        elif inv_type == 'Other' and user_def_type != 'New Type':
            inv_type = user_def_type
        return inv_type

    def process_sample_template(self, study, user, callback):
        """Process a sample template from the POST method

        Parameters
        ----------
        study : Study
            The current study object
        user : User
            The current user object
        callback : function
            The callback function to call with the results once the processing
            is done

        Raises
        ------
        HTTPError
            If the sample template file does not exists
        """
        # If we are on this function, the argument "sample_template" must
        # defined. If not, let tornado raise its error
        sample_template = self.get_argument('sample_template')

        # Define here the message and message level in case of success
        msg = "The sample template '%s' has been added" % sample_template
        msg_level = "success"
        # Get the uploads folder
        _, base_fp = get_mountpoint("uploads")[0]
        # Get the path of the sample template in the uploads folder
        fp_rsp = join(base_fp, str(study.id), sample_template)

        if not exists(fp_rsp):
            # The file does not exists, fail nicely
            raise HTTPError(400, "This file doesn't exist: %s" % fp_rsp)

        try:
            with warnings.catch_warnings(record=True) as warns:
                # force all warnings to always be triggered
                warnings.simplefilter("always")

                # deleting previous uploads and inserting new one
                self.remove_add_study_template(study.raw_data, study.id,
                                               fp_rsp)

                # join all the warning messages into one. Note that this info
                # will be ignored if an exception is raised
                if warns:
                    msg_level = 'warning'
                    msg = '; '.join([str(w.message) for w in warns])

        except (TypeError, QiitaDBColumnError, QiitaDBExecutionError,
                QiitaDBDuplicateError, IOError, ValueError, KeyError,
                CParserError, QiitaDBDuplicateHeaderError) as e:
            # Some error occurred while processing the sample template
            # Show the error to the user so he can fix the template
            msg = html_error_message % ('parsing the sample template:',
                                        basename(fp_rsp), str(e))
            msg_level = "danger"

        callback((msg, msg_level, 'sample_template_tab', None, None))

    def create_raw_data(self, study, user, callback):
        """Adds a (new) raw data to the study

        Parameters
        ----------
        study : Study
            The current study object
        user : User
            The current user object
        callback : function
            The callback function to call with the results once the processing
            is done
        """
        msg = "Raw data successfully added"
        msg_level = "success"

        # Get the arguments needed to create a raw data object
        filetype = self.get_argument('filetype', None)
        previous_raw_data = self.get_argument('previous_raw_data', None)

        if filetype and previous_raw_data:
            # The user selected a filetype and an existing raw data
            msg = ("You can not specify both a new raw data and a previously "
                   "used one")
            msg_level = "danger"
        elif filetype:
            # We are creating a new raw data object
            try:
                rd_id = RawData.create(filetype, [study]).id
            except (TypeError, QiitaDBColumnError, QiitaDBExecutionError,
                    QiitaDBDuplicateError, IOError, ValueError, KeyError,
                    CParserError) as e:
                msg = html_error_message % (
                    "creating a new raw data object for study:",
                    str(study.id), str(e))
                msg_level = "danger"
        elif previous_raw_data:
            previous_raw_data = previous_raw_data.split(',')
            raw_data = [RawData(rd) for rd in previous_raw_data]
            study.add_raw_data(raw_data)
            rd_id = raw_data[0].id
        else:
            # The user did not provide a filetype neither an existing raw data
            # If using the interface, we should never reach this if, but
            # better be safe than sorry
            msg = ("You should choose a filetype for a new raw data or "
                   "choose a raw data previously used")
            msg_level = "danger"
            rd_id = None

        callback((msg, msg_level, 'raw_data_tab', rd_id, None))

    def add_prep_template(self, study, user, callback):
        """Adds a prep template to the system

        Parameters
        ----------
        study : Study
            The current study object
        user : User
            The current user object
        callback : function
            The callback function to call with the results once the processing
            is done
        """
        msg = "Your prep template was added"
        msg_level = "success"

        # If we are on this function, the arguments "raw_data_id",
        # "prep_template" and "data_type_id" must be defined. If not,
        # let tornado raise its error
        raw_data_id = self.get_argument('raw_data_id')
        prep_template = self.get_argument('prep_template')
        data_type_id = self.get_argument('data_type_id')

        # These parameters are optional
        investigation_type = self.get_argument('investigation-type', None)
        user_defined_investigation_type = self.get_argument(
            'user-defined-investigation-type', None)
        new_investigation_type = self.get_argument('new-investigation-type',
                                                   None)

        investigation_type = self._process_investigation_type(
            investigation_type, user_defined_investigation_type,
            new_investigation_type)

        # Make sure that the id is an integer
        raw_data_id = _to_int(raw_data_id)
        # Get the upload base directory
        _, base_path = get_mountpoint("uploads")[0]
        # Get the path to the prep template
        fp_rpt = join(base_path, str(study.id), prep_template)
        if not exists(fp_rpt):
            # The file does not exists, fail nicely
            raise HTTPError(400, "This file doesn't exist: %s" % fp_rpt)

        try:
            with warnings.catch_warnings(record=True) as warns:
                # force all warnings to always be triggered
                warnings.simplefilter("always")

                # deleting previous uploads and inserting new one
                pt_id = self.remove_add_prep_template(fp_rpt, raw_data_id,
                                                      study, data_type_id,
                                                      investigation_type)

                # join all the warning messages into one. Note that this info
                # will be ignored if an exception is raised
                if warns:
                    msg = '; '.join([str(w.message) for w in warns])
                    msg_level = 'danger'
        except (TypeError, QiitaDBColumnError, QiitaDBExecutionError,
                QiitaDBDuplicateError, IOError, ValueError,
                CParserError) as e:
            pt_id = None
            # Some error occurred while processing the prep template
            # Show the error to the user so he can fix the template
            msg = html_error_message % ("parsing the prep template: ",
                                        basename(fp_rpt), str(e))
            msg_level = "danger"

        callback((msg, msg_level, 'raw_data_tab', raw_data_id, pt_id))

    def make_public(self, study, user, callback):
        """Makes the current study public

        Parameters
        ----------
        study : Study
            The current study object
        user : User
            The current user object
        callback : function
            The callback function to call with the results once the processing
            is done
        """
        study.status = 'public'
        msg = "Study set to public"
        msg_level = "success"
        callback((msg, msg_level, "study_information_tab", None, None))

    def approve_study(self, study, user, callback):
        """Approves the current study if and only if the current user is admin

        Parameters
        ----------
        study : Study
            The current study object
        user : User
            The current user object
        callback : function
            The callback function to call with the results once the processing
            is done
        """
        if _approve(user.level):
            study.status = 'private'
            msg = "Study approved"
            msg_level = "success"
        else:
            msg = ("The current user does not have permission to approve "
                   "the study")
            msg_level = "danger"
        callback((msg, msg_level, "study_information_tab", None, None))

    def request_approval(self, study, user, callback):
        """Changes the status of the current study to "awaiting_approval"

        Parameters
        ----------
        study : Study
            The current study object
        user : User
            The current user object
        callback : function
            The callback function to call with the results once the processing
            is done
        """
        study.status = 'awaiting_approval'
        msg = "Study sent to admin for approval"
        msg_level = "success"
        callback((msg, msg_level, "study_information_tab", None, None))

    def make_sandbox(self, study, user, callback):
        """Reverts the current study to the 'sandbox' status

        Parameters
        ----------
        study : Study
            The current study object
        user : User
            The current user object
        callback : function
            The callback function to call with the results once the processing
            is done
        """
        study.status = 'sandbox'
        msg = "Study reverted to sandbox"
        msg_level = "success"
        callback((msg, msg_level, "study_information_tab", None, None))

    def update_investigation_type(self, study, user, callback):
        """Updates the investigation type of a prep template

        Parameters
        ----------
        study : Study
            The current study object
        user : User
            The current user object
        callback : function
            The callback function to call with the results once the processing
            is done
        """
        msg = "investigation type successfully updated"
        msg_level = "success"

        ppd_id = int(self.get_argument('ppd_id'))

        prep_id = self.get_argument('prep_id')
        edit_investigation_type = self.get_argument('edit-investigation-type',
                                                    None)
        edit_user_defined_investigation_type = self.get_argument(
            'edit-user-defined-investigation-type', None)
        edit_new_investigation_type = self.get_argument(
            'edit-new-investigation-type', None)

        pt = PrepTemplate(prep_id)
        rd_id = pt.raw_data

        investigation_type = self._process_investigation_type(
            edit_investigation_type, edit_user_defined_investigation_type,
            edit_new_investigation_type)

        try:
            pt.investigation_type = investigation_type
        except QiitaDBColumnError as e:
            msg = html_error_message % (", invalid investigation type: ",
                                        investigation_type, str(e))
            msg_level = "danger"

        if ppd_id == 0:
            top_tab = "raw_data_tab"
            sub_tab = rd_id
            prep_tab = prep_id
        else:
            top_tab = "preprocessed_data_tab"
            sub_tab = ppd_id
            prep_tab = None

        callback((msg, msg_level, top_tab, sub_tab, prep_tab))

    def unspecified_action(self, study, user, callback):
        """If the action is not recognized, we return an error message

        Parameters
        ----------
        study : Study
            The current study object
        user : User
            The current user object
        callback : function
            The callback function to call with the results once the processing
            is done
        """
        msg = ("Error, did you select a valid uploaded file or are passing "
               "the correct parameters?")
        msg_level = 'danger'
        callback((msg, msg_level, 'study_information_tab', None, None))

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

    def remove_add_study_template(self, raw_data, study_id, fp_rsp):
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

    def remove_add_prep_template(self, fp_rpt, raw_data_id, study,
                                 data_type_id, investigation_type):
        """add prep templates"""
        pt_id = PrepTemplate.create(load_template_to_dataframe(fp_rpt),
                                    RawData(raw_data_id), study,
                                    _to_int(data_type_id),
                                    investigation_type=investigation_type).id
        remove(fp_rpt)
        return pt_id

    @coroutine
    def display_template(self, study, user, msg, msg_level, top_tab=None,
                         sub_tab=None, prep_tab=None):
        """Simple function to avoid duplication of code"""
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
        if available_prep_templates:
            _test = lambda item: not item
            prep_templates = all(
                [_test(val) for val in viewvalues(available_prep_templates)])
        else:
            prep_templates = False

        study_status = study.status
        user_level = user.level
        sample_template_exists = SampleTemplate.exists(study.id)

        # The general information of the study can be changed if the study is
        # not public or if the user is an admin, in which case they can always
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
                    message=msg,
                    level=msg_level,
                    user=self.current_user,
                    study=study,
                    study_title=study.title,
                    study_alias=study.info['study_alias'],
                    show_edit_btn=show_edit_btn,
                    show_upload_btn=show_upload_btn,
                    show_revert_btn=show_revert_btn,
                    btn_to_show=btn_to_show,
                    show_data_tabs=sample_template_exists,
                    top_tab=top_tab,
                    sub_tab=sub_tab,
                    prep_tab=prep_tab)

    @authenticated
    def get(self, study_id):
        study, user = self._get_sudy_and_check_access(study_id)

        top_tab = self.get_argument('top_tab', 'study_information_tab')
        sub_tab = self.get_argument('sub_tab', None)
        prep_tab = self.get_argument('prep_tab', None)

        self.display_template(study, user, "", 'info', top_tab=top_tab,
                              sub_tab=sub_tab, prep_tab=prep_tab)

    @authenticated
    @coroutine
    def post(self, study_id):
        study, user = self._get_sudy_and_check_access(study_id)

        # Define a dictionary with all the supported actions
        actions = defaultdict(
            lambda: self.unspecified_action,
            process_sample_template=self.process_sample_template,
            create_raw_data=self.create_raw_data,
            add_prep_template=self.add_prep_template,
            make_public=self.make_public,
            approve_study=self.approve_study,
            request_approval=self.request_approval,
            make_sandbox=self.make_sandbox,
            update_investigation_type=self.update_investigation_type)

        # Get the action that we need to perform
        action = self.get_argument("action", None)
        action_f = actions[action]

        msg, msg_level, top_tab, sub_tab, prep_tab = yield Task(action_f,
                                                                study, user)

        # Display the function
        self.display_template(study, user, msg, msg_level, top_tab, sub_tab,
                              prep_tab)


class PreprocessingSummaryHandler(BaseHandler):
    def _get_template_variables(self, preprocessed_data_id, callback):
        """Generates all the variables needed to render the template

        Parameters
        ----------
        preprocessed_data_id : int
            The preprocessed data identifier
        callback : function
            The callback function to call with the results once the processing
            is done

        Raises
        ------
        HTTPError
            If the preprocessed data does not have a log file
        """
        # Get the objects and check user privileges
        ppd = PreprocessedData(preprocessed_data_id)
        study = Study(ppd.study)
        check_access(User(self.current_user), study, raise_error=True)

        # Get the return address
        back_button_path = self.get_argument(
            'back_button_path',
            '/study/description/%d?top_tab=preprocessed_data_tab&sub_tab=%s'
            % (study.id, preprocessed_data_id))

        # Get all the filepaths attached to the preprocessed data
        files_tuples = ppd.get_filepaths()

        # Group the files by filepath type
        files = defaultdict(list)
        for _, fp, fpt in files_tuples:
            files[fpt].append(fp)

        try:
            log_path = files['log'][0]
        except KeyError:
            raise HTTPError(500, "Log file not found in preprocessed data %s"
                                 % preprocessed_data_id)

        with open(log_path, 'U') as f:
            contents = f.read()
            contents = contents.replace('\n', '<br/>')
            contents = contents.replace('\t', '&nbsp;&nbsp;&nbsp;&nbsp;')

        title = 'Preprocessed Data: %d' % preprocessed_data_id

        callback((title, contents, back_button_path))

    @authenticated
    @coroutine
    def get(self, preprocessed_data_id):
        ppd_id = _to_int(preprocessed_data_id)

        title, contents, back_button_path = yield Task(
            self._get_template_variables, ppd_id)

        self.render('text_file.html', title=title, contents=contents,
                    user=self.current_user, back_button_path=back_button_path)
