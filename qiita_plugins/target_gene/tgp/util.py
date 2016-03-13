# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from subprocess import Popen, PIPE

JOB_COMPLETED = False


def system_call(cmd):
    """Call command and return (stdout, stderr, return_value)

    Parameters
    ----------
    cmd : str or iterator of str
        The string containing the command to be run, or a sequence of strings
        that are the tokens of the command.

    Returns
    -------
    str, str, int
        - The stabdard output of the command
        - The standard error of the command
        - The exit status of the command

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
