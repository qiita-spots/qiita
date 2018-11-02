#!/usr/bin/env python
import sys

# sample worker process prints the version information for the environment
# it is running in. Useful for confirming Popen is spawning processes with
# in the correct Python environment.
sys.stdout.write("Worker running Python %s\n" % str(sys.version_info))
sys.stdout.write(">>%s<<" % (sys.argv))
