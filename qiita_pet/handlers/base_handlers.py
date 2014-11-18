from tornado.web import RequestHandler
from qiita_db.logger import LogEntry
from qiita_db.user import User


class BaseHandler(RequestHandler):

    def get_current_user(self):
        '''Overrides default method of returning user curently connected'''
        user = self.get_secure_cookie("user")
        if user is None:
            self.clear_cookie("user")
            return None
        else:
            return user.strip('" ')

    def write_error(self, status_code, **kwargs):
        '''Overrides the error page created by Tornado'''
        if status_code == 404:
            # just use the 404 page as the error
            self.render("404.html", user=self.current_user)
            return

        is_admin = User(self.current_user).level == 'admin'

        # render error page
        self.render('error.html', user=self.current_user,
                    status_code=status_code, is_admin=is_admin)

        # log the error
        from traceback import format_exception
        exc_info = kwargs["exc_info"]
        trace_info = ''.join(["%s\n" % line for line in
                             format_exception(*exc_info)])
        request_info = ''.join(["<strong>%s</strong>: %s\n" %
                               (k, self.request.__dict__[k]) for k in
                                self.request.__dict__.keys()])
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
        username = self.current_user
        self.render("index.html", user=username, message='', level='')


class MockupHandler(BaseHandler):
    def get(self):
        self.render("mockup.html", user=self.current_user)


class NoPageHandler(BaseHandler):
    def get(self):
        self.set_status(404)
        self.render("404.html", user=self.current_user)

    def head(self):
        """Satisfy servers that this url exists"""
        self.set_status(404)
        self.finish()
