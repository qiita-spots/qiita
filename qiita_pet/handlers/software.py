# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from copy import deepcopy

from tornado.gen import coroutine

from qiita_core.util import execute_as_transaction
from qiita_db.software import DefaultWorkflow, Software

from .base_handlers import BaseHandler


class SoftwareHandler(BaseHandler):
    @coroutine
    @execute_as_transaction
    def get(self):
        # active True will only show active software
        active = True
        user = self.current_user
        if user is not None and user.level in {"admin", "dev"}:
            active = False

        software = Software.iter(active=active)
        self.render("software.html", software=software)


def _retrive_workflows(active):
    # helper method to avoid duplication of code
    def _default_parameters_parsing(node):
        dp = node.default_parameter
        cmd = dp.command
        cmd_name = "params_%d" % node.id
        rp = deepcopy(cmd.required_parameters)
        op = deepcopy(cmd.optional_parameters)
        params = dict()
        for param, value in dp.values.items():
            if param in rp:
                del rp[param]
            if param in op:
                del op[param]
            params[param] = str(value)

        inputs = []
        outputs = []
        for input in rp.values():
            accepted_values = " | ".join(input[1])
            inputs.append([cmd.id, accepted_values])
        for output in cmd.outputs:
            outputs.append([cmd.id, " | ".join(output)])
        fcmd_name = cmd.name if not cmd.naming_order else f"{cmd.name} | {dp.name}"

        return ([cmd_name, cmd.id, fcmd_name, dp.name, params], inputs, outputs)

    workflows = []
    for w in DefaultWorkflow.iter(active=active):
        # getting the main default parameters
        nodes = []
        edges = []
        at = w.artifact_type

        # first get edges as this will give us the main connected commands
        # and their order
        graph = w.graph
        # inputs is {input_type: node_name, ...} for easy look up of
        # raw_inputs and reuse of the node_name
        inputs = dict()
        # main_nodes is {main_node_name: {
        #                   output_type: output_node_name}, ...}
        # for easy look up and merge of output_names
        main_nodes = dict()
        not_used_nodes = {n.id: n for n in graph.nodes}
        standalone_input = None
        for i, (x, y) in enumerate(graph.edges):
            if x.id in not_used_nodes:
                del not_used_nodes[x.id]
            if y.id in not_used_nodes:
                del not_used_nodes[y.id]
            vals_x, input_x, output_x = _default_parameters_parsing(x)
            vals_y, input_y, output_y = _default_parameters_parsing(y)

            connections = []
            for a, _, c in graph[x][y]["connections"].connections:
                connections.append("%s | %s" % (a, c))

            if i == 0:
                # we are in the first element so we can specifically select
                # the type we are looking for
                if input_x and at in input_x[0][1]:
                    input_x[0][1] = at
                elif input_x:
                    input_x[0][1] = "** WARNING, NOT DEFINED **"
                else:
                    # if we get to this point it means that the workflow has a
                    # multiple commands starting from the main single input,
                    # thus is fine to link them to the same raw data
                    standalone_input = vals_x[0]
                    input_x = [["", at]]

            name_x = vals_x[0]
            name_y = vals_y[0]
            if vals_x not in (nodes):
                nodes.append(vals_x)
                if name_x not in main_nodes:
                    main_nodes[name_x] = dict()
                for a, b in input_x:
                    name = "input_%s_%s" % (name_x, b)
                    if b in inputs:
                        name = inputs[b]
                    else:
                        name = "input_%s_%s" % (name_x, b)
                        if standalone_input is not None:
                            standalone_input = name
                    vals = [name, a, b]
                    if vals not in nodes:
                        inputs[b] = name
                        nodes.append(vals)
                    edges.append([name, vals_x[0]])
                for a, b in output_x:
                    name = "output_%s_%s" % (name_x, b)
                    vals = [name, a, b]
                    if vals not in nodes:
                        nodes.append(vals)
                    edges.append([name_x, name])
                    main_nodes[name_x][b] = name

            if vals_y not in (nodes):
                nodes.append(vals_y)
                if name_y not in main_nodes:
                    main_nodes[name_y] = dict()
            for a, b in input_y:
                # checking if there is an overlap between the parameter
                # and the connections; if there is, use the connection
                overlap = set(main_nodes[name_x]) & set(connections)
                if overlap:
                    # use the first hit
                    b = list(overlap)[0]

                if b in main_nodes[name_x]:
                    name = main_nodes[name_x][b]
                else:
                    name = "input_%s_%s" % (name_y, b)
                    vals = [name, a, b]
                    if vals not in nodes:
                        nodes.append(vals)
                edges.append([name, name_y])
            for a, b in output_y:
                name = "output_%s_%s" % (name_y, b)
                vals = [name, a, b]
                if vals not in nodes:
                    nodes.append(vals)
                edges.append([name_y, name])
                main_nodes[name_y][b] = name

        wparams = w.parameters

        # This case happens when a workflow has 2 commands from the initial
        # artifact and one of them has more processing after
        if not_used_nodes and (nodes or edges) and standalone_input is None:
            standalone_input = edges[0][0]

        # note that this block is similar but not identical to adding connected
        # nodes
        for i, (_, x) in enumerate(not_used_nodes.items()):
            vals_x, input_x, output_x = _default_parameters_parsing(x)
            if input_x and at in input_x[0][1]:
                input_x[0][1] = at
            elif input_x:
                input_x[0][1] = "** WARNING, NOT DEFINED **"
            else:
                # if we get to this point it means that these are "standalone"
                # commands, thus is fine to link them to the same raw data
                if standalone_input is None:
                    standalone_input = vals_x[0]
                input_x = [["", at]]

            name_x = vals_x[0]
            if vals_x not in (nodes):
                nodes.append(vals_x)
                for a, b in input_x:
                    if b in inputs:
                        name = inputs[b]
                    else:
                        name = "input_%s_%s" % (name_x, b)
                    # if standalone_input == name_x then this is the first time
                    # we are processing a standalone command so we need to add
                    # the node and store the name of the node for future usage
                    if standalone_input is None:
                        nodes.append([name, a, b])
                    elif standalone_input == name_x:
                        nodes.append([name, a, b])
                        standalone_input = name
                    else:
                        name = standalone_input
                    edges.append([name, vals_x[0]])
                for a, b in output_x:
                    name = "output_%s_%s" % (name_x, b)
                    nodes.append([name, a, b])
                    edges.append([name_x, name])

        workflows.append(
            {
                "name": w.name,
                "id": w.id,
                "data_types": w.data_type,
                "description": w.description,
                "active": w.active,
                "parameters_sample": wparams["sample"],
                "parameters_prep": wparams["prep"],
                "nodes": nodes,
                "edges": edges,
            }
        )

    return workflows


class WorkflowsHandler(BaseHandler):
    @coroutine
    @execute_as_transaction
    def get(self):
        # active True will only show active workflows
        active = True
        user = self.current_user
        if user is not None and user.level in {"admin", "dev"}:
            active = False

        workflows = _retrive_workflows(active)

        self.render("workflows.html", workflows=workflows)
