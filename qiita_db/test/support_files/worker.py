#!/usr/bin/env python
import sys
from json import dumps
from os import mkdir, utime
from os.path import exists

import click


@click.command()
@click.option("--fp_archive", required=False, type=str)
@click.option("--fp_biom", required=False, type=str)
@click.option("--output_dir", required=False, type=str)
# The above parameters are actually required. However,
# for testing purposes, they are optional here. Specifically, they
# are optional to test use cases where one or both are missing.
#
# For testing purposes, assume that --fp_archive specifies a path to a .json
# file, and after worker.py (or another process) is completed, fp_archive
# specifies a path to a .tre file.
#
# --env_report is a worker.py specific flag to report the python environment
# version that this script is currently running in. Useful for testing
# environment switching.
@click.option("--env_report", is_flag=True, default=False)
# execute needed to support click
def execute(fp_archive, fp_biom, output_dir, env_report):
    """worker.py implements an example interface to directly communicate
    with plugins, or other external programs.
    """

    if env_report:
        d = {
            "version_major": "%d" % sys.version_info.major,
            "version_minor": "%d" % sys.version_info.minor,
            "version_micro": "%d" % sys.version_info.micro,
        }
        click.echo("%s" % dumps(d))
    else:
        fp_archive = fp_archive.replace(".json", ".tre")

        # creating blank files
        if not exists(output_dir):
            mkdir(output_dir)
        for fname in [fp_archive, fp_biom]:
            with open(fname, "a"):
                utime(fname, None)

        d = {"archive": fp_archive, "biom": fp_biom, "output_dir": output_dir}
        click.echo("%s" % dumps(d))


if __name__ == "__main__":
    execute()
