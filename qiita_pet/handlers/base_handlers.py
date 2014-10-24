from tornado.web import RequestHandler


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
        from traceback import format_exception
        if self.settings.get("debug") and "exc_info" in kwargs:
            exc_info = kwargs["exc_info"]
            trace_info = ''.join(["%s<br />" % line for line in
                                 format_exception(*exc_info)])
            request_info = ''.join(["<strong>%s</strong>: %s<br />" %
                                   (k, self.request.__dict__[k]) for k in
                                    self.request.__dict__.keys()])
            error = exc_info[1]

            self.render('error.html', error=error, trace_info=trace_info,
                        request_info=request_info,
                        user=self.current_user)

    def head(self):
        """Adds proper response for head requests"""
        self.finish()


class MainHandler(BaseHandler):
    '''Index page'''
    def get(self):
        username = self.current_user
        completedanalyses = []
        self.render("index.html", user=username, analyses=completedanalyses)


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
