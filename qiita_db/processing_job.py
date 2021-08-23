# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

import networkx as nx
import qiita_db as qdb
import pandas as pd

from collections import defaultdict, Iterable
from datetime import datetime
from itertools import chain
from json import dumps, loads
from multiprocessing import Process, Queue, Event
from re import search, findall
from subprocess import Popen, PIPE
from time import sleep, time
from uuid import UUID
from os.path import join
from threading import Thread
from humanize import naturalsize

from qiita_core.exceptions import IncompetentQiitaDeveloperError
from qiita_core.qiita_settings import qiita_config
from qiita_db.util import create_nested_path


class Watcher(Process):
    # TODO: Qiita will need a proper mapping of these states to Qiita states
    # Currently, these strings are being inserted directly into Qiita's status
    # table. Qiita will be unfamiliar with many of these. We will need at least
    # one additional job type for 'Held': A job waiting for another to complete
    # before it can run.
    #
    # Note that the main Qiita script instantiates an object of this class in
    # a separate thread, so it can periodically update the database w/metadata
    # from Watcher's queue. Qiita's script also calls qdb.complete() so there
    # are no circular references. TODO: replace w/a REST call.

    # valid Qiita states:
    #             The current status of the job, one of {'queued', 'running',
    #             'success', 'error', 'in_construction', 'waiting'}

    # TODO: what to map in_construction to?
    job_state_map = {'C': 'completed', 'E': 'exiting', 'H': 'held',
                     'Q': 'queued', 'R': 'running', 'T': 'moving',
                     'W': 'waiting', 'S': 'suspended'}

    # TODO: moving, waiting, and suspended have been mapped to
    # 'running' in Qiita, as 'waiting' in Qiita connotes that the
    # main job itself has completed, and is waiting on validator
    # jobs to finish, etc. Revisit
    torque_to_qiita_state_map = {'completed': 'completed',
                                 'held': 'queued',
                                 'queued': 'queued',
                                 'exiting': 'running',
                                 'running': 'running',
                                 'moving': 'running',
                                 'waiting': 'running',
                                 'suspended': 'running',
                                 'DROPPED': 'error'}

    def __init__(self):
        super(Watcher, self).__init__()

        # set self.owner to qiita, or whomever owns processes we need to watch.
        self.owner = qiita_config.trq_owner

        # Torque is set to drop jobs from its queue 60 seconds after
        # completion, by default. Setting a polling value less than
        # that allows for multiple chances to catch the exit status
        # before it disappears.
        self.polling_value = qiita_config.trq_poll_val

        # the cross-process method by which to communicate across
        # process boundaries. Note that when Watcher object runs,
        # another process will get created, and receive a copy of
        # the Watcher object. At this point, these self.* variables
        # become local to each process. Hence, the main process
        # can't see self.processes for example; theirs will just
        # be empty.
        self.queue = Queue()
        self.processes = {}

        # the cross-process sentinel value to shutdown Watcher
        self.event = Event()

    def _element_extract(self, snippet, list_of_elements,
                         list_of_optional_elements):
        results = {}
        missing_elements = []

        for element in list_of_elements:
            value = search('<%s>(.*?)</%s>' % (element, element), snippet)
            if value:
                results[element] = value.group(1)
            else:
                missing_elements.append(element)

        if missing_elements:
            raise AssertionError("The following elements were not found: %s"
                                 % ', '.join(missing_elements))

        for element in list_of_optional_elements:
            value = search('<%s>(.*?)</%s>' % (element, element), snippet)
            if value:
                results[element] = value.group(1)

        return results

    def _process_dependent_jobs(self, results):
        # when a job has its status changed, check to see if the job completed
        # with an error. If so, check to see if it had any jobs that were being
        # 'held' on this job's successful completion. If we are maintaining
        # state on any of these jobs, mark them as 'DROPPED', because they will
        # no longer appear in qstat output.
        if results['job_state'] == 'completed':
            if results['exit_status'] == '0':
                return

            if 'depend' in results:
                tmp = results['depend'].split(':')
                if tmp[0] == 'beforeok':
                    tmp.pop(0)
                    for child_job_id in tmp:
                        # jobs in 'beforeok' are labeled with the complete
                        # job id and what looks to be the server name doing
                        # the work. For now, simply remove the
                        # '@host.domain.org' (server) component.
                        child_job_id = child_job_id.split('@')[0]
                        self.processes[child_job_id]['job_state'] = 'DROPPED'
                        self.queue.put(self.processes[child_job_id])

    def run(self):
        # check to see if qstat is available. If not, exit immediately.
        proc = Popen("qstat -x", shell=True, stdout=PIPE, stderr=PIPE)
        proc.wait()
        if proc.returncode != 0:
            # inform any process expecting data from Watcher
            self.queue.put('QUIT')
            self.event.set()

        while not self.event.is_set():
            proc = Popen("qstat -x", shell=True, stdout=PIPE, stderr=PIPE)
            stdout, stderr = proc.communicate()
            if proc.returncode == 0:
                # qstat returned successfully with metadata on processes
                # break up metadata into individual <Job></Job> elements
                # for processing.
                m = findall('<Job>(.*?)</Job>', stdout.decode('ascii'))
                for item in m:
                    # filter out jobs that don't belong to owner
                    if search('<Job_Owner>%s</Job_Owner>' % self.owner, item):
                        # extract the metadata we want.
                        # if a job has completed, an exit_status element will
                        # be present. We also want that.
                        results = self._element_extract(item, ['Job_Id',
                                                               'Job_Name',
                                                               'job_state'],
                                                              ['depend'])
                        tmp = Watcher.job_state_map[results['job_state']]
                        results['job_state'] = tmp
                        if results['job_state'] == 'completed':
                            results2 = self._element_extract(item,
                                                             ['exit_status'],
                                                             [])
                            results['exit_status'] = results2['exit_status']

                        # determine if anything has changed since last poll
                        if results['Job_Id'] in self.processes:
                            if self.processes[results['Job_Id']] != results:
                                # metadata for existing job has changed
                                self.processes[results['Job_Id']] = results
                                self.queue.put(results)
                                self._process_dependent_jobs(results)
                        else:
                            # metadata for new job inserted
                            self.processes[results['Job_Id']] = results
                            self.queue.put(results)
            else:
                self.queue.put('QUIT')
                self.event.set()
                # don't join(), since we are exiting from the main loop

            sleep(self.polling_value)

    def stop(self):
        # 'poison pill' to thread/process
        self.queue.put('QUIT')
        # setting self.event is a safe way of communicating a boolean
        # value across processes and threads.
        # when this event is 'set' by the main line of execution in Qiita,
        # (or in any other process if need be), Watcher's run loop will
        # stop and the Watcher process will exit.
        self.event.set()
        # Here, it is assumed that we are running this from the main
        # context. By joining(), we're waiting for the Watcher process to
        # end before returning from this method.
        self.join()


def launch_local(env_script, start_script, url, job_id, job_dir):

    # launch_local() differs from launch_torque(), as no Watcher() is used.
    # each launch_local() process will execute the cmd as a child process,
    # wait, and update the database once cmd has completed.
    #
    # As processes are lighter weight than jobs, this should be fine.
    # This is how the current job model works locally.
    cmd = [start_script, url, job_id, job_dir]

    # When Popen() executes, the shell is not in interactive mode,
    # so it is not sourcing any of the bash configuration files
    # We need to source it so the env_script are available
    cmd = "bash -c '%s; %s'" % (env_script, ' '.join(cmd))

    # Popen() may also need universal_newlines=True
    proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)

    # Communicate pulls all stdout/stderr from the PIPEs
    # This call waits until cmd is done
    stdout, stderr = proc.communicate()

    # proc.returncode will be equal to None if the process hasn't finished
    # yet. If cmd was terminated by a SIGNAL, it will be a negative value.
    # (*nix platforms only)
    error = None

    if proc.returncode != 0:
        error = "error from launch_local when launching cmd='%s'" % cmd
        error = "%s\n%s\n%s" % (error, stdout, stderr)

        # Forcing the creation of a new connection
        qdb.sql_connection.create_new_transaction()
        ProcessingJob(job_id).complete(False, error=error)


def launch_torque(env_script, start_script, url, job_id, job_dir,
                  dependent_job_id, resource_params):

    # note that job_id is Qiita's UUID, not a Torque job ID
    cmd = [start_script, url, job_id, job_dir]

    # generating file contents to be used with qsub
    lines = []

    # TODO: is PBS_JOBID is being set correctly?
    lines.append("echo $PBS_JOBID")

    # TODO: revisit below
    lines.append("source ~/.bash_profile")
    lines.append(env_script)
    lines.append(' '.join(cmd))

    # writing the file to be used with qsub
    create_nested_path(job_dir)

    fp = join(job_dir, '%s.txt' % job_id)

    with open(fp, 'w') as torque_job_file:
        torque_job_file.write("\n".join(lines))

    qsub_cmd = ['qsub']

    if dependent_job_id:
        # note that a dependent job should be submitted before the
        # 'parent' job ends, most likely. Torque doesn't keep job state
        # around forever, and creating a dependency on a job already
        # completed has not been tested.
        qsub_cmd.append("-W")
        qsub_cmd.append("depend=afterok:%s" % dependent_job_id)

    qsub_cmd.append(resource_params)
    qsub_cmd.append(fp)
    qsub_cmd.append("-o")
    qsub_cmd.append("%s/qsub-output.txt" % job_dir)
    qsub_cmd.append("-e")
    qsub_cmd.append("%s/qsub-error.txt" % job_dir)
    # TODO: revisit epilogue
    qsub_cmd.append("-l")
    qsub_cmd.append("epilogue=/home/qiita/qiita-epilogue.sh")

    # Popen() may also need universal_newlines=True
    # may also need stdout = stdout.decode("utf-8").rstrip()
    qsub_cmd = ' '.join(qsub_cmd)

    # Qopen is a wrapper for Popen() that allows us to wait on a qsub
    # call, but return if the qsub command is not returning after a
    # prolonged period of time.
    q = Qopen(qsub_cmd)
    q.start()

    # wait for qsub_cmd to finish, but not longer than the number of
    # seconds specified below.
    init_time = time()
    q.join(5)
    total_time = time() - init_time
    # for internal use, logging if the time is larger than 2 seconds
    if total_time > 2:
        qdb.logger.LogEntry.create('Runtime', 'qsub return time', info={
            'time_in_seconds': str(total_time)})

    # if q.returncode is None, it's because qsub did not return.
    if q.returncode is None:
        e = "Error Torque configuration information incorrect: %s" % qsub_cmd
        raise IncompetentQiitaDeveloperError(e)

    # q.returncode in this case means qsub successfully pushed the job
    # onto Torque's queue.
    if q.returncode != 0:
        raise AssertionError("Error Torque could not launch %s (%d)" %
                             (qsub_cmd, q.returncode))

    torque_job_id = q.stdout.decode('ascii').strip('\n')

    return torque_job_id


class Qopen(Thread):
    def __init__(self, cmd):
        super(Qopen, self).__init__()
        self.cmd = cmd
        self.stdout = None
        self.stderr = None
        self.returncode = None

    def run(self):
        proc = Popen(self.cmd, shell=True, stdout=PIPE, stderr=PIPE)
        self.stdout, self.stderr = proc.communicate()
        self.returncode = proc.returncode


def _system_call(cmd):
    """Execute the command `cmd`

    Parameters
    ----------
    cmd : str
        The string containing the command to be run.

    Returns
    -------
    tuple of (str, str, int)
        The standard output, standard error and exist status of the
        executed command

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
    _launch_map = {'qiita-plugin-launcher':
                   {'function': launch_local,
                    'execute_in_process': False},
                   'qiita-plugin-launcher-qsub':
                   {'function': launch_torque,
                    'execute_in_process': True}}

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
    def by_external_id(cls, external_id):
        """Return Qiita Job UUID associated with external_id

        Parameters
        ----------
        external_id : str
            An external id (e.g. Torque Job ID)

        Returns
        -------
        str
            Qiita Job UUID, if found, otherwise None
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT processing_job_id FROM qiita.processing_job
                     WHERE external_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [external_id])
            return cls(qdb.sql_connection.TRN.execute_fetchlast())

    def get_resource_allocation_info(self):
        """Return resource allocation defined for this job. For
        external computational resources only.

        Returns
        -------
        str
            A resource allocation string useful to the external resource
        """
        with qdb.sql_connection.TRN:
            if self.command.name == 'complete_job':
                jtype = 'COMPLETE_JOBS_RESOURCE_PARAM'
                v = loads(self.parameters.values['payload'])
                # assume an empty string for name is preferable to None
                name = ''
                if v['artifacts'] is not None:
                    an_element = list(v['artifacts'].keys())[0]
                    name = v['artifacts'][an_element]['artifact_type']
            elif self.command.name == 'release_validators':
                jtype = 'RELEASE_VALIDATORS_RESOURCE_PARAM'
                tmp = ProcessingJob(self.parameters.values['job'])
                name = tmp.parameters.command.name
            elif self.command.name == 'Validate':
                jtype = 'VALIDATOR'
                name = self.parameters.values['artifact_type']
            elif self.id == 'register':
                jtype = 'REGISTER'
                name = 'REGISTER'
            else:
                # assume anything else is a command
                jtype = 'RESOURCE_PARAMS_COMMAND'
                name = self.command.name

            # first, query for resources matching name and type
            sql = """SELECT allocation FROM
                     qiita.processing_job_resource_allocation
                     WHERE name = %s and job_type = %s"""
            qdb.sql_connection.TRN.add(sql, [name, jtype])

            result = qdb.sql_connection.TRN.execute_fetchflatten()

            # if no matches for both type and name were found, query the
            # 'default' value for the type

            if not result:
                sql = """SELECT allocation FROM
                         qiita.processing_job_resource_allocation WHERE
                         name = %s and job_type = %s"""
                qdb.sql_connection.TRN.add(sql, ['default', jtype])

                result = qdb.sql_connection.TRN.execute_fetchflatten()
                if not result:
                    AssertionError(
                        "Could not match %s to a resource allocation!" % name)

            allocation = result[0]

            if ('{samples}' in allocation or '{columns}' in allocation or
                    '{input_size}' in allocation):
                samples, columns, input_size = self.shape
                parts = []
                for part in allocation.split(' '):
                    if ('{samples}' in part or '{columns}' in part or
                            '{input_size}' in part):
                        variable, value = part.split('=')
                        error_msg = ('Obvious incorrect allocation. Please '
                                     'contact qiita.help@gmail.com')
                        # to make sure that the formula is correct and avoid
                        # possible issues with conversions, we will check that
                        # all the variables {samples}/{columns}/{input_size}
                        # present in the formula are not None, if any is None
                        # we will set the job's error (will stop it) and the
                        # message is gonna be shown to the user within the job
                        if (('{samples}' in value and samples is None) or
                                ('{columns}' in value and columns is None) or
                                ('{input_size}' in value and input_size is
                                 None)):
                            self._set_error(error_msg)
                            return 'Not valid'

                        try:
                            # if eval has something that can't be processed
                            # it will raise a NameError
                            mem = eval(value.format(
                                samples=samples, columns=columns,
                                input_size=input_size))
                        except NameError:
                            self._set_error(error_msg)
                            return 'Not valid'
                        else:
                            if mem <= 0:
                                self._set_error(error_msg)
                                return 'Not valid'
                            value = naturalsize(mem, gnu=True, format='%.0f')
                            part = '%s=%s' % (variable, value)

                    parts.append(part)

                allocation = ' '.join(parts)

            return allocation

    @classmethod
    def create(cls, user, parameters, force=False):
        """Creates a new job in the system

        Parameters
        ----------
        user : qiita_db.user.User
            The user executing the job
        parameters : qiita_db.software.Parameters
            The parameters of the job being executed
        force : bool
            Force creation on duplicated parameters

        Returns
        -------
        qiita_db.processing_job.ProcessingJob
            The newly created job

        Notes
        -----
        If force is True the job is going to be created even if another job
        exists with the same parameters
        """
        TTRN = qdb.sql_connection.TRN
        with TTRN:
            command = parameters.command

            # check if a job with the same parameters already exists
            sql = """SELECT processing_job_id, email, processing_job_status,
                        COUNT(aopj.artifact_id)
                     FROM qiita.processing_job
                     LEFT JOIN qiita.processing_job_status
                        USING (processing_job_status_id)
                     LEFT JOIN qiita.artifact_output_processing_job aopj
                        USING (processing_job_id)
                     WHERE command_id = %s AND processing_job_status IN (
                        'success', 'waiting', 'running', 'in_construction') {0}
                     GROUP BY processing_job_id, email,
                        processing_job_status"""

            # we need to use ILIKE because of booleans as they can be
            # false or False
            params = []
            for k, v in parameters.values.items():
                # this is necessary in case we have an Iterable as a value
                # but that is string
                if isinstance(v, Iterable) and not isinstance(v, str):
                    for vv in v:
                        params.extend([k, str(vv)])
                else:
                    params.extend([k, str(v)])

            if params:
                # divided by 2 as we have key-value pairs
                len_params = int(len(params)/2)
                sql = sql.format(' AND ' + ' AND '.join(
                    ["command_parameters->>%s ILIKE %s"] * len_params))
                params = [command.id] + params
                TTRN.add(sql, params)
            else:
                # the sql variable expects the list of parameters but if there
                # is no param we need to replace the {0} with an empty string
                TTRN.add(sql.format(""), [command.id])

            # checking that if the job status is success, it has children
            # [2] status, [3] children count
            existing_jobs = [r for r in TTRN.execute_fetchindex()
                             if r[2] != 'success' or r[3] > 0]
            if existing_jobs and not force:
                raise ValueError(
                    'Cannot create job because the parameters are the same as '
                    'jobs that are queued, running or already have '
                    'succeeded:\n%s' % '\n'.join(
                        ["%s: %s" % (jid, status)
                         for jid, _, status, _ in existing_jobs]))

            sql = """INSERT INTO qiita.processing_job
                        (email, command_id, command_parameters,
                         processing_job_status_id)
                     VALUES (%s, %s, %s, %s)
                     RETURNING processing_job_id"""
            status = qdb.util.convert_to_id(
                "in_construction", "processing_job_status")
            sql_args = [user.id, command.id,
                        parameters.dump(), status]
            TTRN.add(sql, sql_args)
            job_id = TTRN.execute_fetchlast()

            # Link the job with the input artifacts
            sql = """INSERT INTO qiita.artifact_processing_job
                        (artifact_id, processing_job_id)
                     VALUES (%s, %s)"""
            pending = defaultdict(dict)
            for pname, vals in command.parameters.items():
                if vals[0] == 'artifact':
                    artifact_info = parameters.values[pname]
                    # If the artifact_info is a list, then the artifact
                    # still doesn't exists because the current job is part
                    # of a workflow, so we can't link
                    if not isinstance(artifact_info, list):
                        TTRN.add(sql, [artifact_info, job_id])
                    else:
                        pending[artifact_info[0]][pname] = artifact_info[1]
                elif pname == 'artifact':
                    TTRN.add(sql, [parameters.values[pname], job_id])

            if pending:
                sql = """UPDATE qiita.processing_job
                         SET pending = %s
                         WHERE processing_job_id = %s"""
                TTRN.add(sql, [dumps(pending), job_id])

            TTRN.execute()

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
        str
            The current status of the job, one of {'queued', 'running',
            'success', 'error', 'in_construction', 'waiting'}

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

            if (new_status in ('running', 'success', 'error') and
                    not self.command.analysis_only and
                    self.user.level == 'admin'):
                subject = ('Job status change: %s (%s)' % (
                    self.command.name, self.id))
                message = ('New status: %s' % (new_status))
                qdb.util.send_email(self.user.email, subject, message)
            sql = """UPDATE qiita.processing_job
                     SET processing_job_status_id = %s
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [new_status, self.id])
            qdb.sql_connection.TRN.execute()

    @property
    def external_id(self):
        """Retrieves the external id"""
        with qdb.sql_connection.TRN:
            sql = """SELECT external_job_id
                     FROM qiita.processing_job
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            result = qdb.sql_connection.TRN.execute_fetchlast()
            if result is None:
                result = 'Not Available'
            return result

    @external_id.setter
    def external_id(self, value):
        """Sets the external job id of the job

        Parameters
        ----------
        value : str, {'queued', 'running', 'success', 'error',
                      'in_construction', 'waiting'}
            The job's new status

        Raises
        ------
        qiita_db.exceptions.QiitaDBStatusError
            - If the current status of the job is 'success'
            - If the current status of the job is 'running' and `value` is
            'queued'
        """
        sql = """UPDATE qiita.processing_job
                 SET external_job_id = %s
                 WHERE processing_job_id = %s"""
        qdb.sql_connection.perform_as_transaction(sql, [value, self.id])

    @property
    def release_validator_job(self):
        """Retrieves the release validator job

        Returns
        -------
        qiita_db.processing_job.ProcessingJob or None
            The release validator job of this job
        """
        rvalidator = None
        with qdb.sql_connection.TRN:
            sql = """SELECT processing_job_id
                     FROM qiita.processing_job
                     WHERE command_id in (
                         SELECT command_id
                         FROM qiita.software_command
                         WHERE name = 'release_validators')
                             AND command_parameters->>'job' = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            results = qdb.sql_connection.TRN.execute_fetchflatten()
            if results:
                rvalidator = ProcessingJob(results[0])

        return rvalidator

    def submit(self, parent_job_id=None, dependent_jobs_list=None):
        """Submits the job to execution
        This method has the ability to submit itself, as well as a list of
        other ProcessingJob objects. If a list of ProcessingJob objects is
        supplied, they will be submitted conditionally on the successful
        execution of this object.

        Users of this method don't need to set parent_job_id. It is used
        internally by submit() for subsequent submit() calls for dependents.

        Raises
        ------
        QiitaDBOperationNotPermittedError
            If the job is not in 'waiting' or 'in_construction' status
        """
        with qdb.sql_connection.TRN:
            status = self.status
            if status not in {'in_construction', 'waiting'}:
                raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                    "Can't submit job, not in 'in_construction' or "
                    "'waiting' status. Current status: %s" % status)
            self._set_status('queued')
            # At this point we are going to involve other processes. We need
            # to commit the changes to the DB or the other processes will not
            # see these changes
            qdb.sql_connection.TRN.commit()

        job_dir = join(qdb.util.get_work_base_dir(), self.id)
        software = self.command.software
        plugin_start_script = software.start_script
        plugin_env_script = software.environment_script

        # Appending the portal URL so the job requests the information from the
        # portal server that submitted the job
        url = "%s%s" % (qiita_config.base_url, qiita_config.portal_dir)

        # if the word ENVIRONMENT is in the plugin_env_script we have a special
        # case where we are going to execute some command and then wait for the
        # plugin to return their own id (first implemented for
        # fast-bowtie2+woltka)
        if 'ENVIRONMENT' in plugin_env_script:
            # the job has to be in running state so the plugin can change its`
            # status
            with qdb.sql_connection.TRN:
                self._set_status('running')
                qdb.sql_connection.TRN.commit()

            create_nested_path(job_dir)
            cmd = (f'{plugin_env_script}; {plugin_start_script} '
                   f'{url} {self.id} {job_dir}')
            stdout, stderr, return_value = _system_call(cmd)
            if return_value != 0 or stderr != '':
                self._set_error(stderr)
            job_id = stdout
        # note that dependent jobs, such as m validator jobs marshalled into
        # n 'queues' require the job_id returned by an external scheduler such
        # as Torque's MOAB, rather than a job name that can be defined within
        # Qiita. Hence, this method must be able to handle the case where a job
        # requires metadata from a late-defined and time-sensitive source.
        elif qiita_config.plugin_launcher in ProcessingJob._launch_map:
            launcher = ProcessingJob._launch_map[qiita_config.plugin_launcher]
            if launcher['execute_in_process']:
                # run this launcher function within this process.
                # usually this is done if the launcher spawns other processes
                # before returning immediately, usually with a job ID that can
                # be used to monitor the job's progress.

                resource_params = self.get_resource_allocation_info()

                # note that parent_job_id is being passed transparently from
                # submit declaration to the launcher.
                # TODO: In proc launches should throw exceptions, that are
                # handled by this code. Out of proc launches will need to
                # handle exceptions by catching them and returning an error
                # code.
                job_id = launcher['function'](plugin_env_script,
                                              plugin_start_script,
                                              url,
                                              self.id,
                                              job_dir,
                                              parent_job_id, resource_params)

                if dependent_jobs_list:
                    # a dependent_jobs_list will always have at least one
                    # job
                    next_job = dependent_jobs_list.pop(0)

                    if not dependent_jobs_list:
                        # dependent_jobs_list is now empty
                        dependent_jobs_list = None

                    # The idea here is that a list of jobs is considered a
                    # chain. Each job in the chain is submitted with the job
                    # id of job submitted before it; a job will only run if
                    # 'parent_job' ran successfully. Each iteration of submit()
                    # launches a job, pulls the next job from the list, and
                    # submits it. The remainder of the list is also passed to
                    # continue the process.
                    next_job.submit(parent_job_id=job_id,
                                    dependent_jobs_list=dependent_jobs_list)

            elif not launcher['execute_in_process']:
                # run this launcher function as a new process.
                # usually this is done if the launcher performs work that takes
                # an especially long time, or waits for children who perform
                # such work.
                p = Process(target=launcher['function'],
                            args=(plugin_env_script,
                                  plugin_start_script,
                                  url,
                                  self.id,
                                  job_dir))

                p.start()

                job_id = p.pid

                if dependent_jobs_list:
                    # for now, treat dependents as independent when
                    # running locally. This means they will not be
                    # organized into n 'queues' or 'chains', and
                    # will all run simultaneously.
                    for dependent in dependent_jobs_list:
                        p = Process(target=launcher['function'],
                                    args=(plugin_env_script,
                                          plugin_start_script,
                                          url,
                                          self.id,
                                          job_dir))
                        p.start()
            else:
                error = ("execute_in_process must be defined",
                         "as either true or false")
                raise AssertionError(error)
        else:
            error = "plugin_launcher should be one of two values for now"
            raise AssertionError(error)

        # note that at this point, self.id is Qiita's UUID for a Qiita
        # job. job_id at this point is an external ID (e.g. Torque Job
        # ID). Record the mapping between job_id and self.id using
        # external_id.
        if job_id is not None:
            self.external_id = job_id

    def release(self):
        """Releases the job from the waiting status and creates the artifact

        Returns
        -------
        dict of {int: int}
            The mapping between the job output and the artifact
        """
        with qdb.sql_connection.TRN:
            if self.command.software.type != 'artifact definition':
                raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                    "Only artifact definition jobs can be released")

            # Retrieve the artifact information from the DB
            sql = """SELECT artifact_info
                     FROM qiita.processing_job_validator
                     WHERE validator_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            a_info = qdb.sql_connection.TRN.execute_fetchlast()

            provenance = loads(self.parameters.values['provenance'])
            job = ProcessingJob(provenance['job'])
            if 'data_type' in a_info:
                # This job is resulting from a private job
                parents = None
                params = None
                cmd_out_id = None
                name = None
                data_type = a_info['data_type']
                analysis = qdb.analysis.Analysis(
                    job.parameters.values['analysis'])
                a_info = a_info['artifact_data']
            else:
                # This job is resulting from a plugin job
                parents = job.input_artifacts
                params = job.parameters
                cmd_out_id = provenance['cmd_out_id']
                name = provenance['name']
                analysis = None
                data_type = None

            # Create the artifact
            atype = a_info['artifact_type']
            filepaths = a_info['filepaths']
            a = qdb.artifact.Artifact.create(
                filepaths, atype, parents=parents,
                processing_parameters=params,
                analysis=analysis, data_type=data_type, name=name)

            self._set_status('success')

            mapping = {}
            if cmd_out_id is not None:
                mapping = {cmd_out_id: a.id}

            return mapping

    def release_validators(self):
        """Allows all the validator job spawned by this job to complete"""
        if self.command.software.type not in ('artifact transformation',
                                              'private'):
            raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                "Only artifact transformation and private jobs can "
                "release validators")

        # Check if all the validators are completed. Validator jobs can be
        # in two states when completed: 'waiting' in case of success
        # or 'error' otherwise

        validator_ids = ['%s [%s]' % (j.id, j.external_id)
                         for j in self.validator_jobs
                         if j.status not in ['waiting', 'error']]

        # Active polling - wait until all validator jobs are completed
        # TODO: As soon as we see one errored validator, we should kill
        # the other jobs and exit early. Don't wait for all of the jobs
        # to complete.
        while validator_ids:
            jids = ', '.join(validator_ids)
            self.step = ("Validating outputs (%d remaining) via "
                         "job(s) %s" % (len(validator_ids), jids))
            sleep(10)
            validator_ids = ['%s [%s]' % (j.id, j.external_id)
                             for j in self.validator_jobs
                             if j.status not in ['waiting', 'error']]

        # Check if any of the validators errored
        errored = [j for j in self.validator_jobs
                   if j.status == 'error']
        if errored:
            # At least one of the validators failed, Set the rest of the
            # validators and the current job as failed
            waiting = [j.id for j in self.validator_jobs
                       if j.status == 'waiting']

            common_error = "\n".join(
                ["Validator %s error message: %s" % (j.id, j.log.msg)
                 for j in errored])

            val_error = "%d sister validator jobs failed: %s" % (
                len(errored), common_error)
            for j in waiting:
                ProcessingJob(j)._set_error(val_error)

            self._set_error('%d validator jobs failed: %s'
                            % (len(errored), common_error))
        else:
            mapping = {}
            # Loop through all validator jobs and release them, allowing
            # to create the artifacts. Note that if any artifact creation
            # fails, the rollback operation will make sure that the
            # previously created artifacts are not in there
            for vjob in self.validator_jobs:
                mapping.update(vjob.release())

            if mapping:
                sql = """INSERT INTO
                            qiita.artifact_output_processing_job
                            (artifact_id, processing_job_id,
                            command_output_id)
                         VALUES (%s, %s, %s)"""
                sql_args = [[aid, self.id, outid]
                            for outid, aid in mapping.items()]
                with qdb.sql_connection.TRN:
                    qdb.sql_connection.TRN.add(sql, sql_args, many=True)
                self._update_and_launch_children(mapping)
            self._set_status('success')

    def _complete_artifact_definition(self, artifact_data):
        """"Performs the needed steps to complete an artifact definition job

        In order to complete an artifact definition job we need to create
        the artifact, and then start all the jobs that were waiting for this
        artifact to be created. Note that each artifact definition job creates
        one and only one artifact.

        Parameters
        ----------
        artifact_data : {'filepaths': list of (str, str), 'artifact_type': str}
            Dict with the artifact information. `filepaths` contains the list
            of filepaths and filepath types for the artifact and
            `artifact_type` the type of the artifact

        Notes
        -----
        The `provenance` in the job.parameters can contain a `direct_creation`
        flag to avoid having to wait for the complete job to create a new
        artifact, which is normally ran during regular processing. Skipping is
        fine because we are adding an artifact to an existing job outside of
        regular processing
        """
        with qdb.sql_connection.TRN:
            atype = artifact_data['artifact_type']
            filepaths = artifact_data['filepaths']
            # We need to differentiate if this artifact is the
            # result of a previous job or uploading
            job_params = self.parameters.values
            if job_params['provenance'] is not None:
                # The artifact is a result from a previous job
                provenance = loads(job_params['provenance'])
                if provenance.get('direct_creation', False):
                    original_job = ProcessingJob(provenance['job'])
                    artifact = qdb.artifact.Artifact.create(
                        filepaths, atype,
                        parents=original_job.input_artifacts,
                        processing_parameters=original_job.parameters,
                        analysis=job_params['analysis'],
                        name=job_params['name'])

                    sql = """
                        INSERT INTO qiita.artifact_output_processing_job
                            (artifact_id, processing_job_id,
                             command_output_id)
                         VALUES (%s, %s, %s)"""
                    qdb.sql_connection.TRN.add(
                        sql, [artifact.id, original_job.id,
                              provenance['cmd_out_id']])
                    qdb.sql_connection.TRN.execute()

                    self._set_status('success')
                else:
                    if provenance.get('data_type') is not None:
                        artifact_data = {'data_type': provenance['data_type'],
                                         'artifact_data': artifact_data}

                    sql = """UPDATE qiita.processing_job_validator
                             SET artifact_info = %s
                             WHERE validator_id = %s"""
                    qdb.sql_connection.TRN.add(
                        sql, [dumps(artifact_data), self.id])
                    qdb.sql_connection.TRN.execute()

                    # Can't create the artifact until all validators
                    # are completed
                    self._set_status('waiting')
            else:
                # The artifact is uploaded by the user or is the initial
                # artifact of an analysis
                if ('analysis' in job_params and
                        job_params['analysis'] is not None):
                    pt = None
                    an = qdb.analysis.Analysis(job_params['analysis'])
                    sql = """SELECT data_type
                             FROM qiita.analysis_processing_job
                             WHERE analysis_id = %s
                                AND processing_job_id = %s"""
                    qdb.sql_connection.TRN.add(sql, [an.id, self.id])
                    data_type = qdb.sql_connection.TRN.execute_fetchlast()
                else:
                    pt = qdb.metadata_template.prep_template.PrepTemplate(
                        job_params['template'])
                    an = None
                    data_type = None

                qdb.artifact.Artifact.create(
                    filepaths, atype, prep_template=pt, analysis=an,
                    data_type=data_type, name=job_params['name'])
                self._set_status('success')

    def _complete_artifact_transformation(self, artifacts_data):
        """Performs the needed steps to complete an artifact transformation job

        In order to complete an artifact transformation job, we need to create
        a validate job for each artifact output and submit it.

        Parameters
        ----------
        artifacts_data : dict of dicts
            The generated artifact information keyed by output name.
            The format of each of the internal dictionaries must be
            {'filepaths': list of (str, str), 'artifact_type': str}
            where `filepaths` contains the list of filepaths and filepath types
            for the artifact and `artifact_type` the type of the artifact

        Raises
        ------
        QiitaDBError
            If there is more than one prep information attached to the new
            artifact
        """
        validator_jobs = []
        with qdb.sql_connection.TRN:
            cmd_id = self.command.id
            for out_name, a_data in artifacts_data.items():
                # Correct the format of the filepaths parameter so we can
                # create a validate job
                filepaths = defaultdict(list)
                for fp, fptype in a_data['filepaths']:
                    filepaths[fptype].append(fp)
                atype = a_data['artifact_type']

                # The validate job needs a prep information file. In theory,
                # a job can be generated from more that one prep information
                # file, so we check here if we have one or more templates. At
                # this moment, If we allow more than one template, there is a
                # fair amount of changes that need to be done on the plugins,
                # so we are going to restrict the number of templates to one.
                # Note that at this moment there is no way of generating an
                # artifact from 2 or more artifacts, so we can impose this
                # limitation now and relax it later.
                templates = set()
                for artifact in self.input_artifacts:
                    templates.update(pt.id for pt in artifact.prep_templates)
                template = None
                analysis = None
                if len(templates) > 1:
                    raise qdb.exceptions.QiitaDBError(
                        "Currently only single prep template "
                        "is allowed, found %d" % len(templates))
                elif len(templates) == 1:
                    template = templates.pop()
                else:
                    # In this case we have 0 templates. What this means is that
                    # this artifact is being generated in the analysis pipeline
                    # All the artifacts included in the analysis pipeline
                    # belong to the same analysis, so we can just ask the
                    # first artifact for the analysis that it belongs to
                    analysis = self.input_artifacts[0].analysis.id

                # Once the validate job completes, it needs to know if it has
                # been generated from a command (and how) or if it has been
                # uploaded. In order to differentiate these cases, we populate
                # the provenance parameter with some information about the
                # current job and how this artifact has been generated. This
                # does not affect the plugins since they can ignore this
                # parameter
                sql = """SELECT command_output_id
                         FROM qiita.command_output
                         WHERE name = %s AND command_id = %s"""
                qdb.sql_connection.TRN.add(sql, [out_name, cmd_id])
                cmd_out_id = qdb.sql_connection.TRN.execute_fetchlast()
                naming_params = self.command.naming_order
                if naming_params:
                    params = self.parameters.values
                    art_name = "%s %s" % (
                        out_name, ' '.join([str(params[p]).split('/')[-1]
                                            for p in naming_params]))
                else:
                    art_name = out_name

                provenance = {'job': self.id,
                              'cmd_out_id': cmd_out_id,
                              'name': art_name}

                # Get the validator command for the current artifact type and
                # create a new job
                # see also release_validators()
                cmd = qdb.software.Command.get_validator(atype)
                values_dict = {
                    'files': dumps(filepaths), 'artifact_type': atype,
                    'template': template, 'provenance': dumps(provenance),
                    'analysis': None}
                if analysis is not None:
                    values_dict['analysis'] = analysis
                validate_params = qdb.software.Parameters.load(
                    cmd, values_dict=values_dict)

                validator_jobs.append(
                    ProcessingJob.create(self.user, validate_params, True))

            # Change the current step of the job
            self.step = "Validating outputs (%d remaining) via job(s) %s" % (
                len(validator_jobs), ', '.join(['%s [%s]' % (
                    j.id, j.external_id) for j in validator_jobs]))

            # Link all the validator jobs with the current job
            self._set_validator_jobs(validator_jobs)

            # Submit m validator jobs as n lists of jobs
            n = qiita_config.trq_dependency_q_cnt

            # taken from:
            # https://www.geeksforgeeks.org/break-list-chunks-size-n-python/
            lists = [validator_jobs[i * n:(i + 1) * n]
                     for i in range((len(validator_jobs) + n - 1) // n)]

            for sub_list in lists:
                # each sub_list will always have at least a lead_job
                lead_job = sub_list.pop(0)
                if not sub_list:
                    # sub_list is now empty
                    sub_list = None
                lead_job.submit(dependent_jobs_list=sub_list)

            # Submit the job that will release all the validators
            plugin = qdb.software.Software.from_name_and_version(
                'Qiita', 'alpha')
            cmd = plugin.get_command('release_validators')
            params = qdb.software.Parameters.load(
                cmd, values_dict={'job': self.id})
            job = ProcessingJob.create(self.user, params)

        # Doing the submission outside of the transaction
        job.submit()

    def _set_validator_jobs(self, validator_jobs):
        """Sets the validator jobs for the current job

        Parameters
        ----------
        validator_jobs : list of ProcessingJob
            The validator_jobs for the current job
        """
        with qdb.sql_connection.TRN:
            sql = """INSERT INTO qiita.processing_job_validator
                        (processing_job_id, validator_id)
                     VALUES (%s, %s)"""
            sql_args = [[self.id, j.id] for j in validator_jobs]
            qdb.sql_connection.TRN.add(sql, sql_args, many=True)
            qdb.sql_connection.TRN.execute()

    def complete(self, success, artifacts_data=None, error=None):
        """Completes the job, either with a success or error status

        Parameters
        ----------
        success : bool
            Whether the job has completed successfully or not
        artifacts_data : dict of dicts, optional
            The generated artifact information keyed by output name.
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
                    # if it did not succeed
                    raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                        "Can't complete job: not in a running state")
                if artifacts_data:
                    if self.command.software.type == 'artifact definition':
                        # There is only one artifact created
                        _, a_data = artifacts_data.popitem()
                        self._complete_artifact_definition(a_data)
                    else:
                        self._complete_artifact_transformation(artifacts_data)
                else:
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

            # All the children should be marked as failure
            for c in self.children:
                c.complete(False, error="Parent job '%s' failed." % self.id)

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

    def update_heartbeat_state(self):
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
        if self.status != 'running':
            raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                "Cannot change the step of a job whose status is not "
                "'running'")
        sql = """UPDATE qiita.processing_job
                 SET step = %s
                 WHERE processing_job_id = %s"""
        qdb.sql_connection.perform_as_transaction(sql, [value, self.id])

    @property
    def children(self):
        """The children jobs

        Returns
        -------
        generator of qiita_db.processing_job.ProcessingJob
            The children jobs
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT child_id
                     FROM qiita.parent_processing_job
                     WHERE parent_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            for jid in qdb.sql_connection.TRN.execute_fetchflatten():
                yield ProcessingJob(jid)

    @property
    def validator_jobs(self):
        """The validators of this job

        Returns
        -------
        generator of qiita_db.processing_job.ProcessingJob
            The validators of this job
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT validator_id
                     FROM qiita.processing_job_validator pjv
                     JOIN qiita.processing_job pj
                         ON pjv.validator_id = pj.processing_job_id
                     JOIN qiita.processing_job_status USING (
                        processing_job_status_id)
                     WHERE pjv.processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            for jid in qdb.sql_connection.TRN.execute_fetchflatten():
                yield ProcessingJob(jid)

    def _update_children(self, mapping):
        """Updates the children of the current job to populate the input params

        Parameters
        ----------
        mapping : dict of {int: int}
            The mapping between output parameter and artifact

        Returns
        -------
        list of qiita_db.processing_job.ProcessingJob
            The list of childrens that are ready to be submitted
        """
        ready = []
        with qdb.sql_connection.TRN:
            sql = """SELECT command_output_id, name
                     FROM qiita.command_output
                     WHERE command_output_id IN %s"""
            sql_args = [tuple(mapping.keys())]
            qdb.sql_connection.TRN.add(sql, sql_args)
            res = qdb.sql_connection.TRN.execute_fetchindex()
            new_map = {name: mapping[oid] for oid, name in res}

            sql = """SELECT command_parameters, pending
                     FROM qiita.processing_job
                     WHERE processing_job_id = %s"""
            sql_update = """UPDATE qiita.processing_job
                            SET command_parameters = %s,
                                pending = %s
                            WHERE processing_job_id = %s"""
            sql_link = """INSERT INTO qiita.artifact_processing_job
                            (artifact_id, processing_job_id)
                          VALUES (%s, %s)"""
            for c in self.children:
                qdb.sql_connection.TRN.add(sql, [c.id])
                params, pending = qdb.sql_connection.TRN.execute_fetchflatten()
                for pname, out_name in pending[self.id].items():
                    a_id = new_map[out_name]
                    params[pname] = str(a_id)
                    del pending[self.id]
                    # Link the input artifact with the child job
                    qdb.sql_connection.TRN.add(sql_link, [a_id, c.id])

                # Force to insert a NULL in the DB if pending is empty
                pending = pending if pending else None
                qdb.sql_connection.TRN.add(sql_update,
                                           [dumps(params), pending, c.id])
                qdb.sql_connection.TRN.execute()

                if pending is None:
                    # The child already has all the parameters
                    # Add it to the ready list
                    ready.append(c)
        return ready

    def _update_and_launch_children(self, mapping):
        """Updates the children of the current job to populate the input params

        Parameters
        ----------
        mapping : dict of {int: int}
            The mapping between output parameter and artifact
        """
        ready = self._update_children(mapping)
        # Submit all the children that already have all the input parameters
        for c in ready:
            c.submit()
            # some jobs create several children jobs/validators and this can
            # clog the submission process; giving it a second to avoid this
            sleep(1)

    @property
    def outputs(self):
        """The outputs of the job

        Returns
        -------
        dict of {str: qiita_db.artifact.Artifact}
            The outputs of the job keyed by output name
        """
        with qdb.sql_connection.TRN:
            if self.status != 'success':
                raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                    "Can't return the outputs of a non-success job")

            sql = """SELECT artifact_id, name
                     FROM qiita.artifact_output_processing_job
                        JOIN qiita.command_output USING (command_output_id)
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return {
                name: qdb.artifact.Artifact(aid)
                for aid, name in qdb.sql_connection.TRN.execute_fetchindex()}

    @property
    def processing_job_workflow(self):
        """The processing job workflow

        Returns
        -------
        ProcessingWorkflow
            The processing job workflow the job
        """
        with qdb.sql_connection.TRN:
            # Retrieve the workflow root jobs
            sql = """SELECT get_processing_workflow_roots
                     FROM qiita.get_processing_workflow_roots(%s)"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            res = qdb.sql_connection.TRN.execute_fetchindex()
            if res:
                sql = """SELECT processing_job_workflow_id
                         FROM qiita.processing_job_workflow_root
                         WHERE processing_job_id = %s"""
                qdb.sql_connection.TRN.add(sql, [res[0][0]])
                r = qdb.sql_connection.TRN.execute_fetchindex()
                return (qdb.processing_job.ProcessingWorkflow(r[0][0]) if r
                        else None)
            else:
                return None

    @property
    def pending(self):
        """A dictionary with the information about the predecessor jobs

        Returns
        -------
        dict
            A dict with {job_id: {parameter_name: output_name}}"""
        with qdb.sql_connection.TRN:
            sql = """SELECT pending
                     FROM qiita.processing_job
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            res = qdb.sql_connection.TRN.execute_fetchlast()
            return res if res is not None else {}

    @property
    def hidden(self):
        """Whether the job is hidden or not

        Returns
        -------
        bool
            Whether the jobs is hidden or not
        """
        with qdb.sql_connection.TRN:
            sql = """SELECT hidden
                     FROM qiita.processing_job
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [self.id])
            return qdb.sql_connection.TRN.execute_fetchlast()

    def hide(self):
        """Hides the job from the user

        Raises
        ------
        QiitaDBOperationNotPermittedError
            If the job is not in the error status
        """
        with qdb.sql_connection.TRN:
            status = self.status
            if status != 'error':
                raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                    'Only jobs in error status can be hidden. Current status: '
                    '%s' % status)
            sql = """UPDATE qiita.processing_job
                     SET hidden = %s
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [True, self.id])
            qdb.sql_connection.TRN.execute()

    @property
    def shape(self):
        """Number of samples, metadata columns and input size of this job

        Returns
        -------
        int, int, int
            Number of samples, metadata columns and input size. None means it
            couldn't be calculated
        """
        samples = None
        columns = None
        study_id = None
        analysis_id = None
        artifact = None
        input_size = None

        parameters = self.parameters.values

        if self.command.name == 'Validate':
            # Validate only has two options to calculate it's size: template (a
            # job that has a preparation linked) or analysis (is from an
            # analysis). However, 'template' can be present and be None
            if 'template' in parameters and parameters['template'] is not None:
                try:
                    pt = qdb.metadata_template.prep_template.PrepTemplate(
                        parameters['template'])
                except qdb.exceptions.QiitaDBUnknownIDError:
                    pass
                else:
                    study_id = pt.study_id
            elif 'analysis' in parameters:
                analysis_id = parameters['analysis']
        elif self.command.name == 'build_analysis_files':
            # build analysis is a special case because the analysis doesn't
            # exist yet
            sanalysis = qdb.analysis.Analysis(parameters['analysis']).samples
            samples = sum([len(sams) for sams in sanalysis.values()])
            input_size = sum([fp['fp_size'] for aid in sanalysis
                              for fp in qdb.artifact.Artifact(aid).filepaths])
        elif self.command.software.name == 'Qiita':
            if 'study' in parameters:
                study_id = parameters['study']
            elif 'study_id' in parameters:
                study_id = parameters['study_id']
            elif 'analysis' in parameters:
                analysis_id = parameters['analysis']
            elif 'analysis_id' in parameters:
                analysis_id = parameters['analysis_id']
            elif 'artifact' in parameters:
                try:
                    artifact = qdb.artifact.Artifact(parameters['artifact'])
                except qdb.exceptions.QiitaDBUnknownIDError:
                    pass
        elif self.input_artifacts:
            artifact = self.input_artifacts[0]
            input_size = sum([fp['fp_size'] for a in self.input_artifacts
                              for fp in a.filepaths])

        # if there is an artifact, then we need to get the study_id/analysis_id
        if artifact is not None:
            if artifact.study is not None:
                study_id = artifact.study.id
            elif artifact.analysis is not None:
                analysis_id = artifact.analysis.id

        # now retrieve the sample/columns based on study_id/analysis_id
        if study_id is not None:
            try:
                st = qdb.study.Study(study_id).sample_template
            except qdb.exceptions.QiitaDBUnknownIDError:
                pass
            else:
                samples = len(st)
                columns = len(st.categories)
        elif analysis_id is not None:
            try:
                analysis = qdb.analysis.Analysis(analysis_id)
            except qdb.exceptions.QiitaDBUnknownIDError:
                pass
            else:
                mfp = qdb.util.get_filepath_information(
                    analysis.mapping_file)['fullpath']
                samples, columns = pd.read_csv(
                    mfp, sep='\t', dtype=str).shape
                input_size = sum([fp['fp_size'] for aid in analysis.samples for
                                  fp in qdb.artifact.Artifact(aid).filepaths])

        return samples, columns, input_size


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
            # Insert the workflow in the processing_job_workflow table
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
    def from_default_workflow(cls, user, dflt_wf, req_params, name=None,
                              force=False):
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
        force : bool
            Force creation on duplicated parameters

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
            # [0] in_degrees returns a tuple, where [0] is the element we want
            all_nodes = {}
            roots = {}

            for node, position in in_degrees:
                dp = node.default_parameter
                cmd = dp.command
                if position == 0:
                    roots[node] = (cmd, dp)
                all_nodes[node] = (cmd, dp)

            # Check that we have all the required parameters
            root_cmds = set(c for c, _ in roots.values())
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
                        p, req_params[c]), force)
                for n, (c, p) in roots.items()}
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
                    # We have already visited this node
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
                    for out, in_param, _ in connections:
                        # We take advantage of the fact the parameters are
                        # stored in JSON to encode the name of the output
                        # artifact from the previous job
                        job_req_params[in_param] = [source_id, out]

                # At this point we should have all the requried parameters for
                # the current job, so create it
                new_job = ProcessingJob.create(
                    user, qdb.software.Parameters.from_default_params(
                        dflt_params, job_req_params), force)
                node_to_job[n] = new_job

                # Create the parent-child links in the DB
                sql_args = [[pid, new_job.id] for pid in parent_ids]
                qdb.sql_connection.TRN.add(sql, sql_args, many=True)

            return cls._common_creation_steps(user, root_jobs, name)

    @classmethod
    def from_scratch(cls, user, parameters, name=None, force=False):
        """Creates a new processing workflow from scratch

        Parameters
        ----------
        user : qiita_db.user.User
            The user creating the workflow
        parameters : qiita_db.software.Parameters
            The parameters of the first job in the workflow
        name : str, optional
            Name of the workflow. Default: generated from user's name
        force : bool
            Force creation on duplicated parameters

        Returns
        -------
        qiita_db.processing_job.ProcessingWorkflow
            The newly created workflow
        """
        job = ProcessingJob.create(user, parameters, force)
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
            nodes = {}
            if edges:
                nodes = {jid: ProcessingJob(jid)
                         for jid in set(chain.from_iterable(edges))}
                edges = [(nodes[s], nodes[d]) for s, d in edges]
                g.add_edges_from(edges)
            # It is possible that there are root jobs that doesn't have any
            # child, so they do not appear on edge list
            sql = """SELECT processing_job_id
                     FROM qiita.processing_job_workflow_root
                     WHERE processing_job_workflow_id = %s"""
            sql_args = [self.id]
            if nodes:
                sql += " AND processing_job_id NOT IN %s"
                sql_args.append(tuple(nodes))
            qdb.sql_connection.TRN.add(sql, sql_args)
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
            # If the above SQL query returns a single element and the value
            # is different from in construction, it means that all the jobs
            # in the workflow are in the same status and it is not
            # 'in_construction', hence raise the error. If the above SQL query
            # returns more than value (len(res) > 1) it means that the workflow
            # is no longer in construction cause some jobs have been submited
            # for processing. Note that if the above query doesn't retrun any
            # value, it means that no jobs are in the workflow and that means
            # that the workflow is in construction.
            if (len(res) == 1 and res[0] != 'in_construction') or len(res) > 1:
                # The workflow is no longer in construction, raise an error
                raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                    "Workflow not in construction")

    def add(self, dflt_params, connections=None, req_params=None,
            opt_params=None, force=False):
        """Adds a new job to the workflow

        Parameters
        ----------
        dflt_params : qiita_db.software.DefaultParameters
            The DefaultParameters object used
        connections : dict of {qiita_db.processing_job.ProcessingJob:
                               {str: str}}, optional
            Dictionary keyed by the jobs in which the new job depends on,
            and values is a dict mapping between source outputs and new job
            inputs
        req_params : dict of {str: object}, optional
            Any extra required parameter values, keyed by parameter name.
            Default: None, all the requried parameters are provided through
            the `connections` dictionary
        opt_params : dict of {str: object}, optional
            The optional parameters to change from the default set, keyed by
            parameter name. Default: None, use the values in `dflt_params`
        force : bool
            Force creation on duplicated parameters

        Raises
        ------
        qiita_db.exceptions.QiitaDBOperationNotPermittedError
            If the workflow is not in construction
        """
        with qdb.sql_connection.TRN:
            self._raise_if_not_in_construction()

            if connections:
                # The new Job depends on previous jobs in the workflow
                req_params = req_params if req_params else {}
                # Loop through all the connections to add the relevant
                # parameters
                for source, mapping in connections.items():
                    source_id = source.id
                    for out, in_param in mapping.items():
                        req_params[in_param] = [source_id, out]

                new_job = ProcessingJob.create(
                    self.user, qdb.software.Parameters.from_default_params(
                        dflt_params, req_params, opt_params=opt_params), force)

                # SQL used to create the edges between jobs
                sql = """INSERT INTO qiita.parent_processing_job
                            (parent_id, child_id)
                         VALUES (%s, %s)"""
                sql_args = [[s.id, new_job.id] for s in connections]
                qdb.sql_connection.TRN.add(sql, sql_args, many=True)
                qdb.sql_connection.TRN.execute()
            else:
                # The new job doesn't depend on any previous job in the
                # workflow, so it is a new root job
                new_job = ProcessingJob.create(
                    self.user, qdb.software.Parameters.from_default_params(
                        dflt_params, req_params, opt_params=opt_params), force)
                sql = """INSERT INTO qiita.processing_job_workflow_root
                            (processing_job_workflow_id, processing_job_id)
                         VALUES (%s, %s)"""
                sql_args = [self.id, new_job.id]
                qdb.sql_connection.TRN.add(sql, sql_args)
                qdb.sql_connection.TRN.execute()

            return new_job

    def remove(self, job, cascade=False):
        """Removes a given job from the workflow

        Parameters
        ----------
        job : qiita_db.processing_job.ProcessingJob
            The job to be removed
        cascade : bool, optional
            If true, remove the also the input job's children. Default: False.

        Raises
        ------
        qiita_db.exceptions.QiitaDBOperationNotPermittedError
            If the workflow is not in construction
            If the job to be removed has children and `cascade` is `False`
        """
        with qdb.sql_connection.TRN:
            self._raise_if_not_in_construction()

            # Check if the given job has children
            children = list(job.children)
            if children:
                if not cascade:
                    raise qdb.exceptions.QiitaDBOperationNotPermittedError(
                        "Can't remove job '%s': it has children" % job.id)
                else:
                    # We need to remove all job's children, remove them first
                    # and then remove the current job
                    for c in children:
                        self.remove(c, cascade=True)

            # Remove any edges (it can only appear as a child)
            sql = """DELETE FROM qiita.parent_processing_job
                     WHERE child_id = %s"""
            qdb.sql_connection.TRN.add(sql, [job.id])

            # Remove as root job
            sql = """DELETE FROM qiita.processing_job_workflow_root
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [job.id])

            # Remove the input reference
            sql = """DELETE FROM qiita.artifact_processing_job
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [job.id])

            # Remove the job
            sql = """DELETE FROM qiita.processing_job
                     WHERE processing_job_id = %s"""
            qdb.sql_connection.TRN.add(sql, [job.id])

            qdb.sql_connection.TRN.execute()

    def submit(self):
        """Submits the workflow to execution

        Raises
        ------
        qiita_db.exceptions.QiitaDBOperationNotPermittedError
            If the workflow is not in construction
        """
        with qdb.sql_connection.TRN:
            self._raise_if_not_in_construction()

            g = self.graph
            # In order to avoid potential race conditions, we are going to set
            # all the children in 'waiting' status before submitting
            # the root nodes
            in_degrees = dict(g.in_degree())
            roots = []
            for job, degree in in_degrees.items():
                if degree == 0:
                    roots.append(job)
                else:
                    job._set_status('waiting')

            for job in roots:
                job.submit()
