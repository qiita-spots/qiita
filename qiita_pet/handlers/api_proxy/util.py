from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_db.study import Study
from qiita_db.user import User


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
