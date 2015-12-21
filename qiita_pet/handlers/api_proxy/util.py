from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_db.study import Study
from qiita_db.user import User


def check_access(study_id, user_id):
    try:
        study = Study(int(study_id))
    except QiitaDBUnknownIDError:
        return {'status': 'error',
                'message': 'Study does not exist'}
    if not study.has_access(User(user_id)):
        return {'status': 'error',
                'message': 'User does not have access to study'}
    return {}
