from tornado.web import authenticated, HTTPError
from future.utils import viewitems
from wtforms import Form, StringField, validators

from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_db.user import User
from qiita_db.logger import LogEntry
from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_core.util import send_email, execute_as_transaction
from qiita_core.qiita_settings import qiita_config


class UserProfile(Form):
    name = StringField("Name", [validators.required()])
    affiliation = StringField("Affiliation")
    address = StringField("Address")
    phone = StringField("Phone")


class UserProfileHandler(BaseHandler):
    """Displays user profile page and handles profile updates"""
    @authenticated
    def get(self):
        profile = UserProfile()
        profile.process(data=self.current_user.info)
        self.render("user_profile.html", profile=profile, msg="", passmsg="")

    @authenticated
    @execute_as_transaction
    def post(self):
        passmsg = ""
        msg = ""
        user = self.current_user
        action = self.get_argument("action")
        if action == "profile":
            # tuple of colmns available for profile
            # FORM INPUT NAMES MUST MATCH DB COLUMN NAMES
            form_data = UserProfile()
            form_data.process(data=self.request.arguments)
            profile = {name: data[0] for name, data in
                       viewitems(form_data.data)}

            # Turn default value as list into default strings
            for field in form_data:
                field.data = field.data[0]
            try:
                user.info = profile
                msg = "Profile updated successfully"
            except Exception as e:
                msg = "ERROR: profile could not be updated"
                LogEntry.create('Runtime', "Cound not update profile: %s" %
                                str(e), info={'User': user.id})

        elif action == "password":
            form_data = UserProfile()
            form_data.process(data=user.info)
            oldpass = self.get_argument("oldpass")
            newpass = self.get_argument("newpass")
            try:
                changed = user.change_password(oldpass, newpass)
            except Exception as e:
                passmsg = "ERROR: could not change password"
                LogEntry.create('Runtime', "Could not change password: %s" %
                                str(e), info={'User': user.id})
            else:
                if changed:
                    passmsg = "Password changed successfully"
                else:
                    passmsg = "Incorrect old password"
        self.render("user_profile.html", user=user.id, profile=form_data,
                    msg=msg, passmsg=passmsg)


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
                send_email(user.id, "Qiita: Password Reset", "Please go to "
                           "the following URL to reset your password: \n"
                           "%s/%s/auth/reset/%s  \nYou "
                           "have 30 minutes from the time you requested a "
                           "reset to change your password. After this period, "
                           "you will have to request another reset." %
                           (qiita_config.base_url, qiita_config.portal_dir,
                            info["pass_reset_code"]))
                message = ("Check your email for the reset code.")
                level = "success"
                page = "index.html"
            except Exception as e:
                message = ("Unable to send email. Error has been registered. "
                           "Your password has not been reset.")
                level = "danger"
                LogEntry.create('Runtime', "Unable to send forgot password "
                                "email: %s" % str(e), info={'User': user.id})

        self.render(page, user=user_id, message=message, level=level)


class ChangeForgotPasswordHandler(BaseHandler):
    """Displays change password page and handles password reset"""
    def get(self, code):
            self.render("change_lost_pass.html", user=None, message="",
                        level="", code=code)

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
            changed = user.change_forgot_password(code, newpass)

            if changed:
                message = ("Password reset successful. Please log in to "
                           "continue.")
                level = "success"
                page = "index.html"
            else:
                message = ("Unable to reset password. Most likely your email "
                           "is incorrect or your reset window has timed out.")

                level = "danger"

        self.render(page, message=message, level=level, code=code)


class UserMessagesHander(BaseHandler):
    @authenticated
    def get(self):
        self.render("user_messages.html",
                    messages=self.current_user.messages())

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
            raise HTTPError(400, "Unknown action: %s" % action)

        self.render("user_messages.html",
                    messages=self.current_user.messages())
