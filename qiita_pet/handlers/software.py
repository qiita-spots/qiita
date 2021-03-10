# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from tornado.gen import coroutine

from qiita_core.util import execute_as_transaction
from qiita_db.software import Software, DefaultWorkflow
from .base_handlers import BaseHandler
from copy import deepcopy


class SoftwareHandler(BaseHandler):
    @coroutine
    @execute_as_transaction
    def get(self):
        # active True will only show active software
        active = True
        user = self.current_user
        if user is not None and user.level in {'admin', 'dev'}:
            active = False

        software = Software.iter(active=active)
        self.render("software.html", software=software)


class WorkflowsHandler(BaseHandler):
    @coroutine
    @execute_as_transaction
    def get(self):
        # active True will only show active workflows
        active = True
        user = self.current_user
        if user is not None and user.level in {'admin', 'dev'}:
            active = False

        workflows = []
        previous_outputs = []
        for w in DefaultWorkflow.iter(active=active):
            # getting the main default parameters
            nodes = []
            edges = []
            for order, n in enumerate(w.graph.nodes):
                dp = n.default_parameter
                cmd = dp.command

                # looping over the default parameters to make sure we got them
                # all from required and optional parameters; whatever is left
                # from required, are our inputs
                rp = deepcopy(cmd.required_parameters)
                op = deepcopy(cmd.optional_parameters)
                params = dict()
                for param, value in dp.values.items():
                    if param in rp:
                        del rp[param]
                    if param in op:
                        del op[param]
                    params[param] = str(value)

                # cmd_name, command id, command name,
                # default params name, default parameters
                cmd_name = 'command_%d' % order
                nodes.append([cmd_name, cmd.id, cmd.name,
                              dp.name, params])
                for input in rp.values():
                    accepted_values = ' | '.join(input[1])
                    if order == 0:
                        name = 'input_%d' % order
                        nodes.append([name, cmd.id, accepted_values])
                    else:
                        name = 'output_%d_%s' % (order - 1, accepted_values)
                    edges.append([name, cmd_name])

                for output in cmd.outputs:
                    previous_outputs.append(output[1])
                    name = 'output_%d_%s' % (order, output[1])
                    nodes.append([name, cmd.id, output[1]])
                    edges.append([cmd_name, name])

            workflows.append(
                {'name': w.name, 'id': w.id, 'data_types': w.data_type,
                 'nodes': nodes, 'edges': edges})
        self.render("workflows.html", workflows=workflows)
