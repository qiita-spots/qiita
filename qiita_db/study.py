#!/usr/bin/env python
from __future__ import division

"""
Objects for dealing with Qiita studies

This module provides the implementation of the Study class.


Classes
-------
- `QittaStudy` -- A Qiita study class
"""
# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from datetime import date

from .base import QiitaStatusObject
from .util import check_required, check_table_cols
from .exceptions import QiitaDBNotImplementedError, QiitaDBExecutionError
from .sql_connection import SQLConnectionHandler


REQUIRED_KEYS = {"timeseries_type_id", "lab_person_id", "mixs_compliant",
                 "metadata_complete", "number_samples_collected",
                 "number_samples_promised", "portal_type",
                 "principal_investigator_id", "study_title", "study_alias",
                 "study_description", "study_abstract"}


class Study(QiitaStatusObject):
    """
    Study object to access to the Qiita Study information

    Attributes
    ----------
    name
    sample_ids
    info

    Methods
    -------
    add_samples(samples)
        Adds the samples listed in `samples` to the study

    remove_samples(samples)
        Removes the samples listed in `samples` from the study
    """

    @staticmethod
    def create(owner, info, investigation=None):
        """Creates a new study on the database

        Parameters
        ----------
        owner : str
            the user id of the study' owner
        info: dict
            the information attached to the study
        investigation: dict
            if the study is part of an investigation, the information needed to
            create the investigation or add study to investigation

        Raises
        ------
        QiitaDBExecutionError
            All required keys not passed or non-db columns in info dictionary

        Notes
        -----
        If investigation_id passed in investigation database, will assume that
        study is part of that investigation. Otherwise need to pass the
        following keys in investigation: "name", "description",
        "contact_person_id"
        """
        # make sure required keys are in the info dict
        check_required(info, REQUIRED_KEYS) 

        conn_handler = SQLConnectionHandler()
        # make sure dictionary only has keys for available columns in db
        check_table_cols(conn_handler, info, "study")

        # Insert study into database
        sql = ("INSERT INTO qiita.study (email,study_status_id,first_contact,"
               "%s) VALUES (%s) RETURNING study_id" % (','.join(info.keys()),
                                                       '%s' * (len(info)+3)))
        # make sure data in same order as sql column names
        data = [owner, 1, date.today().strftime("%B %d, %Y")]
        for col in info.keys():
            data.append(info[col])
        study_id = conn_handler.execute_fetchone(sql, data)[0]

        # Insert investigation information if necessary
        if investigation:
            if "investigation_id" in investigation:
                # investigation already exists
                inv_id = investigation["investigation_id"]
            else:
                # investigation does not exist in db so create it and add study
                sql = ("INSERT INTO qiita.investigation(name, description,"
                       "contact_person_id) VALUES (%s,%s,%s) RETURNING "
                       "investigation_id")
                data = (investigation["name"], investigation["description"],
                        investigation["contact_person_id"])
                inv_id = conn_handler.execute_fetchone(sql, data)[0]
            # add study to investigation
            sql = ("INSERT INTO qiita.investigation_study (investigation_id, "
                   "study_id) VALUES (%s, %s)")
            conn_handler.execute(sql, (inv_id, study_id))

        return Study(study_id)

    @staticmethod
    def delete(id_):
        """Deletes the study `id_` from the database

        Parameters
        ----------
        id_ :
            The object identifier
        """
        raise QiitaDBNotImplementedError()

    @property
    def name(self):
        """Returns the name of the study"""
        conn_handler = SQLConnectionHandler()
        sql = "SELECT name FROM qiita.study WHERE study_id = %s"
        return conn_handler.execute_fetchone(sql, self.id_)[0]

    @name.setter
    def name(self, name):
        """Sets the name of the study

        Parameters
        ----------
        name : str
            The new study name
        """
        raise QiitaDBNotImplementedError()

    @property
    def sample_ids(self):
        """Returns the IDs of all samples in study

        The sample IDs are returned as a list of strings in alphabetical order.
        """
        raise QiitaDBNotImplementedError()

    @property
    def info(self):
        """Dict with any other information attached to the study"""
        raise QiitaDBNotImplementedError()

    @info.setter
    def info(self, info):
        """Updates the information attached to the study

        Parameters
        ----------
        info : dict
        """
        raise QiitaDBNotImplementedError()

    def add_samples(self, samples):
        """Adds the samples listed in `samples` to the study
        Parameters
        ----------
        samples : list of strings
            The sample Ids to be added to the study
        """
        raise QiitaDBNotImplementedError()

    def remove_samples(self, samples):
        """Removes the samples listed in `samples` from the study
        Parameters
        ----------
        samples : list of strings
            The sample Ids to be removed from the study
        """
        raise QiitaDBNotImplementedError()
