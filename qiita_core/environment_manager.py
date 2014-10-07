from os import fork
from sys import exit

from IPython.parallel.apps.ipclusterapp import IPClusterStart, IPClusterStop


def start_cluster(profile, n):
    """Start a cluster"""
    me = fork()
    if me == 0:
        c = IPClusterStart(profile=profile, log_level=0, daemonize=True)
        c.n = n
        c.initialize(argv=[])
        c.start()


def stop_cluster(profile):
    """Stop a cluster"""
    me = fork()
    if me == 0:
        c = IPClusterStop(profile=profile, log_level=0)
        c.initialize(argv=[])
        c.start()
        exit(0)
