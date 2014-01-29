#!/usr/bin/env python

__author__ = "Jose Antonio Navas Molina"
__copyright__ = "Copyright 2013, The Qiita Project"
__credits__ = ["Jose Antonio Navas Molina", "Joshua Shorenstein"]
__license__ = "BSD"
__version__ = "0.1.0-dev"
__maintainer__ = "Jose Antonio Navas Molina"
__email__ = "josenavasmolina@gmail.edu"
__status__ = "Development"


def create_user(email, password, **kwargs):
    """ Creates a new user in the system

    Inputs:
        email: the user's email
        password: the user password
        kwargs: extra user information

    Returns:
        The new QiitaUser object

    Checks:
        - Valid user_id
        - user_id already exists
        - Valid password
        - Valid email

    Raises an error if something went wrong
    """
    raise NotImplementedError("qiita_ware.api.user_manager: create_user")


def update_user(user):
    """ Updates the user information in the system

    Inputs:
        user: a QiitaUser object

    Does not perform any check - assumed to be included on the QiitaUser obj
    Raises an error if something went wrong
    """
    raise NotImplementedError("qiita_ware.api.user_manager: update_user")


def delete_user(user_id, password, rm_shared_analysis=False,
                rm_shared_studies=False):
    """ Deletes the user_id from the system

    Inputs:
        user_id: user id of the user to remove
        password: password of the user
        rm_shared_analysis: if true remove the shared analysis own by the user
        rm_shared_studies: if true remove the shared studies own by the user

    Checks:
        - user credentials (user_id, password)

    Removes the user with user_id=user_id and its associated private analyses
        and studies. If the flags rm_shared_analysis and rm_shared_studies are
        set to true, it also removes the shared studies in which the user is
        the owner.

    Raises an error if something went wrong
    """
    raise NotImplementedError("qiita_ware.api.user_manager: delete_user")


def get_user(user_id):
    """ Retrieves the QiitaUser object for the user_id

    Inputs:
        user_id: the user_id of the QiitaUser object to be retrieved

    Returns:
        The QiitaUser object for the user user_id

    Raises a UserNotExistsError if user_id is not in the system
    """
    raise NotImplementedError("qiita_ware.api.user_manager: get_user")


def get_all_users():
    """ Gets a list with all users

    Inputs: None

    Result:
        A list with the QiitaUser obj of all users in the system

    Raises an error if something went wrong
    """
    raise NotImplementedError("qiita_ware.api.user_manager: get_all_users")


def search_users(user_id_hint, **kwargs):
    """ Retrieves all the users in the system that match the search query

    Inputs:
        user_id_hint: string with a partial user id
        kwargs: extra user information

    Returns:
        A list with the QiitaUser obj of all users in the system that match
            the search query

    Raises an error if something went wrong
    """
    raise NotImplementedError("qiita_ware.api.user_manager: search_user")


def check_password(user_id, password):
    """ Checks if password is correct for user_id

    Inputs:
        user_id: the user id
        password: the password to check

    Returns:
        Bool: the password is correct or not

    Raises a UserNotExistsError if user_id is not in the system
    """
    raise NotImplementedError("qiita_ware.api.user_manager: check_password")


def change_password(user_id, old_pwd, new_pwd):
    """ Changes the password of user_id to new_pwd

    Inputs:
        user_id: the user_id of the user to change the password
        old_pwd: the old password of user_id
        new_pwd: the new password of user_id

    Checks:
        - user credentials (user_id, old_pwd)
        - Valid new_pwd

    Raises an error if something went wrong
    """
    raise NotImplementedError("qiita_ware.api.user_manager: change_password")


def reset_password(user_id):
    """ Resets the password of user_id

    Inputs:
        user_id: the user_id of the user to reset the password

    Raises a UserNotExistsError if user_id is not in the system
    Raises an error if something went wrong
    """
    raise NotImplementedError("qiita_ware.api.user_manager: reset_password")


def change_user_level(admin_id, admin_pwd, user_id, new_level):
    """ Changes the level of user_id to be new_level

    Inputs:
        admin_id: the admin user that makes the change
        admin_pwd: the admin password to verify credentials
        user_id: the user_id of the user to change the level
        new_level: the new user level of the user

    Checks:
        - admin credentials (admin_id, admin_pwd)
        - check user_id exists
        - check new_level is a valid level

    Raises an error if something went wrong
    """
    raise NotImplementedError("qiita_ware.api.user_manager: change_user_level")
