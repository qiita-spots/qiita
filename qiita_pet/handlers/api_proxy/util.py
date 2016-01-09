# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from os.path import exists, join

from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_db.study import Study
from qiita_db.user import User
from qiita_db.util import get_mountpoint


def check_access(study_id, user_id):
    """Checks if user given has access to the study given

    Parameters
    ----------
    study_id : int
        ID of the study to check access to
    user_id : str
        ID of the user to check access for

    Returns
    -------
    dict
        Empty dict if access allowed, else a dict in the form
        {'status': 'error',
         'message': reason for error}

    """
    try:
        study = Study(int(study_id))
    except QiitaDBUnknownIDError:
        return {'status': 'error',
                'message': 'Study does not exist'}
    if not study.has_access(User(user_id)):
        return {'status': 'error',
                'message': 'User does not have access to study'}
    return {}


def check_fp(study_id, filename):
    """Check whether an uploaded file exists

    Parameters
    ----------
    study_id : int
        Study file uploaded to
    filename : str
        name of the uploaded file

    Returns
    -------
    dict or str
        dict if error, filepath as string if filepath exists
    """
    # Get the uploads folder
    _, base_fp = get_mountpoint("uploads")[0]
    # Get the path of the sample template in the uploads folder
    fp_rsp = join(base_fp, str(study_id), filename)

    if not exists(fp_rsp):
        # The file does not exist, fail nicely
        return {'status': 'error',
                'message': 'file does not exist',
                'file': filename}
    return fp_rsp
