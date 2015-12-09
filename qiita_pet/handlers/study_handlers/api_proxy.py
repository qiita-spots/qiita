# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

from qiita_core.qiita_settings import qiita_config
from qiita_db.study import Study

from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.util import check_access

html_error_message = "<b>An error occurred %s %s</b></br>%s"


def _approve(level):
    """Check if the study can be approved based on user level and configuration

    Parameters
    ----------
    level : str
        The level of the current user

    Returns
    -------
    bool
        Whether the study can be approved or not
    """
    return True if not qiita_config.require_approval else level == 'admin'


class StudyAPIProxy(BaseHandler):
    """Adds API proxy functions to the handler. Can be removed once the restful
       API is in place."""
    def study_prep_proxy(self, study_id):
        """Proxies expected json from the API for existing prep templates

        Parameters
        ----------
        study_id : int
            Study id to get prep template info for

        Returns:
        dict of list of dict
            prep template information seperated by data type, in the form
            {data_type: [{prep 1 info dict}, ....], ...}
        """
        # Can only pass ids over API, so need to instantiate object
        study = Study(study_id)
        check_access(self.current_user, study, raise_error=True)
        prep_info = {}
        for dtype in study.data_types:
            prep_info[dtype] = []
            for prep in study.prep_templates(dtype):
                start_artifact = prep.artifact
                info = {
                    'name': 'PREP %d NAME' % prep.id,
                    'id': prep.id,
                    'status': prep.status,
                    'start_artifact': start_artifact.artifact_type,
                    'start_artifact_id': start_artifact.id,
                    'last_artifact': 'TODO'
                }
                prep_info[dtype].append(info)
        return prep_info

    def study_data_types_proxy(self):
        """Proxies expected json from the API for available data types

        Returns
        -------
        list of str
            Data types available on the system
        """
        data_types = Study.all_data_types()
        return data_types if data_types else []

    def study_info_proxy(self, study_id):
        """Proxies expected json from the API for base study info

        Parameters
        ----------
        study_id : int
            Study id to get prep template info for

        Returns:
        dict of list of dict
            prep template information seperated by data type, in the form
            {data_type: [{prep 1 info dict}, ....], ...}
        """
        # Can only pass ids over API, so need to instantiate object
        study = Study(study_id)
        check_access(self.current_user, study, raise_error=True)
        study_info = study.info
        study_info['publication_doi'] = [p[0] for p in study.publications]
        study_info['study_id'] = study.id
        study_info['study_title'] = study.title

        pi = study_info["principal_investigator"]
        study_info["principal_investigator"] = '%s (%s)' % (pi.name,
                                                            pi.affiliation)

        lab_person = study_info["lab_person"]
        study_info["lab_person"] = '%s (%s)' % (lab_person.name,
                                                lab_person.affiliation)

        samples = study.sample_template.keys()
        study_info['num_samples'] = 0 if samples is None else len(set(samples))
        return study_info
