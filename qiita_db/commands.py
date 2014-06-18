from functools import partial
try:
    # Python 2
    from ConfigParser import ConfigParser
except ImportError:
    # Python 3
    from configparser import ConfigParser

from qiita_db.study import Study, StudyPerson
from qiita_db.user import User


def make_study_from_cmd(owner, title, info):

    # Parse the configuration file
    config = ConfigParser()
    config.readfp(info)

    optional = dict(config.items('optional'))
    get_optional = lambda name: optional.get(name, None)
    get_required = partial(config.get, 'required')
    infodict = {}
    infodict['funding'] = get_optional('funding')
    infodict['timeseries_type_id'] = get_required('timeseries_type_id')
    infodict['metadata_complete'] = get_required('metadata_complete')
    infodict['mixs_compliant'] = get_required('mixs_compliant')
    infodict['most_recent_contact'] = get_optional('most_recent_contact')
    infodict['number_samples_collected'] = get_required(
        'number_samples_collected')
    infodict['number_samples_promised'] = get_required(
        'number_samples_promised')
    infodict['portal_type_id'] = get_required('portal_type_id')
    infodict['reprocess'] = get_required('reprocess')
    infodict['spatial_series'] = get_optional('spatial_series')
    infodict['study_alias'] = get_required('study_alias')
    infodict['study_description'] = get_required('study_description')
    infodict['study_abstract'] = get_required('study_abstract')
    infodict['vamps_id'] = get_optional('vamps_id')
    emp_person_name_email = get_optional('emp_person_name')
    if emp_person_name_email is not None:
        emp_name, emp_email = emp_person_name_email.split(',')
        infodict['emp_person_id'] = StudyPerson.create(emp_name.strip(),
                                                       emp_email.strip())
    lab_name_email = get_optional('lab_person')
    if lab_name_email is not None:
        lab_name, lab_email = lab_name_email.split(',')
        print lab_name
        print lab_email
        infodict['lab_person_id'] = StudyPerson.create(lab_name.strip(),
                                                       lab_email.strip())
    pi_name_email = get_required('principal_investigator')
    pi_name, pi_email = pi_name_email.split(',')
    infodict['principal_investigator_id'] = StudyPerson.create(
        pi_name.strip(), pi_email.strip())
    # this will eventually change to using the Experimental Factory Ontolgoy
    # names
    efo_ids = get_required('efo_ids')
    efo_ids = [x.strip() for x in efo_ids.split(',')]

    Study.create(User(owner), title, efo_ids, infodict)
