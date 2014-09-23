from tornado.web import authenticated

from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_db.user import User
from qiita_db.logger import LogEntry
from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_core.util import send_email


class UserProfileHandler(BaseHandler):
    """Displays user profile page and handles profile updates"""
    @authenticated
    def get(self):
        user = self.current_user
        self.render("user_profile.html", user=user, profile=User(user).info,
                    msg="", passmsg="")

    @authenticated
    def post(self):
        user = User(self.current_user)
        action = self.get_argument("action")
        if action == "profile":
            profile = {}
            # tuple of colmns available for profile
            # FORM INPUT NAMES MUST MATCH DB COLUMN NAMES
            profileinfo = ("name", "affiliation", "address", "phone")
            for info in profileinfo:
                profile[info] = self.get_argument(info, None)

            try:
                user.info = profile
                msg = "Profile updated successfully"
            except Exception as e:
                msg = "ERROR: profile could not be updated"
                LogEntry.create('Runtime', "Cound not update profile: %s" %
                                str(e), info={'User': user.id})
        elif action == "password":
            profile = user.info
            oldpass = self.get_argument("oldpass")
            newpass = self.get_argument("newpass")
            try:
                user.change_password(oldpass, newpass)
            except Exception as e:
                passmsg = "ERROR: could not change password"
                LogEntry.create('Runtime', "Cound not change password: %s" %
                                str(e), info={'User': user.id})
            else:
                passmsg = "Password changed successfully"
        self.render("user_profile.html", user=user.id, profile=profile,
                    msg=msg, passmsg="")


class ForgotPasswordHandler(BaseHandler):
    """Displays forgot password page and generates code for lost passwords"""
    def get(self):
        self.render("lost_pass.html", user=None, error="")

    def post(self):
        error = ""
        try:
            user = User(self.get_argument("email"))
        except QiitaDBUnknownIDError:
            error = "ERROR: Unknown user."
        else:
            user.generate_reset_code()
            info = user.info
            try:
                send_email(user, "QIITA: Password Reset", "Please go to the "
                           "following URL to reset your password: "
                           "http://qiita.colorado.edu/auth/reset/%s" %
                           info["pass_reset_code"])
                error = "Password reset. Check your email for the reset code."
            except Exception as e:
                error = "Unable to send email."
                LogEntry.create('Runtime', "Unable to send forgot password "
                                "email" % str(e), info={'User': user.id})
        self.render("lost_pass.html", user=None, error=error)


class ChangeForgotPassHandler(BaseHandler):
    """Displays change password page and handles password reset"""
    def get(self, code):
            self.render("change_lost_pass.html", user=None, error="",
                        code=code)

    def post(self, code):
        error = ""
        try:
            user = User(self.get_argument("email"))
        except QiitaDBUnknownIDError:
            error = "Unable to reset password"
        else:
            newpass = self.get_argument("newpass")
            changed = user.change_forgot_password(code, newpass)
            if changed:
                error="Password reset successful. Please log in to continue."
            else:
                error = "Unable to reset password"

        self.render("change_lost_pass.html", user=None,
                    error=error, code=code)
