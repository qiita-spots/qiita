# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from tornado.gen import coroutine
from tornado.web import HTTPError

from .base_handlers import BaseHandler
from qiita_core.util import execute_as_transaction

from qiita_db.software import Software
from qiita_db.study import Study

from json import dumps
from collections import Counter


class AdminProcessingJobBaseClass(BaseHandler):
    def _check_access(self):
        if self.current_user is None or self.current_user.level not in {
                'admin', 'wet-lab admin'}:
            raise HTTPError(403, reason="User %s doesn't have sufficient "
                            "privileges to view error page" %
                            self.current_user.email)

        return self

    def _get_private_software(self):
        # skipping the internal Qiita plugin and only selecting private
        # commands
        private_software = [s for s in Software.iter()
                            if s.name != 'Qiita' and s.type == 'private']

        return private_software


class AdminProcessingJob(AdminProcessingJobBaseClass):
    @coroutine
    @execute_as_transaction
    def get(self):
        self._check_access()

        self.render("admin_processing_job.html",
                    private_software=self._get_private_software())


class AJAXAdminProcessingJobListing(AdminProcessingJobBaseClass):
    @coroutine
    @execute_as_transaction
    def get(self):
        self._check_access()
        echo = self.get_argument('sEcho')
        command_id = int(self.get_argument('commandId'))

        jobs = []
        for ps in self._get_private_software():
            for cmd in ps.commands:
                if cmd.id != command_id:
                    continue

                for job in cmd.processing_jobs:
                    if job.hidden:
                        continue
                    msg = ''
                    if job.status == 'error':
                        msg = job.log.msg
                    elif job.status == 'running':
                        msg = job.step
                    msg = msg.replace('\n', '</br>')
                    outputs = []
                    if job.status == 'success':
                        outputs = [[k, v.id] for k, v in job.outputs.items()]
                    validator_jobs = [v.id for v in job.validator_jobs]

                    if job.heartbeat is not None:
                        heartbeat = job.heartbeat.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        heartbeat = 'N/A'

                    jobs.append([job.id, job.command.name, job.status, msg,
                                 outputs, validator_jobs, heartbeat,
                                 job.parameters.values, job.external_id,
                                 job.user.email])
        results = {
            "sEcho": echo,
            "recordsTotal": len(jobs),
            "recordsFiltered": len(jobs),
            "data": jobs
        }

        # return the json in compact form to save transmit size
        self.write(dumps(results, separators=(',', ':')))


class SampleValidation(AdminProcessingJobBaseClass):
    @coroutine
    @execute_as_transaction
    def get(self):
        self._check_access()

        self.render("sample_validation.html", input=True)

    @execute_as_transaction
    def post(self):
        # Get user-inputted qiita id and sample names / tube_ids
        qid = self.get_argument("qid")
        snames = self.get_argument("snames").split()

        # Get study give qiita id
        study = Study(qid).sample_template

        # Stripping leading qiita id from sample names
        # Example: 1.SKB1.640202 -> SKB1.640202
        qsnames = list(study)
        for i, qsname in enumerate(qsnames):
            if qsname.startswith(qid):
                qsnames[i] = qsname.replace(f'{qid}.', "", 1)

        # Creates a way to access a tube_id by its corresponding sample name
        # and vice versa, which is important to adding tube_id in parentheses
        # after a sample name a few lines later
        tube_ids_lookup = dict()
        tube_ids_rev = dict()
        tube_ids = set()
        if "anonymized_name" in study.categories:
            for qsname, tid in study.get_category("anonymized_name").items():
                formatted_name = qsname
                if qsname.startswith(qid):
                    formatted_name = qsname.replace(f'{qid}.', "", 1)

                tube_ids.add(tid)
                tube_ids_lookup[formatted_name] = tid
                tube_ids_rev[tid] = formatted_name

        # Adds tube ids after sample name in parentheses
        if len(tube_ids) > 0:
            for i, sname in enumerate(snames):
                if sname in qsnames:
                    snames[i] = f'{sname} ({tube_ids_lookup[sname]})'
                elif sname in tube_ids:
                    snames[i] = f'{tube_ids_rev[sname]} ({sname})'

        # Finds duplicates in the samples
        seen = Counter()
        for sample in snames:
            seen[sample] += 1
        duplicates = [f'{s} \u00D7 {seen[s]}' for s in seen if seen[s] > 1]

        # Remove blank samples from sample names
        blank = set([x for x in snames if x.lower().startswith('blank')])
        snames = [x for x in snames if 'blank' not in x.lower()]

        # Validate user's sample names against qiita study
        if len(tube_ids) == 0:
            qsnames = set(qsnames)
        else:
            qsnames = set([f'{x} ({tube_ids_lookup[x]})' for x in qsnames])
        snames = set(snames)
        matching = qsnames.intersection(snames)
        missing = qsnames.difference(snames)
        extra = snames.difference(qsnames)

        self.render("sample_validation.html", input=False, matching=matching,
                    missing=missing, extra=extra, blank=blank,
                    duplicates=duplicates)
