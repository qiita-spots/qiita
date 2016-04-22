# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from os.path import join, basename

from json import loads

from biom import load_table
from biom.util import biom_open
from biom.exception import TableException


def validate(qclient, job_id, parameters, out_dir):
    """Validate and fix a new BIOM artifact

    Parameters
    ----------
    qclient : qiita_client.QiitaClient
        The Qiita server client
    job_id : str
        The job id
    parameters : dict
        The parameter values to validate and create the artifact
    out_dir : str
        The path to the job's output directory

    Returns
    -------
    bool, list of (str, str, list of (str, str)) , str
        Whether the job is successful
        The artifact information, if successful
        The error message, if not successful
    """
    prep_id = parameters['template']
    files = loads(parameters['files'])
    a_type = parameters['artifact_type']

    if a_type != "BIOM":
        return (False, None, "Unknown artifact type %s. Supported types: BIOM"
                             % a_type)

    qclient.update_job_step(job_id, "Step 1: Collecting prep information")
    prep_info = qclient.get("/qiita_db/prep_template/%s/data" % prep_id)
    prep_info = prep_info['data']

    # Check if the biom table has the same sample ids as the prep info
    qclient.update_job_step(job_id, "Step 2: Validting BIOM file")
    new_biom_fp = biom_fp = files['BIOM'][0]
    table = load_table(biom_fp)
    pt_sample_ids = set(prep_info)
    biom_sample_ids = set(table.ids())

    if not pt_sample_ids.issuperset(biom_sample_ids):
        # The BIOM sample ids are different from the ones in the prep template
        qclient.update_job_step(job_id, "Step 3: Fixing BIOM sample ids")
        # Attempt 1: the user provided the run prefix column - in this case
        # the run prefix column holds the sample ids present in the BIOM file
        if 'run_prefix' in prep_info[next(iter(pt_sample_ids))]:
            id_map = {v['run_prefix']: k for k, v in prep_info.items()}
        else:
            # Attemp 2: the sample ids in the BIOM table are the same that in
            # the prep template but without the prefix
            prefix = next(iter(pt_sample_ids)).split('.', 1)[0]
            prefixed = set("%s.%s" % (prefix, s) for s in biom_sample_ids)
            if pt_sample_ids.issuperset(prefixed):
                id_map = {s: "%s.%s" % (prefix, s) for s in biom_sample_ids}
            else:
                # There is nothing we can do. The samples in the BIOM table do
                # not match the ones in the prep template and we can't fix it
                error_msg = ('The sample ids in the BIOM table do not match '
                             'the ones in the prep information. Please, '
                             'provide the column "run_prefix" in the prep '
                             'information to map the existing sample ids to '
                             'the prep information sample ids.')
                return False, None, error_msg

        # Fix the sample ids
        try:
            table.update_ids(id_map, axis='sample')
        except TableException:
            missing = biom_sample_ids - set(id_map)
            error_msg = ('Your prep information is missing samples that are '
                         'present in your BIOM table: %s' % ', '.join(missing))
            return False, None, error_msg

        new_biom_fp = join(out_dir, basename(biom_fp))
        with biom_open(new_biom_fp, 'w') as f:
            table.to_hdf5(f, "Qiita BIOM type plugin")

    return True, [[None, 'BIOM', [new_biom_fp, 'biom']]], ""
