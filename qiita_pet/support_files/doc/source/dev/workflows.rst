.. _workflows:

.. index :: workflows

Qiita Workflows
===============

The Qiita Workflows allow developers to define full software pipelines of how a
give data type can be processed. A given Qiita Workflow will also define which
commands a user can see in the GUI and allow to add that "default" workflow to
a preparation via a single click on the GUI.

How to add a workflow?
----------------------

#. Add the workflow

   - `INSERT INTO qiita.default_workflow (name)...;`


#. Add the data types that can use that workflow

   - `INSERT INTO qiita.default_workflow_data_type (data_type_id, default_workflow_id) ...;`


#. Add nodes (commands) via the default_parameter_set of the commands (you are selecting
   the command and their parameters at once). Note that order is not important as we are going to link (organize) them in the next point.

   - `INSERT INTO qiita.default_workflow_node (default_parameter_set_id, default_workflow_id) ...;`


#. Link the nodes (via edges)

   - `INSERT INTO qiita.default_workflow_edge (parent_id, child_id) ...;`


#. Link the specific output (as commands can have multiple) of the parent nodes/commands to their
   children (inputs)

   - `INSERT INTO qiita.default_workflow_edge_connections (default_workflow_edge_id, parent_output_id, child_input_id) ...;`
