# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from collections import Counter
from json import dumps

from tornado.gen import coroutine
from tornado.web import HTTPError

from qiita_core.util import execute_as_transaction
from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_db.processing_job import ProcessingJob as PJ
from qiita_db.software import Software
from qiita_db.sql_connection import TRN
from qiita_db.study import Study

from .base_handlers import BaseHandler


class AdminProcessingJobBaseClass(BaseHandler):
    def _check_access(self):
        if self.current_user is None or self.current_user.level not in {
            "admin",
            "wet-lab admin",
        }:
            raise HTTPError(
                403,
                reason="User %s doesn't have sufficient "
                "privileges to view error page" % self.current_user.email,
            )

        return self

    def _get_private_software(self):
        # skipping the internal Qiita plugin and only selecting private
        # commands
        private_software = [
            s for s in Software.iter() if s.name != "Qiita" and s.type == "private"
        ]

        return private_software


class AdminProcessingJob(AdminProcessingJobBaseClass):
    @coroutine
    @execute_as_transaction
    def get(self):
        self._check_access()

        self.render(
            "admin_processing_job.html", private_software=self._get_private_software()
        )


class AJAXAdminProcessingJobListing(AdminProcessingJobBaseClass):
    @coroutine
    @execute_as_transaction
    def get(self):
        self._check_access()
        echo = self.get_argument("sEcho")
        command_id = int(self.get_argument("commandId"))

        with TRN:
            # different versions of the same plugin will have different
            # command_id, this will make sure to get them all (commands)
            sql = """SELECT processing_job_id FROM qiita.processing_job
                     WHERE hidden = false and command_id in (
                        SELECT command_id FROM qiita.software_command
                        WHERE
                            name in (
                                SELECT name FROM qiita.software_command
                                WHERE command_id = %s)) AND
                            (heartbeat > current_date - interval '14' day OR
                             heartbeat is NULL)"""
            TRN.add(sql, [command_id])
            jids = TRN.execute_fetchflatten()

        jobs = []
        for jid in jids:
            job = PJ(jid)
            msg = ""
            if job.status == "error":
                msg = job.log.msg
            elif job.status == "running":
                msg = job.step
            if msg is not None:
                msg = msg.replace("\n", "</br>")
            outputs = []
            if job.status == "success":
                outputs = [[k, v.id] for k, v in job.outputs.items()]
            validator_jobs = [v.id for v in job.validator_jobs]

            if job.heartbeat is not None:
                heartbeat = job.heartbeat.strftime("%Y-%m-%d %H:%M:%S")
            else:
                heartbeat = "N/A"

            jobs.append(
                [
                    job.id,
                    job.command.name,
                    job.status,
                    msg,
                    outputs,
                    validator_jobs,
                    heartbeat,
                    job.parameters.values,
                    job.external_id,
                    job.user.email,
                ]
            )
        results = {
            "sEcho": echo,
            "recordsTotal": len(jobs),
            "recordsFiltered": len(jobs),
            "data": jobs,
        }

        # return the json in compact form to save transmit size
        self.write(dumps(results, separators=(",", ":")))


class SampleValidation(AdminProcessingJobBaseClass):
    @coroutine
    @execute_as_transaction
    def get(self):
        self._check_access()

        self.render("sample_validation.html", input=True, error=None)

    @execute_as_transaction
    def post(self):
        # Get user-inputted qiita id and sample names
        qid = self.get_argument("qid")
        snames = self.get_argument("snames").split()
        error, matching, missing, extra, blank, duplicates = [None] * 6

        # Stripping leading qiita id from sample names
        # Example: 1.SKB1.640202 -> SKB1.640202
        try:
            sample_info = Study(qid).sample_template
            qsnames = list(sample_info)
        except TypeError:
            error = f"Study {qid} seems to have no sample template"
        except QiitaDBUnknownIDError:
            error = f"Study {qid} does not exist"

        if error is None:
            # if tube_id is present then this should take precedence in qsnames
            tube_ids = dict()
            if "tube_id" in sample_info.categories:
                for k, v in sample_info.get_category("tube_id").items():
                    # ignoring empty values
                    if v in (None, "None", ""):
                        continue
                    if k.startswith(qid):
                        k = k.replace(f"{qid}.", "", 1)
                    tube_ids[k] = v

            for i, qsname in enumerate(qsnames):
                if qsname.startswith(qid):
                    qsname = qsname.replace(f"{qid}.", "", 1)
                if qsname in tube_ids:
                    nname = f"{qsname}, tube_id: {tube_ids[qsname]}"
                    snames = [s if s != tube_ids[qsname] else nname for s in snames]
                    qsname = nname
                qsnames[i] = qsname

            # Finds duplicates in the samples
            seen = Counter(snames)
            duplicates = [f"{s} \u00d7 {seen[s]}" for s in seen if seen[s] > 1]

            # Remove blank samples from sample names
            blank = [x for x in snames if x.lower().startswith("blank")]
            snames = set(snames) - set(blank)

            # Validate user's sample names against qiita study
            qsnames = set(qsnames)
            snames = set(snames)
            matching = qsnames.intersection(snames)
            missing = qsnames.difference(snames)
            extra = snames.difference(qsnames)

        self.render(
            "sample_validation.html",
            input=False,
            matching=matching,
            missing=missing,
            extra=extra,
            blank=blank,
            duplicates=duplicates,
            error=error,
        )
