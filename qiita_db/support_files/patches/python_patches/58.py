# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from json import loads, dumps

from qiita_core.qiita_settings import r_client
from qiita_db.sql_connection import TRN
from qiita_db.software import Software, Command, Parameters
from qiita_db.processing_job import ProcessingJob
from qiita_db.study import Study
from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_db.metadata_template.prep_template import PrepTemplate


def correct_redis_data(key, cmd, values_dict, user):
    """Corrects the data stored in the redis DB

    Parameters
    ----------
    key: str
        The redis key to fix
    cmd : qiita_db.software.Command
        Command to use to create the processing job
    values_dict : dict
        Dictionary used to instantiate the parameters of the command
    user : qiita_db.user. User
        The user that will own the job
    """
    info = r_client.get(key)
    if info:
        info = loads(info)
        if info['job_id'] is not None:
            if 'is_qiita_job' in info:
                if info['is_qiita_job']:
                    try:
                        job = ProcessingJob(info['job_id'])
                        payload = {'job_id': info['job_id'],
                                   'alert_type': info['status'],
                                   'alert_msg': info['alert_msg']}
                        r_client.set(key, dumps(payload))
                    except (QiitaDBUnknownIDError, KeyError):
                        # We shomehow lost the information of this job
                        # Simply delete the key
                        r_client.delete(key)
                else:
                    # These jobs don't contain any information on the live
                    # dump. We can safely delete the key
                    r_client.delete(key)
            else:
                # These jobs don't contain any information on the live
                # dump. We can safely delete the key
                r_client.delete(key)
        else:
            # Job is null, we have the information here
            if info['status'] == 'success':
                # In the success case no information is stored. We can
                # safely delete the key
                r_client.delete(key)
            elif info['status'] == 'warning':
                # In case of warning the key message stores the warning
                # message. We need to create a new job, mark it as
                # successful and store the error message as expected by
                # the new structure
                params = Parameters.load(cmd, values_dict=values_dict)
                job = ProcessingJob.create(user, params)
                job._set_status('success')
                payload = {'job_id': job.id,
                           'alert_type': 'warning',
                           'alert_msg': info['message']}
                r_client.set(key, dumps(payload))
            else:
                # The status is error. The key message stores the error
                # message. We need to create a new job and mark it as
                # failed with the given error message
                params = Parameters.load(cmd, values_dict=values_dict)
                job = ProcessingJob.create(user, params)
                job._set_error(info['message'])
                payload = {'job_id': job.id}
                r_client.set(key, dumps(payload))
    else:
        # The key doesn't contain any information. Delete the key
        r_client.delete(key)


with TRN:
    # Retrieve the Qiita plugin
    qiita_plugin = Software.from_name_and_version('Qiita', 'alpha')

    # Create the submit command for VAMPS command
    parameters = {'artifact': ['integer', None]}
    Command.create(qiita_plugin, "submit_to_VAMPS",
                   "submits an artifact to VAMPS", parameters)

    # Create the copy artifact command
    parameters = {'artifact': ['integer', None],
                  'prep_template': ['prep_template', None]}
    Command.create(qiita_plugin, "copy_artifact",
                   "Creates a copy of an artifact", parameters)

    # Create the submit command for EBI command
    parameters = {'artifact': ['integer', None],
                  'submission_type': ['choice:["ADD", "MODIFY"]', 'ADD']}
    Command.create(qiita_plugin, "submit_to_EBI",
                   "submits an artifact to EBI", parameters)

    # Create the submit command for delete_artifact
    parameters = {'artifact': ['integer', None]}
    Command.create(qiita_plugin, "delete_artifact",
                   "Delete an artifact", parameters)

    # Create the submit command for create a sample template
    parameters = {
        'fp': ['string', None], 'study_id': ['integer', None],
        'is_mapping_file': ['boolean', True], 'data_type': ['string', None]}
    Command.create(qiita_plugin, "create_sample_template",
                   "Create a sample template", parameters)

    # Create the update sample template command
    parameters = {'study': ['integer', None], 'template_fp': ['string', None]}
    st_cmd = Command.create(qiita_plugin, "update_sample_template",
                            "Updates the sample template", parameters)

    # Create the delete study command
    parameters = {'study': ['integer', None]}
    Command.create(qiita_plugin, "delete_study",
                   "Deletes a full study", parameters)

    # Create the delete sample template command
    parameters = {'study': ['integer', None]}
    Command.create(qiita_plugin, "delete_sample_template",
                   "Deletes a sample template", parameters)

    # Create the update prep template command
    parameters = {'prep_template': ['integer', None],
                  'template_fp': ['string', None]}
    pt_cmd = Command.create(qiita_plugin, "update_prep_template",
                            "Updates the prep template", parameters)

    # Create the delete sample or column command
    parameters = {
        'obj_class': ['choice:["SampleTemplate", "PrepTemplate"]', None],
        'obj_id': ['integer', None],
        'sample_or_col': ['choice:["samples", "columns"]', None],
        'name': ['string', None]}
    Command.create(qiita_plugin, "delete_sample_or_column",
                   "Deletes a sample or a columns from the metadata",
                   parameters)

    # Create the command to complete a job
    parameters = {'job_id': ['string', None], 'payload': ['string', None]}
    Command.create(qiita_plugin, "complete_job", "Completes a given job",
                   parameters)

    # Assumptions on the structure of the data in the redis database has
    # changed, we need to fix to avoid failures
    # Get all the sample template keys
    for key in r_client.keys('sample_template_[0-9]*'):
        try:
            study = Study(int(key.split('_')[-1]))
            user = study.owner
        except QiitaDBUnknownIDError:
            # This means that the study no longer exists - delete the key
            # and continue
            r_client.delete(key)
            continue
        values_dict = {'study': study.id, 'template_fp': 'ignored-patch58'}
        correct_redis_data(key, st_cmd, values_dict, user)

    # Get all the prep template keys
    for key in r_client.keys('prep_template_[0-9]*'):
        try:
            pt = PrepTemplate(int(key.split('_')[-1]))
            user = Study(pt.study_id).owner
        except QiitaDBUnknownIDError:
            # This means that the prep template no longer exists - delete the
            # key and continue
            r_client.delete(key)
            continue
        values_dict = {'prep_template': pt.id,
                       'template_fp': 'ignored-patch58'}
        correct_redis_data(key, pt_cmd, values_dict, user)
