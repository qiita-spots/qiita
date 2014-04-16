#!/usr/bin/env python
from __future__ import division

# -----------------------------------------------------------------------------
# Copyright (c) 2014, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------


def create_analysis(analysis_name, **kwargs):
    """ Adds a new Qiita analysis to the system

    Inputs:
        analysis_name: the name of the new analysis
        kwargs: extra analysis information

    Returns:
        The new QiitaAnalysis object

    Checks:
        - Valid analysis_name

    Raises an error if something went wrong
    """
    raise NotImplementedError("qiita_ware.api.analysis_manager: "
                              "create_analysis")


def update_analysis(analysis):
    """ Updates the analysis information in the system

    Inputs:
        analysis: a QiitaAnalysis object

    Checks:
        - Analysis is mutable - double checked, should be embedded on the
            QiitaAnalysis object

    Does not perform any data content check - assumed to be included on the
        QiitaAnalysis obj
    Raises an error if something went wrong
    """
    raise NotImplementedError("qiita_ware.api.analysis_manager: "
                              "update_analysis")


def delete_analysis(analysis_id):
    """ Deletes the QiitaAnalysis analysis_id from the system

    Inputs:
        analysis_id: the analysis id to remove

    Checks:
        - analysis exists
        - analysis status:
            Public: raise error
            Shared: if Force remove else error
            Private: remove
    """
    raise NotImplementedError("qiita_ware.api.analysis_manager: "
                              "delete_analysis")


def get_analysis(analysis_id):
    """ Retrieves the analysis_id object

    Inputs:
        analysis_id: the id of the analysis to retrieve

    Returns:
        The QiitaAnalysis object

    Raises an error if something went wrong
    """
    raise NotImplementedError("qiita_ware.api.analysis_manager: get_analysis")


def search_analyses(analysis_name_hint, **kwargs):
    """ Retrieves all the analyses in the system that match the search query

    Inputs:
        user_id: the user that makes the search
        analysis_name_hint: string with a partial analysis name
        **kwargs: extra analysis information

    Returns:
        A list with all the QiitaAnalysis objects that match the search query
            that are visible by the user_id
    """
    raise NotImplementedError("qiita_ware.api.analysis_manager: "
                              "search_analyses")


def stop_analysis(analysis_id):
    """ Stops all the running jobs of analysis_id

    Inputs:
        analysis_id: the analysis to be stopped
    """
    raise NotImplementedError("qiita_ware.api.analysis_manager: stop_analysis")


def publish_analysis(analysis_id):
    """ Makes analysis_id public

    Inputs:
        analysis_id: id of the analysis
    """
    raise NotImplementedError("qiita_ware.api.analysis_manager: "
                              "publish_analysis")

##############################################
#                                            #
# Functions only need in local installations #
#                                            #
##############################################


def submit_analysis_to_QiitaMain(analysis_id, **kwargs):
    """ Submits anlysis_id to the Qiita Main repository hosted in the
            Knight Lab

        Inputs:
            analysis_id: the analysis to upload
            kwargs: TBD
    """
    raise NotImplementedError("qiita_ware.api.analysis_manager: "
                              "submit_analysis_to_QiitaMain")

############################################
#                                          #
# Functions only need if using Qiita-pet   #
# as a front-end. Otherwise, there is no   #
# notion of users.                         #
#                                          #
############################################


def get_all_visible_analyses(user_id):
    """ Retrieves all the analysis visible by user_id

    Inputs:
        user_id: the user id

    Returns:
        A list with all QiitaAnalysis objs that are visible by user_id
    """
    raise NotImplementedError("qiita_ware.api.analysis_manager: "
                              "get_all_visible_analyses")


def get_running_analyses(user_id):
    """ Retrieves all the running analysis visible by user_id

    Inputs:
        user_id: the user id

    Returns:
        A list with all QiitaAnalysis objs that are running and visible
            by user_id
    """
    raise NotImplementedError("qiita_ware.api.analysis_manager: "
                              "get_running_analyses")


def get_completed_analyses(user_id):
    """ Retrieves all the completed analysis visible by user_id

    Inputs:
        user_id: the user id

    Returns:
        A list with all QiitaAnalysis objs that are completed and visible
            by user_id
    """
    raise NotImplementedError("qiita_ware.api.analysis_manager: "
                              "get_completed_analyses")


def share_analysis(analysis_id, user_id):
    """ Shares the analysis_id with user_id

    Inputs:
        analysis_id: id of the analysis
        user_id: user to share the analysis with
    """
    raise NotImplementedError("qiita_ware.api.analysis_manager: "
                              "share_analysis")


def transfer_analysis(analysis_id, user_id):
    """ Transfers ownership of analysis_id to user_id

    Inputs:
        analysis_id: id of the analysis
        user_id: user to transfer ownership of the analysis to
    """
    raise NotImplementedError("qiita_ware.api.analysis_manager: "
                              "trasnfer_analysis")
