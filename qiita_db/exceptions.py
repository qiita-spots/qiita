# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division
import warnings

from qiita_core.exceptions import QiitaError


class QiitaDBError(QiitaError):
    """Base class for all qiita_db exceptions"""
    pass


class QiitaDBNotImplementedError(QiitaDBError):
    """"""
    pass


class QiitaDBExecutionError(QiitaDBError):
    """Exception for error when executing SQL queries"""
    pass


class QiitaDBConnectionError(QiitaDBError):
    """Exception for error when connecting to the db"""
    pass


class QiitaDBColumnError(QiitaDBError):
    """Exception when missing table information or excess information passed"""
    pass


class QiitaDBLookupError(QiitaDBError, LookupError):
    """Exception when converting or getting non-existant values in DB"""
    pass


class QiitaDBArtifactCreationError(QiitaDBError):
    """Exception when creating an artifact"""
    def __init__(self, reason):
        super(QiitaDBArtifactCreationError, self).__init__()
        self.args = ("Cannot create artifact: %s" % reason)


class QiitaDBDuplicateError(QiitaDBError):
    """Exception when duplicating something in the database"""
    def __init__(self, obj_name, attributes):
        super(QiitaDBDuplicateError, self).__init__()
        self.args = ("The '%s' object with attributes (%s) already exists."
                     % (obj_name, attributes),)


class QiitaDBStatusError(QiitaDBError):
    """Exception when editing is done with an unallowed status"""
    pass


class QiitaDBUnknownIDError(QiitaDBError):
    """Exception for error when an object does not exists in the DB"""
    def __init__(self, missing_id, table):
        super(QiitaDBUnknownIDError, self).__init__()
        self.args = ("The object with ID '%s' does not exists in table '%s'"
                     % (missing_id, table),)


class QiitaDBDuplicateHeaderError(QiitaDBError):
    """Exception for error when a MetadataTemplate has duplicate columns"""
    def __init__(self, repeated_headers):
        super(QiitaDBDuplicateHeaderError, self).__init__()
        self.args = ("Duplicate headers found in MetadataTemplate. Note "
                     "that the headers are not case-sensitive, repeated "
                     "header(s): %s." % ', '.join(repeated_headers),)


class QiitaDBDuplicateSamplesError(QiitaDBError):
    """Exception for error when a MetadataTemplate has duplicate columns"""
    def __init__(self, repeated_samples):
        super(QiitaDBDuplicateSamplesError, self).__init__()
        self.args = ("Duplicate samples found in MetadataTemplate: %s."
                     % ', '.join(repeated_samples),)


class QiitaDBIncompatibleDatatypeError(QiitaDBError):
    """When arguments are used with incompatible operators in a query"""
    def __init__(self, operator, argument_type):
        super(QiitaDBIncompatibleDatatypeError, self).__init__()
        self.args = ("The %s operator is not for use with data of type %s" %
                     (operator, str(argument_type)))


class QiitaDBWarning(UserWarning):
    """Warning specific for the QiitaDB domain"""
    pass

warnings.simplefilter('always', QiitaDBWarning)
