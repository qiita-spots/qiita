#!/usr/bin/env python

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = ["Jose Antonio Navas Molina", "Joshua Shorenstein"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"


from qiita.core.exceptions import (QiitaUserError,
                                   IncompetentQiitaDeveloperError)

LEVELS = ('admin', 'dev', 'superuser', 'user', 'guest')


class QiitaUser(object):
    """Models an user of Qiita"""

    def __init__(self, email, level, info=None, **kwargs):
        """Initializes the QiitaUser object

        Inputs:
            email: the email (also username) of the user
            level: the level of the user
            info: attached information to the user

        Raises an IncompetentQiitaDeveloperError if:
            - level is not recognized
            = info is provided and is not a dictionary
        """
        self.email = email
        if level and level not in LEVELS:
            raise IncompetentQiitaDeveloperError("level not recognized: %s"
                                                 % level)
        self._level = level
        if not isinstance(info, dict):
            raise IncompetentQiitaDeveloperError("info should be a dictionary."
                                                 " %s found" % type(info))
        self.info = info if info else {}
        self._analyses = kwargs.get("analyses", [])
        self._studies = kwargs.get("studies",  [])
        self._shared_analyses = kwargs.get("shared_analyses",  [])
        self._shared_studies = kwargs.get("shared_studies",  [])

    #properties for enum-type variables
    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, level):
        if level not in LEVELS:
            raise IncompetentQiitaDeveloperError("Level not recognised: %s" %
                                                 level)
        self._level = level

    #helper functions attached to object
    def check_password(self, check_pwd):
        """Checks that check_pwd is the user's password"""
        # We may want to check this on the DB
        raise NotImplementedError("QiitaUser.check_password")

    # Functions for list type objects
    def add_analysis(self, analysis_id):
        """Adds an analysis to the user list

        Inputs:
            analysis: the id of the analysis
        """
        self._analyses.append(analysis_id)

    def add_shared_analysis(self, analysis_id):
        """Adds a shared analysis to the user list

        Inputs:
            analysis_id: the id of the analysis
        """
        self._shared_analyses.append(analysis_id)

    def add_study(self, study_id):
        """Adds a study to the user list

        Inputs:
            study_id: the id of the study
        """
        self._studies.append(study_id)

    def add_shared_study(self, study_id):
        """Adds a shared study to the user list

        Inputs:
            study_id: the id of the study
        """
        self._shared_studies.append(study_id)

    # Remove functions
    def remove_analysis(self, analysis_id):
        """Removes the given analysis from the user list

        Inputs:
            analysis_id: the id of the analysis

        Raises a QiitaUserError if analysis_id is not own by the user
        """
        try:
            self._analyses.remove(analysis_id)
        except ValueError:
            raise QiitaUserError("User does not own analysis %s" % analysis_id)

    def remove_shared_analysis(self, analysis_id):
        """Removes the given analysis from the user shared list

        Inputs:
            analysis_id: the id of the analysis

        Raises a QiitaUserError if analysis_id is not shared with the user
        """
        try:
            self._shared_analyses.remove(analysis_id)
        except ValueError:
            raise QiitaUserError("User does not have analysis %s shared"
                                 % analysis_id)

    def remove_study(self, study_id):
        """Removes the given study from the user list

        Inputs:
            study_id: the study id

        Raises a QiitaUserError if study_id is not own by the user
        """
        try:
            self._studies.remove(study_id)
        except ValueError:
            raise QiitaUserError("User does not own study %s" % study_id)

    def remove_shared_study(self, study_id):
        """Removes the given study from the user shared list

        Inputs:
            study_id: the study id

        Raises a QiitaUserError if study_idis not shared with the user
        """
        try:
            self._shared_studies.remove(study_id)
        except ValueError:
            raise QiitaUserError("User does not have study %s shared"
                                 % study_id)

    def get_analysis(self, ):
        """Gets an analysis to the user list

        Inputs:
            analysis: the id of the analysis
        """
        self._analyses.append()

    def get_shared_analysis(self, ):
        """Gets a shared analysis to the user list
        """
        self._shared_analyses.append()

    def get_study(self, study_id):
        """Gets a study to the user list

        Inputs:
            study_id: the id of the study
        """
        self._studies.append(study_id)

    def get_shared_study(self, study_id):
        """Gets a shared study to the user list

        Inputs:
            study_id: the id of the study
        """
        self._shared_studies.append(study_id)
