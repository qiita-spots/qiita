from __future__ import division

from shutil import rmtree
from os import remove
from sys import stderr

import networkx as nx
from moi.job import submit, ctxs, ctx_default


class ParallelWrapper(object):
    """Base class for any parallel code"""
    def __init__(self, retain_temp_files=False, block=True,
                 moi_update_status=None, moi_context=None, moi_parent_id=None):
        self._retain_temp_files = retain_temp_files
        self._block = block
        self._job_graph = nx.DiGraph()
        self._logger = None
        self._filepaths_to_remove = []
        self._dirpaths_to_remove = []
        self._update_status = moi_update_status
        self._context = ctxs.get(moi_context, ctxs[ctx_default])
        self._group = moi_parent_id

    def _construct_job_graph(self, *args, **kwargs):
        """Constructs the workflow graph with the jobs to execute

        Raises
        ------
        NotImplementedError
            If not overwritten in a subclass
        """
        raise NotImplementedError("This method should be overwritten by the "
                                  "subclass")

    def _failure_callback(self, msg=None):
        """Callback to execute in case that any of the job nodes failed

        Parameters
        ----------
        msg : str
            Any message generated from the failure
        """
        pass

    def _validate_execution_order(self, results):
        """Makes sure that the execution order represented in _job_graph has
        been respected

        Parameters
        ----------
        results : dict of {Node: AsyncResult}
            The AsyncResult objects of the executed jobs
        """
        # Adapted from
        # http://ipython.org/ipython-doc/dev/parallel/dag_dependencies.html
        self._logger.write("Validating execution order... ")
        for node in self._job_graph:
            started = results[node].metadata.started
            if started is None:
                self._logger.write("Job %s: starting time not available"
                                   % node)
                continue

            for parent in self._job_graph.predecessors(node):
                finished = results[parent].metadata.completed
                if finished is None:
                    self._logger.write("Job %s: finish time not available"
                                       % parent)
                    continue

                if started < finished:
                    self._logger.write(
                        "Job order not respected: %s should have happened "
                        "after %s\n" % (node, parent))

        self._logger.write("Done\n")

    def _validate_job_status(self, results):
        """Validates that all jobs executed finished correctly

        Parameters
        ----------
        results : dict of {Node: AsyncResult}
            The AsyncResult objects of the executed jobs
        """
        self._logger.write("\nValidating job status:\n")
        errored = False
        callback_msg = []
        for node, ar in results.items():
            msg = ["\nJob %s: " % node]
            if ar.successful():
                msg.append("Success\n")
            else:
                errored = True
                msg.append("Error\n")
                try:
                    job_result = ar.get()
                except Exception, e:
                    job_result = e
                msg.append("\tJob results: %s\n"
                           "\tPython output: %s\n"
                           "\tStandard output: %s\n"
                           "\tStandard error: %s\n"
                           % (job_result, ar.pyout, ar.stdout, ar.stderr))
                callback_msg.append(''.join(msg))
            self._logger.write(''.join(msg))

        if errored:
            self._failure_callback(msg='\n'.join(callback_msg))

    def _clean_up_paths(self):
        """Removes the temporary paths"""
        if not self._retain_temp_files:
            self._logger.write("\nCleaning up temporary files")
            for fp in self._filepaths_to_remove:
                remove(fp)
            for dp in self._dirpaths_to_remove:
                rmtree(dp)

    def _job_blocker(self, results):
        # Block until all jobs are done
        self._logger.write("\nWaiting for all jobs to finish... ")
        self._context.bv.wait(results.values())
        self._logger.write("Done\n")
        self._validate_job_status(results)
        self._validate_execution_order(results)
        self._clean_up_paths()
        if self._logger != stderr:
            self._logger.close()

    def _submit_with_deps(self, deps, name, func, *args, **kwargs):
        """Submit with dependencies

        Parameters
        ----------
        deps : list of AsyncResult
            AsyncResults that this new job depend on
        name : str
            A job name
        func : function
            The function to submit

        Returns
        -------
        AsyncResult
            The result returned by IPython's apply_async.
        """
        parent_id = self._group
        url = None

        with self._context.bv.temp_flags(after=deps, block=False):
            _, _, ar = submit(self._context, parent_id, name, url, func,
                              *args, **kwargs)
        return ar

    def __call__(self, *args, **kwargs):
        self._construct_job_graph(*args, **kwargs)

        if self._logger is None:
            self._logger = stderr

        # Adapted from
        # http://ipython.org/ipython-doc/dev/parallel/dag_dependencies.html
        async_results = {}
        for node_name in nx.topological_sort(self._job_graph):
            node = self._job_graph.node[node_name]
            requires_deps = node.get('requies_deps', False)

            func = node['func']
            args = node['args']
            job_name = node['job_name']
            kwargs = {}

            deps = []
            dep_results = {}
            kwargs['dep_results'] = dep_results
            for predecessor_name in self._job_graph.predecessors(node_name):
                predecessor_result = async_results[predecessor_name]
                deps.append(predecessor_result)

                if requires_deps:
                    dep_results[predecessor_name] = predecessor_result.get()

            self._logger.write("Submitting %s: %s %s...\n " % (node_name,
                                                               func.__name__,
                                                               args))

            async_results[node_name] = \
                self._submit_with_deps(deps, job_name, func, *args, **kwargs)

            self._logger.write("Done\n")

        if self._block:
            self._job_blocker(async_results)
