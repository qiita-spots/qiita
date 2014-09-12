from subprocess import Popen, PIPE

from IPython.parallel import Client

from qiita_ware.exceptions import ComputeError


def system_call(cmd):
    """Call cmd and return (stdout, stderr, return_value).

    cmd: can be either a string containing the command to be run, or a
     sequence of strings that are the tokens of the command.

    This function is ported from QIIME (http://www.qiime.org), previously
    named qiime_system_call. QIIME is a GPL project, but we obtained permission
    from the authors of this function to port it to pyqi (and keep it under
    pyqi's BSD license).
    """
    proc = Popen(cmd,
                 universal_newlines=True,
                 shell=True,
                 stdout=PIPE,
                 stderr=PIPE)
    # communicate pulls all stdout/stderr from the PIPEs to
    # avoid blocking -- don't remove this line!
    stdout, stderr = proc.communicate()
    return_value = proc.returncode

    if return_value != 0:
        raise ComputeError("Failed to execute: %s\nstdout: %s\nstderr: %s" %
                           (cmd, stdout, stderr))

    return stdout, stderr, return_value


class Dispatch(object):
    """Dispatch compute

    Attributes
    ----------
    reserved
    reserved_lview
    general
    general_lview
    demo
    demo_lview

    Methods
    -------
    submit_async
    submit_async_deps
    submit_sync
    sync

    """
    def __init__(self):
        # self.reserved = Client(profile='qiita_reserved')
        # self.general = Client(profile='qiita_general')
        self.demo = Client(profile='qiita_demo')

        # self._stage_imports(self.reserved)
        # self._stage_imports(self.general)
        self._stage_imports(self.demo)

        # self.reserved_lview = self.reserved.load_balanced_view()
        # self.general_lview = self.general.load_balanced_view()
        self.demo_lview = self.demo.load_balanced_view()

    def _stage_imports(self, cluster):
        with cluster[:].sync_imports(quiet=True):
            from qiita_ware.context import system_call  # noqa

    def sync(self, data):
        """Sync data to engines

        Parameters
        ----------
        data : dict
            dict of objects and to sync

        """
        # self.reserved[:].update(data)
        # self.general[:].update(data)
        self.demo[:].update(data)

    def submit_async(self, cmd, *args, **kwargs):
        """Submit an async command to execute

        Parameters
        ----------
        cmd : {function, str}
            A function to execute or a system call to execute
        args : list
            Arguments to pass to a function (if cmd is function)
        kwargs : dict
            Keyword arguments to pass to a function (if cmd is function)

        Returns
        -------
        IPython.parallel.client.asyncresult.AsyncResult

        """
        if isinstance(cmd, str):
            task = self.demo_lview.apply_async(system_call, cmd)
        else:
            task = self.demo_lview.apply_async(cmd, *args, **kwargs)

        return task

    def submit_async_deps(self, deps, cmd, *args, **kwargs):
        """Submit as async command to execute after all dependencies are done

        Parameters
        ----------
        deps : list of AsyncResult
            The list of job dependencies for cmd
        cmd : {function, str}
            A function to execute or a system call to execute
        args : list
            Arguments to pass to a function (if cmd is function)
        kwargs : dict
            Keyword arguments to pass to a function (if cmd is function)

        Returns
        -------
        IPython.parallel.client.asyncresult.AsyncResult
        """
        with self.demo_lview.temp_flags(after=deps, block=False):
            if isinstance(cmd, str):
                task = self.demo_lview.apply_async(system_call, cmd)
            else:
                task = self.demo_lview.apply_async(cmd, *args, **kwargs)

        return task

    def submit_sync(self, cmd, *args, **kwargs):
        """Submit an sync command to execute

        Parameters
        ----------
        cmd : {function, str}
            A function to execute or a system call to execute
        args : list
            Arguments to pass to a function (if cmd is function)
        kwargs : dict
            Keyword arguments to pass to a function (if cmd is function)

        Returns
        -------
        Dependent on cmd

        """
        if isinstance(cmd, str):
            result = self.demo_lview.apply_sync(system_call, cmd)
        else:
            result = self.demo_lview.apply_sync(cmd, *args, **kwargs)

        return result

# likely want this in qiita_ware.__init__
context = Dispatch()
