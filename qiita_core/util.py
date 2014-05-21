# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from qiita_core.config import qiita_config


def qiita_test_checker():
    """Decorator that allows the execution of all methods in a test class only
    and only if Qiita is set up to work in a test environment.

    Raises
    ------
    RuntimeError
        If Qiita is set up to work in a production environment
    """
    def checker(cls):
        if not qiita_config.test_environment:
            raise RuntimeError("Working in a production environment. Not "
                               "executing the tests to keep the production "
                               "database safe.")
        return cls
    return checker