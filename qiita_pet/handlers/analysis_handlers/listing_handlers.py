# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from collections import defaultdict
from functools import partial
from json import dumps, loads

from tornado.web import authenticated

from qiita_core.qiita_settings import qiita_config, r_client
from qiita_core.util import execute_as_transaction
from qiita_db.analysis import Analysis
from qiita_db.artifact import Artifact
from qiita_db.processing_job import ProcessingJob
from qiita_db.software import Parameters, Software
from qiita_db.util import generate_analysis_list
from qiita_pet.handlers.analysis_handlers import check_analysis_access
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.util import download_link_or_path
from qiita_pet.util import is_localhost


class ListAnalysesHandler(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self):
        user = self.current_user
        is_local_request = is_localhost(self.request.headers["host"])

        uanalyses = user.shared_analyses | user.private_analyses
        user_analysis_ids = set([a.id for a in uanalyses])

        panalyses = Analysis.get_by_status("public")
        public_analysis_ids = set([a.id for a in panalyses])
        public_analysis_ids = public_analysis_ids - user_analysis_ids

        user_analyses = generate_analysis_list(user_analysis_ids)
        public_analyses = generate_analysis_list(public_analysis_ids, True)

        dlop = partial(download_link_or_path, is_local_request)

        messages = {"info": "", "danger": ""}
        for analysis_id in user_analysis_ids:
            job_info = r_client.get("analysis_delete_%d" % analysis_id)
            if job_info:
                job_info = defaultdict(lambda: "", loads(job_info))
                job_id = job_info["job_id"]
                job = ProcessingJob(job_id)
                job_status = job.status
                processing = job_status not in ("success", "error")
                if processing:
                    messages["info"] += (
                        "Analysis %s is being deleted<br/>" % analysis_id
                    )
                elif job_status == "error":
                    messages["danger"] += job.log.msg.replace("\n", "<br/>") + "<br/>"
                else:
                    if job_info["alert_type"] not in messages:
                        messages[job_info["alert_type"]] = []
                    messages[job_info["alert_type"]] += (
                        job.log.msg.replace("\n", "<br/>") + "<br/>"
                    )

        self.render(
            "list_analyses.html",
            user_analyses=user_analyses,
            public_analyses=public_analyses,
            messages=messages,
            dlop=dlop,
        )

    @authenticated
    @execute_as_transaction
    def post(self):
        analysis_id = int(self.get_argument("analysis_id"))

        user = self.current_user
        check_analysis_access(user, Analysis(analysis_id))

        qiita_plugin = Software.from_name_and_version("Qiita", "alpha")
        cmd = qiita_plugin.get_command("delete_analysis")
        params = Parameters.load(cmd, values_dict={"analysis_id": analysis_id})
        job = ProcessingJob.create(user, params, True)
        # Store the job id attaching it to the sample template id
        r_client.set("analysis_delete_%d" % analysis_id, dumps({"job_id": job.id}))
        job.submit()

        self.redirect("%s/analysis/list/" % (qiita_config.portal_dir))


class AnalysisSummaryAJAX(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self):
        info = self.current_user.default_analysis.summary_data()
        self.write(dumps(info))


class SelectedSamplesHandler(BaseHandler):
    @authenticated
    @execute_as_transaction
    def get(self):
        # Format sel_data to get study IDs for the processed data
        sel_data = defaultdict(dict)
        proc_data_info = {}
        analysis = self.current_user.default_analysis
        for aid, samples in analysis.samples.items():
            artifact = Artifact(aid)
            sel_data[artifact.study][aid] = samples
            proc_data_info[aid] = {
                "processed_date": str(artifact.timestamp),
                "merging_scheme": artifact.merging_scheme,
                "data_type": artifact.data_type,
            }

        # finding common metadata fields
        metadata = analysis.metadata_categories
        common = {"sample": set(), "prep": set()}
        for i, (_, m) in enumerate(metadata.items()):
            svals = set(m["sample"])
            pvals = set(m["prep"])
            if i != 0:
                svals = common["sample"] & svals
                pvals = common["prep"] & pvals
            common["sample"] = svals
            common["prep"] = pvals

        self.render(
            "analysis_selected.html",
            sel_data=sel_data,
            proc_info=proc_data_info,
            metadata=metadata,
            common=common,
        )
