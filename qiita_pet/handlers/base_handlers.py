from tornado.web import RequestHandler
from qiita_db.logger import LogEntry
from qiita_db.user import User


class BaseHandler(RequestHandler):
    def get_current_user(self):
        '''Overrides default method of returning user curently connected'''
        username = self.get_secure_cookie("user")
        if username is not None:
            # strip off quotes added by get_secure_cookie
            username = username.strip("\"' ")
            return User(username)
        else:
            self.clear_cookie("user")
            return None

    def write_error(self, status_code, **kwargs):
        '''Overrides the error page created by Tornado'''
        if status_code == 404:
            # just use the 404 page as the error
            self.render("404.html")
            return

        if status_code == 403:
            # We don't need to log this failues in the logging table
            return

        is_admin = False
        user = self.get_current_user()
        if user:
            try:
                is_admin = user.level == 'admin'
            except:
                # Any issue with this check leaves default as not admin
                pass

        # render error page
        self.render('error.html', status_code=status_code, is_admin=is_admin)

        # log the error
        from traceback import format_exception
        exc_info = kwargs["exc_info"]
        trace_info = ''.join(["%s\n" % line for line in
                             format_exception(*exc_info)])
        req_dict = self.request.__dict__
        # must trim body to 1024 chars to prevent huge error messages
        req_dict['body'] = req_dict.get('body', '')[:1024]
        request_info = ''.join(["<strong>%s</strong>: %s\n" %
                               (k, req_dict[k]) for k in
                                req_dict.keys() if k != 'files'])
        error = exc_info[1]
        LogEntry.create(
            'Runtime',
            'ERROR:\n%s\nTRACE:\n%s\nHTTP INFO:\n%s\n' %
            (error, trace_info, request_info))

    def head(self):
        """Adds proper response for head requests"""
        self.finish()


class MainHandler(BaseHandler):
    '''Index page'''
    def get(self):
        msg = self.get_argument('message', '')
        lvl = self.get_argument('level', '')
        self.render("index.html", message=msg, level=lvl)


class MockupHandler(BaseHandler):
    def get(self):
        self.render("mockup.html")


class NoPageHandler(BaseHandler):
    def get(self):
        self.set_status(404)
        self.render("404.html")

    def head(self):
        """Satisfy servers that this url exists"""
        self.set_status(404)
        self.finish()
