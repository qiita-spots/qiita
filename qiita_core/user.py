#!/usr/bin/env python

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = ["Jose Antonio Navas Molina", "Joshua Shorenstein"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"


from qiita.core.exceptions import QiitaUserError, IncompetentQiitaDeveloper

LEVELS = ['admin', 'dev', 'superuser', 'regular', 'guest']


class QiitaUser(object):
    """Models an user of Qiita"""

    def __init__(self, email, level, info=None):
        """Initializes the QiitaUser object

        Inputs:
            email: the email (also username) of the user
            level: the level of the user
            info: attached information to the user

        Raises an IncompetentQiitaDeveloper if:
            - level is not recognized
            = info is provided and is not a dictionary
        """
        self._email = email
        if level and level not in LEVELS:
            raise IncompetentQiitaDeveloper("level not recognized: %s" % level)
        self._level = level
        if info and type(info) is not dict:
            raise IncompetentQiitaDeveloper("info should be a dictionary. %s "
                                            "found" % type(info))
        self._info = info if info else {}
        self._analyses = None
        self._studies = None
        self._shared_analyses = None
        self._shared_studies = None

    def check_password(self, check_pwd):
        """Checks that check_pwd is the user's password"""
        # We may want to check this on the DB
        raise NotImplementedError("QiitaUser.check_password")

    # Get functions
    def get_email(self):
        """Retrieves the user email"""
        return self._email

    def get_level(self):
        """Retrieves the user level"""
        return self._level

    # Set functions
    def set_email(self, email):
        """Raises a QiitaUserError. The email can't be changed"""
        raise QiitaUserError("The email of a user can't be changed")

    def set_level(self, level):
        """Sets the level of the user"""
        self._level = level

    # Add functions
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
        except ValueError, e:
            raise QiitaUserError("User does not own analysis %s" % analysis_id)

    def remove_shared_analysis(self, analysis_id):
        """Removes the given analysis from the user shared list

        Inputs:
            analysis_id: the id of the analysis

        Raises a QiitaUserError if analysis_id is not shared with the user
        """
        try:
            self._shared_analyses.remove(analysis_id)
        except ValueError, e:
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
        except ValueError, e:
            raise QiitaUserError("User does not own study %s" % study_id)

    def remove_shared_study(self, study_id):
        """Removes the given study from the user shared list

        Inputs:
            study_id: the study id

        Raises a QiitaUserError if study_idis not shared with the user
        """
        try:
            self._shared_studies.remove(study)
        except ValueError, e:
            raise QiitaUserError("User does not have study %s shared"
                                 % study_id)
