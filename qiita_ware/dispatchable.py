# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------


def update_sample_template(study_id, fp):
    """Updates a sample template

    Parameters
    ----------
    study_id : int
        Study id whose template is going to be updated
    fp : str
        The file path to the template file

    Returns
    -------
    dict of {str: str}
        A dict of the form {'status': str, 'message': str}
    """
    import warnings
    from os import remove
    from qiita_db.metadata_template.util import load_template_to_dataframe
    from qiita_db.metadata_template.sample_template import SampleTemplate

    msg = ''
    status = 'success'

    try:
        with warnings.catch_warnings(record=True) as warns:
            # deleting previous uploads and inserting new one
            st = SampleTemplate(study_id)
            df = load_template_to_dataframe(fp)
            st.extend_and_update(df)
            remove(fp)

            # join all the warning messages into one. Note that this info
            # will be ignored if an exception is raised
            if warns:
                msg = '\n'.join(set(str(w.message) for w in warns))
                status = 'warning'
    except Exception as e:
            status = 'danger'
            msg = str(e)

    return {'status': status, 'message': msg}


def delete_sample_template(study_id):
    """Delete a sample template

    Parameters
    ----------
    study_id : int
        Study id whose template is going to be deleted

    Returns
    -------
    dict of {str: str}
        A dict of the form {'status': str, 'message': str}
    """
    from qiita_db.metadata_template.sample_template import SampleTemplate

    msg = ''
    status = 'success'
    try:
        SampleTemplate.delete(study_id)
    except Exception as e:
        status = 'danger'
        msg = str(e)

    return {'status': status, 'message': msg}


def update_prep_template(prep_id, fp):
    """Updates a prep template

    Parameters
    ----------
    prep_id : int
        Prep template id to be updated
    fp : str
        The file path to the template file

    Returns
    -------
    dict of {str: str}
        A dict of the form {'status': str, 'message': str}
    """
    import warnings
    from os import remove
    from qiita_db.metadata_template.util import load_template_to_dataframe
    from qiita_db.metadata_template.prep_template import PrepTemplate

    msg = ''
    status = 'success'

    prep = PrepTemplate(prep_id)

    try:
        with warnings.catch_warnings(record=True) as warns:
            df = load_template_to_dataframe(fp)
            prep.extend(df)
            prep.update(df)
            remove(fp)

            if warns:
                msg = '\n'.join(set(str(w.message) for w in warns))
                status = 'warning'
    except Exception as e:
            status = 'danger'
            msg = str(e)

    return {'status': status, 'message': msg}


def delete_sample_or_column(obj_class, obj_id, sample_or_col, name):
    """Deletes a sample or a column from the metadata

    Parameters
    ----------
    obj_class : {SampleTemplate, PrepTemplate}
        The metadata template subclass
    obj_id : int
        The template id
    sample_or_col : {"samples", "columns"}
        Which resource are we deleting. Either "samples" or "columns"
    name : str
        The name of the resource to be deleted

    Returns
    -------
    dict of {str: str}
        A dict of the form {'status': str, 'message': str}
    """
    st = obj_class(obj_id)

    if sample_or_col == 'columns':
        del_func = st.delete_column
    elif sample_or_col == 'samples':
        del_func = st.delete_sample
    else:
        return {'status': 'danger',
                'message': 'Unknown value "%s". Choose between "samples" '
                           'and "columns"' % sample_or_col}

    msg = ''
    status = 'success'

    try:
        del_func(name)
    except Exception as e:
        status = 'danger'
        msg = str(e)

    return {'status': status, 'message': msg}
