# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import re
import warnings
from json import dumps

from tornado.web import HTTPError, authenticated
from wtforms import BooleanField, Form, StringField, validators
from wtforms.validators import ValidationError

import qiita_db as qdb
from qiita_core.exceptions import IncorrectPasswordError
from qiita_core.qiita_settings import qiita_config
from qiita_core.util import execute_as_transaction
from qiita_db.exceptions import QiitaDBError, QiitaDBUnknownIDError
from qiita_db.logger import LogEntry
from qiita_db.user import User
from qiita_db.util import send_email
from qiita_pet.handlers.api_proxy import user_jobs_get_req
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.portal import PortalEditBase


class UserProfile(Form):
    def validate_general(value: str, infomsg: str, url_prefix: str):
        """Validate basic user inputs, i.e. check for leading/trailing
           whitespaces and leading URL prefix, like http://scholar.google.com/

        Parameters
        ----------
        value : str
            The WTform user input string.
        infomsg : str
            An error message to inform the user how to extract the correct
            value.
        url_prefix : str
            The URL prefix of the social network

        Returns
        -------
        None in case of empty input, otherwise the input value

        Raises
        ------
        ValidationError if
          a) input has leading or trailing whitespaces
          b) input starts with the given url_prefix
        """
        if (value is None) or (value == ""):
            # nothing to complain, as input is empty
            return None

        if value != value.strip():
            raise ValidationError(
                "Please remove all leading and trailing whitespaces from your "
                "input.<br/>%s" % infomsg
            )

        if len(url_prefix) > 0:
            isPrefix = re.search("^%s" % url_prefix, value)
            if isPrefix is not None:
                raise ValidationError(
                    'Please remove the "%s" part from your input.<br/>%s'
                    % (isPrefix[0], infomsg)
                )

        # if there is still no error raised, we return the actual value of the
        # user input
        return value

    def validator_orcid_id(form: Form, field: StringField):
        """A WTForm validator to check if user input follows ORCID syntax.

        Parameters
        ----------
        form : wtforms.Form
            The WTform form enclosing the user input field.
        field : wtforms.StringField
            The WTform user input field.

        Returns
        -------
        True, if user input is OK.

        Raises
        ------
        ValidationError if user input is not valid
        """
        infomsg = (
            "Enter only your 16 digit numerical ORCID identifier, where"
            ' every four digits are separated with a dash "-". An '
            "example is: 0000-0002-0975-9019"
        )
        value = UserProfile.validate_general(field.data, infomsg, "https://orcid.org")
        if value is None:
            return True

        if re.search(r"^\d{4}-\d{4}-\d{4}-\d{4}$", value) is None:
            raise ValidationError(
                "Your input does not follow the required format.<br/>%s" % infomsg
            )

    def validator_gscholar_id(form, field):
        """A WTForm validator to check if user input follows google scholar ID
           syntax.

        Parameters
        ----------
        form : wtforms.Form
            The WTform form enclosing the user input field.
        field : wtforms.StringField
            The WTform user input field.

        Returns
        -------
        True, if user input is OK.

        Raises
        ------
        ValidationError if user input is not valid
        """
        infomsg = (
            "To retrieve your google scholar ID, surf to your profile "
            "and copy the URL in your browser. It might read like "
            "https://scholar.google.com/citations?user=_e3QL94AAAAJ&"
            'hl=en<br/>Ignore everything left of the "?". The right '
            'part is a set of key=value pairs, separated by "&" '
            'characters. Find the key "user=", the right part up to '
            'the next "&" is your google scholar ID, in the example: '
            '"_e3QL94AAAAJ"'
        )
        # we need a regex here, since we don't know the TLD the user is
        # presenting to us
        value = UserProfile.validate_general(
            field.data, infomsg, r"https://scholar.google.\w{1,3}/citations\?"
        )
        if value is None:
            return True

        if "&" in value:
            raise ValidationError(
                "Your input contains multiple key=value pairs (we found at "
                'least one "&" character).<br/>%s' % infomsg
            )
        if "user=" in value:
            raise ValidationError(
                'Please remove the key "user" and the "=" character from '
                "your input.<br/>%s" % infomsg
            )
        if value.startswith("="):
            raise ValidationError(
                'Please remove leading "=" characters from your input.<br/>%s' % infomsg
            )

    def validator_rgate_id(form, field):
        """A WTForm validator to check if user input follows ResearchGate
           user names.

        Parameters
        ----------
        form : wtforms.Form
            The WTform form enclosing the user input field.
        field : wtforms.StringField
            The WTform user input field.

        Returns
        -------
        True, if user input is OK.

        Raises
        ------
        ValidationError if user input is not valid
        """
        infomsg = (
            "To retrieve your ResearchGate ID, surf to your profile "
            "and copy the URL in your browser. It might read like "
            "https://www.researchgate.net/profile/Rob-Knight<br/>"
            'Your ID is the part right of the last "/", in the example:'
            ' "Rob-Knight"'
        )
        value = UserProfile.validate_general(
            field.data, infomsg, "https://www.researchgate.net/profile/"
        )
        if value is None:
            return True

    name = StringField("Name", [validators.required()])
    affiliation = StringField("Affiliation")
    address = StringField("Address")
    phone = StringField("Phone")
    receive_processing_job_emails = BooleanField("Receive Processing Job Emails?")

    social_orcid = StringField("ORCID", [validator_orcid_id], description="")
    social_googlescholar = StringField(
        "Google Scholar", [validator_gscholar_id], description=""
    )
    social_researchgate = StringField(
        "ResearchGate", [validator_rgate_id], description=""
    )


class UserProfileHandler(BaseHandler):
    """Displays user profile page and handles profile updates"""

    @authenticated
    def get(self):
        profile = UserProfile()
        profile.process(data=self.current_user.info)
        self.render(
            "user_profile.html",
            profile=profile,
            msg="",
            passmsg="",
            creation_timestamp=self.current_user.info["creation_timestamp"],
        )

    @authenticated
    @execute_as_transaction
    def post(self):
        passmsg = ""
        msg = ""
        user = self.current_user
        action = self.get_argument("action")
        form_data = UserProfile()
        if action == "profile":
            # tuple of columns available for profile
            # FORM INPUT NAMES MUST MATCH DB COLUMN NAMES
            not_str_fields = "receive_processing_job_emails"
            form_data.process(data=self.request.arguments)
            profile = {
                name: data[0].decode("ascii") if name not in not_str_fields else data
                for name, data in form_data.data.items()
            }

            # Turn default value as list into default strings
            for field in form_data:
                if field.name not in not_str_fields:
                    field.data = field.data[0].decode("ascii")
            if form_data.validate() is False:
                msg = (
                    "ERROR: profile could not be updated"
                    " as some of your above inputs must be corrected."
                )
            else:
                try:
                    user.info = profile
                    msg = "Profile updated successfully"
                except Exception as e:
                    msg = "ERROR: profile could not be updated"
                    LogEntry.create(
                        "Runtime",
                        "Cound not update profile: %s" % str(e),
                        info={"User": user.id},
                    )

        elif action == "password":
            form_data.process(data=user.info)
            oldpass = self.get_argument("oldpass")
            newpass = self.get_argument("newpass")
            try:
                changed = user.change_password(oldpass, newpass)
            except Exception as e:
                passmsg = "ERROR: could not change password"
                LogEntry.create(
                    "Runtime",
                    "Could not change password: %s" % str(e),
                    info={"User": user.id},
                )
            else:
                if changed:
                    passmsg = "Password changed successfully"
                else:
                    passmsg = "Incorrect old password"
        self.render(
            "user_profile.html",
            user=user.id,
            profile=form_data,
            msg=msg,
            passmsg=passmsg,
            creation_timestamp=self.current_user.info["creation_timestamp"],
        )


class ForgotPasswordHandler(BaseHandler):
    """Displays forgot password page and generates code for lost passwords"""

    def get(self):
        self.render("lost_pass.html", user=None, message="", level="")

    @execute_as_transaction
    def post(self):
        message = ""
        level = ""
        page = "lost_pass.html"
        user_id = None

        try:
            user = User(self.get_argument("email"))
        except QiitaDBUnknownIDError:
            message = "ERROR: Unknown user."
            level = "danger"
        else:
            user_id = user.id
            user.generate_reset_code()
            info = user.info
            try:
                # qiita_config.base_url doesn't have a / at the end, but the
                # qiita_config.portal_dir has it at the beginning but not at
                # the end. This constructs the correct URL
                url = qiita_config.base_url + qiita_config.portal_dir
                send_email(
                    user.id,
                    "Qiita: Password Reset",
                    "Please go to "
                    "the following URL to reset your password: \n"
                    "%s/auth/reset/%s  \nYou "
                    "have 30 minutes from the time you requested a "
                    "reset to change your password. After this period, "
                    "you will have to request another reset."
                    % (url, info["pass_reset_code"]),
                )
                message = "Check your email for the reset code."
                level = "success"
                page = "index.html"
            except Exception as e:
                message = (
                    "Unable to send email. Error has been registered. "
                    "Your password has not been reset."
                )
                level = "danger"
                LogEntry.create(
                    "Runtime",
                    "Unable to send forgot password email: %s" % str(e),
                    info={"User": user.id},
                )

        self.render(page, user=user_id, message=message, level=level)


class ChangeForgotPasswordHandler(BaseHandler):
    """Displays change password page and handles password reset"""

    def get(self, code):
        self.render("change_lost_pass.html", user=None, message="", level="", code=code)

    @execute_as_transaction
    def post(self, code):
        message = ""
        level = ""
        page = "change_lost_pass.html"
        user = None

        try:
            user = User(self.get_argument("email"))
        except QiitaDBUnknownIDError:
            message = "Unable to reset password"
            level = "danger"
        else:
            newpass = self.get_argument("newpass")
            try:
                changed = user.change_forgot_password(code, newpass)
            except IncorrectPasswordError:
                message = "The new password is not valid. Try again."
                changed = False
            except QiitaDBError:
                message = "Invalid code. Request a new one."
                changed = False

            if changed:
                message = "Password reset successful. Please log in to continue."
                level = "success"
                page = "index.html"
            else:
                if message != "":
                    message = (
                        "Unable to reset password. Most likely your "
                        "email is incorrect or your reset window has "
                        "timed out."
                    )
                level = "danger"

        self.render(page, message=message, level=level, code=code)


class UserMessagesHander(BaseHandler):
    @authenticated
    def get(self):
        self.render("user_messages.html", messages=self.current_user.messages())

    def post(self):
        action = self.get_argument("action")
        messages = self.get_arguments("messages")
        if len(messages) == 0:
            HTTPError(400, "No messages passed")

        if action == "read":
            self.current_user.mark_messages(messages, read=True)
        elif action == "unread":
            self.current_user.mark_messages(messages, read=False)
        elif action == "delete":
            self.current_user.delete_messages(messages)
        else:
            raise HTTPError(400, reason="Unknown action: %s" % action)

        self.render("user_messages.html", messages=self.current_user.messages())


class UserJobs(BaseHandler):
    @authenticated
    def get(self):
        response = user_jobs_get_req(self.current_user)
        self.write(response)


class PurgeUsersAJAXHandler(PortalEditBase):
    # define columns besides email that will be displayed on website
    FIELDS = ["name", "affiliation", "address", "phone", "creation_timestamp"]

    @authenticated
    @execute_as_transaction
    def get(self):
        # retrieving users not yet verified
        self.check_admin()
        with qdb.sql_connection.TRN:
            sql = """SELECT email,{0}
                     FROM qiita.qiita_user
                     WHERE (user_level_id=5) AND
                           (creation_timestamp < (NOW() - INTERVAL '30 DAY'))
                  """.format(",".join(self.FIELDS))
            qdb.sql_connection.TRN.add(sql)
            users = qdb.sql_connection.TRN.execute()[1:]

        # fetching information for each user
        result = []
        for list in users:
            for user in list:
                usermail = user[0]
                user_unit = {"email": usermail}
                user_infos = User(usermail).info
                for col in self.FIELDS:
                    user_unit[col] = str(user_infos[col])
                result.append(user_unit)
        # returning information as JSON
        self.write(dumps(result, separators=(",", ":")))


class PurgeUsersHandler(PortalEditBase):
    @authenticated
    @execute_as_transaction
    def get(self):
        # render page and transfer headers to be included for the table
        self.check_admin()
        self.render(
            "admin_purge_users.html",
            headers=["email"] + PurgeUsersAJAXHandler.FIELDS,
            submit_url="/admin/purge_users/",
        )

    def post(self):
        # check if logged in user is admin and fetch all checked boxes as well
        # as the action
        self.check_admin()
        users = map(str, self.get_arguments("selected"))
        action = self.get_argument("action")

        # depending on the action delete user from db (remove)
        num_deleted_user = 0
        for user in users:
            try:
                with warnings.catch_warnings(record=True) as warns:
                    if action == "Remove":
                        user_to_delete = User(user)
                        user_to_delete.delete(user)
                        num_deleted_user += 1
                    else:
                        raise HTTPError(400, reason="Unknown action: %s" % action)
            except QiitaDBError as e:
                self.write(action.upper() + " ERROR:<br/>" + str(e))
                return
        msg = "; ".join([str(w.message) for w in warns])
        self.write(
            ("%i non-validated user(s) successfully removed from database<br/>%s")
            % (num_deleted_user, msg)
        )
