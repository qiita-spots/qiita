# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from json import loads
from time import sleep

from qiita_core.qiita_settings import r_client

from qiita_db.processing_job import ProcessingJob


def wait_for_prep_information_job(prep_id, raise_if_none=True):
    """Waits until a prep information job is completed

    Parameters
    ----------
    prep_id : int
        Prep template id
    raise_if_none : bool, optional
        If True, raise an AssertionError if the correspondent redis key
        is empty. Default: True

    Raises
    ------
    AssertionError
        If `raise_if_none` is True and the correspondent redis key is not set
    """
    res = r_client.get('prep_template_%d' % prep_id)

    if raise_if_none and res is None:
        raise AssertionError("unexpectedly None")

    if res is not None:
        payload = loads(res)
        job_id = payload['job_id']
        wait_for_processing_job(job_id)


def wait_for_processing_job(job_id):
    """Waits until a processing job is completed

    Parameters
    ----------
    job_id : str
        Job id
    """
    job = ProcessingJob(job_id)
    while job.status not in ('success', 'error'):
        sleep(0.8)
    # this print is useful for debugging
    if job.status == 'error':
        print("==> %s: %s" % (job.id, job.log.msg))
    sleep(0.8)
