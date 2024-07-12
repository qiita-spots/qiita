
from tornado.gen import coroutine, Task
from tornado.web import authenticated, HTTPError


from .base_handlers import BaseHandler
from qiita_core.qiita_settings import qiita_config, r_client
from qiita_core.util import execute_as_transaction

default_cname = "Split libraries FASTQ"
default_sname = "QIIMEq2"
default_col_name = "samples * columns"
commands = 'resources:commands'

class ResourcesHandler(BaseHandler):
    def check_admin(self):
        if self.current_user.level != "admin":
            raise HTTPError(403, reason="%s does not have access to portal "
                            "editing!" % self.current_user.id)


    @execute_as_transaction
    def _get_resources(self, callback):
        resources = {}
        vals = [
            ('img', r_client.get),
            ('time', r_client.get)
        ]
        for k, f in vals:
            redis_key = 'resources$#%s$#%s$#%s:%s' % (default_cname,
                                            default_sname, default_col_name, k)
            resources[k] = f(redis_key)
        callback(resources)


    def _get_commands(self, callback):
        r_client.get(commands)
        callback(r_client)

    
    @authenticated
    @coroutine
    @execute_as_transaction
    def get(self):
        self.check_admin()
        resources = yield Task(self._get_resources)
        commands = yield Task(self._get_commands) # TODO: it would make more sense to have this rendered once instead of everytime we make a get request, but i'm not sure how to do that right now
        self.render('resources.html',
            img=resources['img'], time=resources['time'],
            commands=commands,
            software=default_sname, command=default_cname,
            col_name=default_col_name
        )


    @authenticated
    @execute_as_transaction
    def post(self):
        self.check_admin()
        software = self.get_argument("software", "")
        command = self.get_argument("command", "")
        column_type = self.get_argument("column_type", "")
        

        self.get()
        

