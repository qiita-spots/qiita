# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------


class QiitaClientError(Exception):
    pass


class NotFoundError(QiitaClientError):
    pass


class BadRequestError(QiitaClientError):
    pass


class ForbiddenError(QiitaClientError):
    pass
