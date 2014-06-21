from IPython.parallel.apps.ipclusterapp import IPClusterStart, IPClusterStop


def start_cluster(profile, n):
    """Start a cluster"""
    c = IPClusterStart(profile=profile, log_level=0, daemonize=True)
    c.n = n
    c.initialize(argv=[])
    c.start()


def stop_cluster(profile):
    """Stop a cluster"""
    c = IPClusterStop(profile=profile, log_level=0)
    c.initialize(argv=[])
    c.start()
