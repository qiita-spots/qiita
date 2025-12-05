import ast
import json

from tornado.gen import Task, coroutine
from tornado.web import HTTPError, authenticated

from qiita_core.qiita_settings import r_client
from qiita_core.util import execute_as_transaction

from .base_handlers import BaseHandler

commands = "resources:commands"
default_col_name = "samples * columns"


class ResourcesHandler(BaseHandler):
    def check_admin(self):
        if self.current_user.level != "admin":
            raise HTTPError(
                403,
                reason="%s does not have access to portal "
                "editing!" % self.current_user.id,
            )

    @execute_as_transaction
    def _get_resources(self, cname, sname, version, col_name, callback):
        resources = {}
        vals = [
            ("img_mem", r_client.get),
            ("img_time", r_client.get),
            ("time", r_client.get),
            ("title_mem", r_client.get),
            ("title_time", r_client.get),
        ]
        for k, f in vals:
            redis_key = "resources$#%s$#%s$#%s$#%s:%s" % (
                cname,
                sname,
                version,
                col_name,
                k,
            )
            resources[k] = f(redis_key)
        callback(resources)

    @execute_as_transaction
    def _get_commands(self, callback):
        res = r_client.get(commands)
        callback(res)

    @authenticated
    @coroutine
    @execute_as_transaction
    def get(self):
        self.check_admin()
        commands = yield Task(self._get_commands)

        commands_str = commands.decode("utf-8")
        commands_dict = ast.literal_eval(commands_str)
        commands_json = json.dumps(commands_dict)

        self.render(
            "resources.html",
            img_mem=None,
            img_time=None,
            time=None,
            mk=None,
            ma=None,
            mb=None,
            mmodel=None,
            mreal=None,
            mcalc=None,
            mfail=None,
            tk=None,
            ta=None,
            tb=None,
            tmodel=None,
            treal=None,
            tcalc=None,
            tfail=None,
            commands=commands_json,
            initial_load=True,
        )

    @authenticated
    @coroutine
    @execute_as_transaction
    def post(self):
        try:
            data = json.loads(self.request.body)
            software = data.get("software")
            version = data.get("version")
            command = data.get("command")

            resources = yield Task(
                self._get_resources, command, software, version, default_col_name
            )

            mcof, mmodel, mreal, mcalc, mfail = list(
                map(
                    lambda x: x.split(b": ")[1].strip().decode("utf-8"),
                    resources["title_mem"].split(b"\n"),
                )
            )

            tcof, tmodel, treal, tcalc, tfail = list(
                map(
                    lambda x: x.split(b": ")[1].strip().decode("utf-8"),
                    resources["title_time"].split(b"\n"),
                )
            )

            mk, ma, mb = mcof.split("||")
            tk, ta, tb = tcof.split("||")

            response_data = {
                "status": "success",
                "img_mem": resources["img_mem"].decode("utf-8")
                if isinstance(resources["img_mem"], bytes)
                else resources["img_mem"],
                "img_time": resources["img_time"].decode("utf-8")
                if isinstance(resources["img_time"], bytes)
                else resources["img_time"],
                "time": resources["time"].decode("utf-8")
                if isinstance(resources["time"], bytes)
                else resources["time"],
                "mk": mk,
                "ma": ma,
                "mb": mb,
                "tk": tk,
                "ta": ta,
                "tb": tb,
                "mmodel": mmodel,
                "mreal": mreal,
                "mcalc": mcalc,
                "mfail": mfail,
                "tcof": tcof,
                "tmodel": tmodel,
                "treal": treal,
                "tcalc": tcalc,
                "tfail": tfail,
                "initial_load": False,
            }
            self.write(json.dumps(response_data) + "\n")

        except json.JSONDecodeError:
            self.set_status(400)
            self.finish({"error": "Invalid JSON data"})
        except Exception as e:
            import traceback

            print(traceback.format_exc())
            if resources["title_mem"] is None:
                response_data = {
                    "status": "no_data",
                    "img_mem": None,
                    "img_time": None,
                    "time": None,
                    "mk": None,
                    "ma": None,
                    "mb": None,
                    "tk": None,
                    "ta": None,
                    "tb": None,
                    "mmodel": None,
                    "mreal": None,
                    "mcalc": None,
                    "mfail": None,
                    "tcof": None,
                    "tmodel": None,
                    "treal": None,
                    "tcalc": None,
                    "tfail": None,
                    "initial_load": False,
                }
                self.set_status(200)
                self.write(json.dumps(response_data) + "\n")
            else:
                self.set_status(500)
                self.finish({"error": str(e)})
