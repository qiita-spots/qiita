from IPython.parallel import Client

from qiime.util import qiime_system_call
from qiita_ware.exceptions import ComputeError


def system_call(cmd, *args, **kwargs):
    stdout, stderr, exit_status = qiime_system_call(cmd)
    if exit_status != 0:
        raise ComputeError("Failed to execute: %s\nstdout: %s\nstderr: %s" %
                           (cmd, stdout, stderr))


class ClusterDispatch(object):
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
    submit
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
            from qiita_core.cluster import system_call

    def sync(self, data):
        """Sync data to engines

        Parameters
        ----------
        data : dict
            dict of objects and to sync

        """
        self.demo[:].update(data)
        self.reserved[:].update(data)
        self.general[:].update(data)

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

qiita_compute = ClusterDispatch()
