#!/usr/bin/env python

__author__ = "Joshua Shorenstein"
__copyright__ = "Copyright 2013, The QiiTa-pet Project"
__credits__ = ["Joshua Shorenstein", "Jose Antonio Navas Molina"]
__license__ = "BSD"
__version__ = "0.2.0-dev"
__maintainer__ = "Joshua Shorenstein"
__email__ = "Joshua.Shorenstein@colorado.edu"
__status__ = "Development"

from redis import Redis
from redis.exceptions import RedisError

# Set up Redis connection
try:
    r_server = Redis()
except RedisError, e:
    raise RuntimeError("Unable to connect to the REDIS database: %s" % e)