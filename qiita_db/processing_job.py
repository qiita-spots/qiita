# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from uuid import UUID
from datetime import datetime
from subprocess import Popen, PIPE
from multiprocessing import Process
from os.path import join
from itertools import chain

from future.utils import viewitems, viewvalues
import networkx as nx

from qiita_core.qiita_settings import qiita_config
import qiita_db as qdb


def _system_call(cmd):
    """Call cmd and return (stdout, stderr, return_value)

    Parameters
    ----------
    cmd : str or iterator of str
        The string containing the command to be run, or a sequence of strings
        that are the tokens of the command.

    Notes
    -----
    This function is ported from QIIME (http://www.qiime.org), previously named
    qiime_system_call. QIIME is a GPL project, but we obtained permission from
    the authors of this function to port it to Qiita and keep it under BSD
    license.
    """
    proc = Popen(cmd, universal_newlines=True, shell=True, stdout=PIPE,
                 stderr=PIPE)
    # Communicate pulls all stdout/stderr from the PIPEs
    # This call blocks until the command is done
    stdout, stderr = proc.communicate()
    return_value = proc.returncode
    return stdout, stderr, return_value


def _job_submitter(job, cmd):
    """Executes the commands `cmd` and updates the job in case of failure

    Parameters
    ----------
    job : qiita_db.processing_job.ProcesingJob
        The job that is executed by cmd
    cmd : str
        The command to execute the job
    """
    std_out, std_err, return_value = _system_call(cmd)
    if return_value != 0:
        error = ""
        job.complete(False, error=error)


class ProcessingJob(qdb.base.QiitaObject):
    r"""Models a job that executes a command in a set of artifacts

    Attributes
    ----------
    user
    command
    parameters
    status
    log
    heartbeat
    step

    Methods
    -------
    exists
    create
    """
    _table = 'processing_job'

    @classmethod
    def exists(cls, job_id):
        """Check if the job `job_id` exists

        Parameters
        ----------
        job_id : str
            The job id

        Returns
        -------
        bool
            True if the job `job_id` exists. False otherwise.
        """
        try:
            UUID(job_id)
        except ValueError:
            return False

        with qdb.sql_connection.TRN:
            sql = """SELECT EXISTS(SELECT *
                                   FROM qiita.processing_job
                                   WHERE processing_job_id = %s)"""
            qdb.sql_connection.TRN.add(sql, [job_id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @classmethod
    def create(cls, user, parameters):
        """Creates a new job in the system

        Parameters
        ----------
        user : qiita_db.user.User
            The user executing the job
        parameters : qiita_db.software.Parameters
            The parameters of the job being executed

        Returns
        -------
        qiita_db.processing_job.ProcessingJob
            The newly created job
        """
        with qdb.sql_connection.TRN:
            command = parameters.command
            sql = """INSERT INTO qiita.processing_job
                        (email, command_id, command_parameters,
                         processing_job_status_id)
                     VALUES (%s, %s, %s, %s)
                     RETURNING processing_job_id"""
            status = qdb.util.convert_to_id(
                "in_construction", "processing_job_status")
            sql_args = [user.id, command.id,
                        parameters.dump(), status]
            qdb.sql_connection.TRN.add(sql, sql_args)
            job_id = qdb.sql_connection.TRN.execute_fetchlast()

            # Link the job with the input artifacts
            sql = """INSERT INTO qiita.artifact_processing_job
                        (artifact_id, processing_job_id)
                     VALUES (%s, %s)"""
            for pname, vals in command.parameters.items():
                if vals[0] == 'artifact':
                    artifact_info = parameters.values[pname]
                    # If the artifact_info is a list, then the artifact
                    # still doesn't exists because the current job is part
                    # of a workflow, so we can't link
                    if not isinstance(artifact_info, list):
                        qdb.sql_connection.TRN.add(
                            sql, [artifact_info, job_id])

            qdb.sql_connection.TRN.execute()

            return cls(job_id)

    @property
    def user(self):
        """The user that launched the job

        Returns
        -------
        qiita_db.user.User
            The user that launched the job
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT email
                     FROM qiita.processing_job
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            email = qdb.sql_connection.TRN.execute_fetchlast()
            return qdb.user.User(email)

    @property
    def command(self):
        """The command that the job executes

        Returns
        -------
        qiita_db.software.Command
            The command that the job executes
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT command_id
                     FROM qiita.processing_job
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            cmd_id = qdb.sql_connection.TRN.execute_fetchlast()
            return qdb.software.Command(cmd_id)

    @property
    def parameters(self):
        """The parameters used in the job's command

        Returns
        -------
        qiita_db.software.Parameters
            The parameters used in the job's command
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT command_id, command_parameters
                     FROM qiita.processing_job
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            res = qdb.sql_connection.TRN.execute_fetchindex()[0]
            return qdb.software.Parameters.load(
                qdb.software.Command(res[0]), values_dict=res[1])

    @property
    def input_artifacts(self):
        """The artifacts used as input in the job

        Returns
        -------
        list of qiita_db.artifact.Artifact
            The artifacs used as input in the job
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT artifact_id
                     FROM qiita.artifact_processing_job
                     WHERE processing_job_id = %s
                     ORDER BY artifact_id"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return [qdb.artifact.Artifact(aid)
                    for aid in qdb.sql_connection.TRN.execute_fetchflatten()]

    @property
    def status(self):
        """The status of the job

        Returns
        -------
        {'queued', 'running', 'success', 'error', 'in_construction', 'waiting'}
            The current status of the job
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT processing_job_status
                     FROM qiita.processing_job_status
                        JOIN qiita.processing_job
                            USING (processing_job_status_id)
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    def _set_status(self, value):
        """Sets the status of the job

        Parameters
        ----------
        value : str, {'queued', 'running', 'success', 'error',
                      'in_construction', 'waiting'}
            The new status of the job

        Raises
        ------
        qiita_db.exceptions.QiitaDBStatusError
            - If the current status of the job is 'success'
            - If the current status of the job is 'running' and `value` is
            'queued'
        """
        with qdb.sql_connection.TRN:
            current_status = self.status
            if current_status == 'success':
                raise qdb.exceptions.QiitaDBStatusError(
                    "Cannot change the status of a 'success' job")
            elif current_status == 'running' and value == 'queued':
                raise qdb.exceptions.QiitaDBStatusError(
                    "Cannot revert the status of a 'running' job to 'queued'")

            new_status = qdb.util.convert_to_id(
                value, "processing_job_status")
            sql = """UPDATE qiita.processing_job
                     SET processing_job_status_id = %s
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [new_status, self.id])
            qdb.sql_connection.TRN.execute()

    def _generate_cmd(self):
        """Generates the command to submit the job

        Returns
        -------
        str
            The command to use to submit the job
        """
        job_dir = join(qdb.util.get_work_base_dir(), self.id)
        software = self.command.software
        plugin_start_script = software.start_script
        plugin_env_script = software.environment_script
        cmd = '%s "%s" "%s" "%s" "%s" "%s"' % (
            qiita_config.plugin_launcher, plugin_env_script,
            plugin_start_script, qiita_config.base_url, self.id, job_dir)
        return cmd

    def submit(self):
        """Submits the job to execution

        Raises
        ------
        QiitaDBOperationNotPermittedError
            If the job is not in 'waiting' or 'in_construction' status
        """
        if self.status not in {'in_construction', 'waiting'}:
            raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                "Can't submit job, not in 'in_construction' or "
                "'waiting' status")
        cmd = self._generate_cmd()
        p = Process(target=_job_submitter, args=(self, cmd))
        p.start()

    def complete(self, success, artifacts_data=None, error=None):
        """Completes the job, either with a success or error status

        Parameters
        ----------
        success : bool
            Whether the job has completed successfully or not
        artifacts_data : dict of dicts
            The generated artifact information, keyed by output name.
            The format of each of the internal dictionaries must be
            {'filepaths': list of (str, str), 'artifact_type': str}
            where `filepaths` contains the list of filepaths and filepath types
            for the artifact and `artifact_type` the type of the artifact
        error : str, optional
            If the job was not successful, the error message

        Raises
        ------
        qiita_db.exceptions.QiitaDBOperationNotPermittedError
            If the job is not in running state
        """
        with qdb.sql_connection.TRN:
            if success:
                if self.status != 'running':
                    # If the job is not running, we only allow to complete it
                    # if it did not success
                    raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                        "Can't complete job: not in a running state")
                if artifacts_data:
                    artifact_ids = []
                    for out_name, a_data in viewitems(artifacts_data):
                        filepaths = a_data['filepaths']
                        atype = a_data['artifact_type']
                        parents = self.input_artifacts
                        params = self.parameters
                        a = qdb.artifact.Artifact.create(
                            filepaths, atype, parents=parents,
                            processing_parameters=params)
                        cmd_out_id = qdb.util.convert_to_id(
                            out_name, "command_output", "name")
                        artifact_ids.append((cmd_out_id, a.id))
                    if artifact_ids:
                        sql = """INSERT INTO
                                    qiita.artifact_output_processing_job
                                    (artifact_id, processing_job_id,
                                     command_output_id)
                                 VALUES (%s, %s, %s)"""
                        sql_params = [[aid, self.id, out_id]
                                      for out_id, aid in artifact_ids]
                        qdb.sql_connection.TRN.add(sql, sql_params, many=True)
                self._set_status('success')
            else:
                self._set_error(error)

    @property
    def log(self):
        """The log entry attached to the job if it failed

        Returns
        -------
        qiita_db.logger.LogEntry or None
            If the status of the job is `error`, returns the LogEntry attached
            to the job
        """
        with qdb.sql_connection.TRN:
            res = None
            if self.status == 'error':
                sql = """SELECT logging_id
                         FROM qiita.processing_job
                         WHERE processing_job_id = %s"""
                qdb.sql_connection.TRN.add(sql, [self.id])
                log_id = qdb.sql_connection.TRN.execute_fetchlast()
                res = qdb.logger.LogEntry(log_id)
        return res

    def _set_error(self, error):
        """Attaches a log entry to the job

        Parameters
        ----------
        error : str
            The error message

        Raises
        ------
        qiita_db.exceptions.QiitaDBOperationNotPermittedError
            If the status of the job is 'success'
        """
        with qdb.sql_connection.TRN:
            if self.status == 'success':
                raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                    "Can only set up the log for jobs whose status is 'error'")

            self._set_status('error')
            log = qdb.logger.LogEntry.create('Runtime', error)

            sql = """UPDATE qiita.processing_job
                     SET logging_id = %s
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [log.id, self.id])
            qdb.sql_connection.TRN.execute()

    @property
    def heartbeat(self):
        """The timestamp of the last heartbeat received from the job

        Returns
        -------
        datetime
            The last heartbeat timestamp
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT heartbeat
                     FROM qiita.processing_job
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    def execute_heartbeat(self):
        """Updates the heartbeat of the job

        In case that the job is in `queued` status, it changes the status to
        `running`.

        Raises
        ------
        QiitaDBOperationNotPermittedError
            If the job is already completed
        """
        with qdb.sql_connection.TRN:
            status = self.status
            if status == 'queued':
                self._set_status('running')
            elif status != 'running':
                raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                    "Can't execute heartbeat on job: already completed")
            sql = """UPDATE qiita.processing_job
                     SET heartbeat = %s
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [datetime.now(), self.id])
            qdb.sql_connection.TRN.execute()

    @property
    def step(self):
        """Returns the current step of the job

        Returns
        -------
        str
            The current step of the job
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT step
                     FROM qiita.processing_job
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @step.setter
    def step(self, value):
        """Sets the current step of the job

        Parameters
        ----------
        value : str
            The new current step of the job

        Raises
        ------
        qiita_db.exceptions.QiitaDBOperationNotPermittedError
            If the status of the job is not 'running'
        """
        with qdb.sql_connection.TRN:
            if self.status != 'running':
                raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                    "Cannot change the step of a job whose status is not "
                    "'running'")
            sql = """UPDATE qiita.processing_job
                     SET step = %s
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [value, self.id])
            qdb.sql_connection.TRN.execute()


class ProcessingWorkflow(qdb.base.QiitaObject):
    """Models a workflow defined by the user

    Parameters
    ----------
    user : qiita_db.user.User
        The user that modeled the workflow
    root : list of qiita_db.processing_job.ProcessingJob
        The first job in the workflow
    """
    _table = "processing_job_workflow"

    @classmethod
    def _common_creation_steps(cls, user, root_jobs, name=None):
        """Executes the common creation steps

        Parameters
        ----------
        user : qiita_db.user.User
            The user creating the workflow
        root_jobs : list of qiita_db.processing_job.ProcessingJob
            The root jobs of the workflow
        name : str, optional
            The name of the workflow. Default: generated from user's name
        """
        with qdb.sql_connection.TRN:
            # Insert the workflow in the processing_job_worflow table
            name = name if name else "%s's workflow" % user.info['name']
            sql = """INSERT INTO qiita.processing_job_workflow (email, name)
                     VALUES (%s, %s)
                     RETURNING processing_job_workflow_id"""
            qdb.sql_connection.TRN.add(sql, [user.email, name])
            w_id = qdb.sql_connection.TRN.execute_fetchlast()
            # Connect the workflow with it's initial set of jobs
            sql = """INSERT INTO qiita.processing_job_workflow_root
                        (processing_job_workflow_id, processing_job_id)
                     VALUES (%s, %s)"""
            sql_args = [[w_id, j.id] for j in root_jobs]
            qdb.sql_connection.TRN.add(sql, sql_args, many=True)
            qdb.sql_connection.TRN.execute()

        return cls(w_id)

    @classmethod
    def from_default_workflow(cls, user, dflt_wf, req_params, name=None):
        """Creates a new processing workflow from a default workflow

        Parameters
        ----------
        user : qiita_db.user.User
            The user creating the workflow
        dflt_wf : qiita_db.software.DefaultWorkflow
            The default workflow
        req_params : dict of {qdb.software.Command: dict of {str: object}}
            The required parameters values for the source commands in the
            workflow, keyed by command. The inner dicts are keyed by
            parameter name.
        name : str, optional
            Name of the workflow. Default: generated from user's name

        Returns
        -------
        qiita_db.processing_job.ProcessingWorkflow
            The newly created workflow
        """
        with qdb.sql_connection.TRN:
            dflt_g = dflt_wf.graph

            # Find the roots of the workflow. That is, the nodes that do not
            # have a parent in the graph (in_degree = 0)
            in_degrees = dflt_g.in_degree()

            # We can potentially access this information from the nodes
            # multiple times, so caching in here
            all_nodes = {n: (n.command, n.parameters)
                         for n in in_degrees}
            roots = {n: (n.command, n.parameters)
                     for n, d in viewitems(in_degrees) if d == 0}

            # Check that we have all the required parameters
            root_cmds = set(c for c, _ in viewvalues(roots))
            if root_cmds != set(req_params):
                error_msg = ['Provided required parameters do not match the '
                             'initial set of commands for the workflow.']
                missing = [c.name for c in root_cmds - set(req_params)]
                if missing:
                    error_msg.append(
                        ' Command(s) "%s" are missing the required parameter '
                        'set.' % ', '.join(missing))
                extra = [c.name for c in set(req_params) - root_cmds]
                if extra:
                    error_msg.append(
                        ' Paramters for command(s) "%s" have been provided, '
                        'but they are not the initial commands for the '
                        'workflow.' % ', '.join(extra))
                raise qdb.exceptions.QiitaDBError(''.join(error_msg))

            # Start creating the root jobs
            node_to_job = {
                n: ProcessingJob.create(
                    user,
                    qdb.software.Parameters.from_default_params(
                        p, req_params[c]))
                for n, (c, p) in viewitems(roots)}
            root_jobs = node_to_job.values()

            # SQL used to create the edges between jobs
            sql = """INSERT INTO qiita.parent_processing_job
                        (parent_id, child_id)
                     VALUES (%s, %s)"""

            # Create the rest of the jobs. These are different form the root
            # jobs because they depend on other jobs to complete in order to be
            # submitted
            for n in nx.topological_sort(dflt_g):
                if n in node_to_job:
                    # We have already seend this node
                    # (because it is a root node)
                    continue

                cmd, dflt_params = all_nodes[n]
                job_req_params = {}
                parent_ids = []

                # Each incoming edge represents an artifact that is generated
                # by the source job of the edge
                for source, dest, data in dflt_g.in_edges(n, data=True):
                    # Retrieve the id of the parent job - it already exists
                    # because we are visiting the nodes in topological order
                    source_id = node_to_job[source].id
                    parent_ids.append(source_id)
                    # Get the connections between the job and the source
                    connections = data['connections'].connections
                    for out, in_param in connections:
                        # We take advantage of the fact the parameters are
                        # stored in JSON to encode the name of the output
                        # artifact from
                        # the previous job
                        job_req_params[in_param] = [source_id, out]

                # At this point we should have all the requried paramters for
                # the current job, so create it
                new_job = ProcessingJob.create(
                    user, qdb.software.Parameters.from_default_params(
                        dflt_params, job_req_params))
                node_to_job[n] = new_job

                # Create the parent-child links in the DB
                sql_args = [[pid, new_job.id] for pid in parent_ids]
                qdb.sql_connection.TRN.add(sql, sql_args, many=True)

            return cls._common_creation_steps(user, root_jobs, name)

    @classmethod
    def from_scratch(cls, user, parameters, name=None):
        """Creates a new processing workflow from scratch

        Parameters
        ----------
        user : qiita_db.user.User
            The user creating the workflow
        parameters : qiita_db.software.Parameters
            The parameters of the first job in the workflow
        name : str, optional
            Name of the workflow. Default: generated from user's name

        Returns
        -------
        qiita_db.processing_job.ProcessingWorkflow
            The newly created workflow
        """
        job = ProcessingJob.create(user, parameters)
        return cls._common_creation_steps(user, [job], name)

    @property
    def name(self):
        """"The name of the workflow

        Returns
        -------
        str
            The name of the workflow
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT name
                     FROM qiita.processing_job_workflow
                     WHERE processing_job_workflow_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    @property
    def user(self):
        """The user that created the workflow

        Returns
        -------
        qdb.user.User
            The user that created the workflow
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT email
                     FROM qiita.processing_job_workflow
                     WHERE processing_job_workflow_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            email = qdb.sql_connection.TRN.execute_fetchlast()
            return qdb.user.User(email)

    @property
    def graph(self):
        """Returns the graph of jobs that represent the workflow

        Returns
        -------
        networkx.DiGraph
            The graph representing the workflow
        """
        g = nx.DiGraph()
        with qdb.sql_connection.TRN:
            # Retrieve all graph workflow nodes
            sql = """SELECT parent_id, child_id
                     FROM qiita.get_processing_workflow_edges(%s)"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            edges = qdb.sql_connection.TRN.execute_fetchindex()
            if edges:
                nodes = {jid: ProcessingJob(jid)
                         for jid in set(chain.from_iterable(edges))}
                g.add_nodes_from(nodes.values())
                edges = [(nodes[s], nodes[d]) for s, d in edges]
                g.add_edges_from(edges)
            else:
                # It is possible that there are no edges because we are still
                # building the workflow. In that case, just return a graph
                # with only the nodes
                sql = """SELECT processing_job_id
                         FROM qiita.processing_job_workflow_root
                         WHERE processing_job_workflow_id = %s"""
                qdb.sql_connection.TRN.add(sql, [self.id])
                nodes = [
                    ProcessingJob(jid)
                    for jid in qdb.sql_connection.TRN.execute_fetchflatten()]
                g.add_nodes_from(nodes)
        return g

    def _raise_if_not_in_construction(self):
        """Raises an error if the workflow is not in construction

        Raises
        ------
        qiita_db.exceptions.QiitaDBOperationNotPermittedError
            If the workflow is not in construction
        """
        with qdb.sql_connection.TRN:
            # To know if the workflow is in construction or not it suffices
            # to look at the status of the root jobs
            sql = """SELECT DISTINCT processing_job_status
                     FROM qiita.processing_job_workflow_root
                        JOIN qiita.processing_job USING (processing_job_id)
                        JOIN qiita.processing_job_status
                            USING (processing_job_status_id)
                     WHERE processing_job_workflow_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            res = qdb.sql_connection.TRN.execute_fetchflatten()
            if len(res) != 1 or res[0] != 'in_construction':
                # The workflow is no longer in construction, raise an error
                raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                    "Workflow not in construction")

    def add(self, connections, dflt_params, req_params=None, opt_params=None):
        """Adds a new job to the workflow

        Parameters
        ----------
        connections : dict of {qiita_db.processing_job.ProcessingJob:
                               {str: str}}
            Dictionary keyed by the jobs in which the new job depends on,
            and values is a dict mapping between source outputs and new job
            inputs
        dflt_params : qiita_db.software.DefaultParameters
            The DefaultParameters object used
        req_params : dict of {str: object}, optional
            Any extra required parameter values, keyed by parameter name.
            Default: None, all the requried parameters are provided through
            the `connections` dictionary
        opt_params : dict of {str: object}, optional
            The optional parameters to change from the default set, keyed by
            parameter name. Default: None, use the values in `dflt_params`

        Raises
        ------
        qiita_db.exceptions.QiitaDBOperationNotPermittedError
            If the workflow is not in construction
        """
        with qdb.sql_connection.TRN:
            self._raise_if_not_in_construction()

            req_params = req_params if req_params else {}
            # Loop through all the connections to add the relevant parameters
            for source, mapping in viewitems(connections):
                source_id = source.id
                for out, in_param in viewitems(mapping):
                    req_params[in_param] = [source_id, out]

            new_job = ProcessingJob.create(
                self.user, qdb.software.Parameters.from_default_params(
                    dflt_params, req_params, opt_params=opt_params))

            # SQL used to create the edges between jobs
            sql = """INSERT INTO qiita.parent_processing_job
                        (parent_id, child_id)
                     VALUES (%s, %s)"""
            sql_args = [[s.id, new_job.id] for s in connections]
            qdb.sql_connection.TRN.add(sql, sql_args, many=True)
            qdb.sql_connection.TRN.execute()

    def remove(self, job):
        """Removes a given job from the workflow

        Parameters
        ----------
        job : qiita_db.processing_job.ProcessingJob
            The job to be removed

        Raises
        ------
        qiita_db.exceptions.QiitaDBOperationNotPermittedError
            If the workflow is not in construction
            If the job to be removed has children
        """
        with qdb.sql_connection.TRN:
            self._raise_if_not_in_construction()

            # Check if the given job has children
            sql = """SELECT EXISTS(SELECT *
                                   FROM qiita.parent_processing_job
                                   WHERE parent_id=%s)"""
            qdb.sql_connection.TRN.add(sql, [job.id])
            if qdb.sql_connection.TRN.execute_fetchlast():
                raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                    "Can't remove job '%s': it has children" % job.id)

            # Remove any edges (it can only appear as a child)
            sql = """DELETE FROM qiita.parent_processing_job
                     WHERE child_id = %s"""
            qdb.sql_connection.TRN.add(sql, [job.id])

            # Remove as root job
            sql = """DELETE FROM qiita.processing_job_workflow_root
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [job.id])

            # Remove the job
            sql = """DELETE FROM qiita.processing_job
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [job.id])

            qdb.sql_connection.TRN.execute()

    def submit(self):
        """"""
