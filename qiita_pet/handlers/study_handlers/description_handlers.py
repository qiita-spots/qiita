# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from __future__ import division

from tornado.web import authenticated, HTTPError


from qiita_core.qiita_settings import qiita_config
from qiita_db.study import Study, StudyPerson

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


def _to_int(value):
    """Transforms `value` to an integer

    Parameters
    ----------
    value : str or int
        The value to transform

    Returns
    -------
    int
        `value` as an integer

    Raises
    ------
    HTTPError
        If `value` cannot be transformed to an integer
    """
    try:
        res = int(value)
    except ValueError:
        raise HTTPError(500, "%s cannot be converted to an integer" % value)
    return res


class StudyIndexHandler(BaseHandler):
    def study_prep_proxy(self, study):
        """Proxies expected json from the API for existing prep templates"""
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
        """Proxies expected json from the API for available data types"""
        data_types = Study.all_data_types()
        return data_types if data_types else []

    def study_info_proxy(self, study):
        """Proxies expected json from the API for base study info"""
        study_info = Study.get_info([study.id])[0]

        pi = StudyPerson(study_info["principal_investigator_id"])
        study_info["principal_investigator"] = '%s (%s)' % (
            pi.name, pi.affiliation)
        del study_info["principal_investigator_id"]

        lab_person = StudyPerson(study_info["lab_person_id"])
        study_info["lab_person"] = '%s (%s)' % (
            lab_person.name, lab_person.affiliation)
        del study_info["lab_person_id"]
        samples = study.sample_template.keys()
        study_info['num_samples'] = 0 if samples is None else len(set(samples))
        return study_info

    @authenticated
    def get(self, study_id):
        study = Study(_to_int(study_id))
        check_access(self.current_user, study, raise_error=True)
        prep_info = self.study_prep_proxy(study)
        data_types = self.study_data_types_proxy()
        study_info = self.study_info_proxy(study)
        self.render("study_base.html", prep_info=prep_info,
                    data_types=data_types, study_info=study_info)


class StudyBaseInfoAJAX(BaseHandler):
    def study_info_proxy(self, study):
        """Proxies expected json from the API for base study info"""
        study_info = Study.get_info([study.id])[0]

        pi = StudyPerson(study_info["principal_investigator_id"])
        study_info["principal_investigator"] = '%s (%s)' % (
            pi.name, pi.affiliation)
        del study_info["principal_investigator_id"]

        lab_person = StudyPerson(study_info["lab_person_id"])
        study_info["lab_person"] = '%s (%s)' % (
            lab_person.name, lab_person.affiliation)
        del study_info["lab_person_id"]
        samples = study.sample_template.keys()
        study_info['num_samples'] = 0 if samples is None else len(set(samples))
        return study_info

    @authenticated
    def get(self):
        sid = self.get_argument('study_id')
        study = Study(_to_int(sid))
        check_access(self.current_user, study, raise_error=True)
        study_info = self.study_info_proxy(study)
        self.render('study_description_templates/base_info.html',
                    study_info=study_info)
