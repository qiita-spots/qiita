from tornado.web import authenticated

from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_db.user import User
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
            except:
                msg = "ERROR: profile could not be updated"
        elif action == "password":
            profile = user.info
            oldpass = self.get_argument("oldpass")
            newpass = self.get_argument("newpass")
            try:
                user.change_password(oldpass, newpass)
            except:
                passmsg = "ERROR: could not change password"
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
            user.generate_reset_code()
            info = user.info
        except QiitaDBUnknownIDError:
            error = "ERROR: Unknown user."
        else:
            try:
                send_email(user, "QIITA: Password Reset", "Please go to the "
                           "following URL to reset your password: "
                           "http://qiita.colorado.edu/auth/reset/%s" %
                           info["pass_reset_code"])
                error = "Password reset. Check your email for the reset code."
            except:
                error = "Unable to send email."
        self.render("lost_pass.html", user=None, error=error)


class ChangeForgotPassHandler(BaseHandler):
    """Displays change password page and handles password reset"""
    def get(self, code):
            self.render("change_lost_pass.html", user=None, error="",
                        code=code)

    def post(self, code):
        try:
            user = User(self.get_argument("email"))
        except QiitaDBUnknownIDError:
            self.render("change_lost_pass.html", user=None,
                        error="Unable to reset password", code=code)
            return
        newpass = self.get_argument("newpass")
        changed = user.change_forgot_password(code, newpass)
        if changed:
            self.render("change_lost_pass.html", user=None,
                        error="Password reset successful. Please log in to "
                        "continue.", code=code)
        else:
            self.render("change_lost_pass.html", user=None,
                        error="Unable to reset password", code=code)
