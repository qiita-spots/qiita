# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from tornado.gen import coroutine
from tornado.web import HTTPError

from qiita_core.util import execute_as_transaction
from qiita_db.artifact import Artifact
from qiita_db.exceptions import QiitaDBUnknownIDError
from qiita_db.study import Study
from qiita_db.util import get_artifacts_information
from qiita_pet.handlers.util import doi_linkifier, pubmed_linkifier
from qiita_pet.util import EBI_LINKIFIER

from .base_handlers import BaseHandler


class PublicHandler(BaseHandler):
    @coroutine
    @execute_as_transaction
    def get(self):
        study_id = self.get_argument("study_id", None)
        artifact_id = self.get_argument("artifact_id", None)

        if study_id is None and artifact_id is None:
            raise HTTPError(422, reason="You need to specify study_id or artifact_id")
            self.finish()
        elif study_id is not None:
            try:
                study = Study(int(study_id))
            except QiitaDBUnknownIDError:
                raise HTTPError(422, reason="Study %s doesn't exist" % study_id)
                self.finish()
            artifact_ids = [a.id for a in study.artifacts() if a.visibility == "public"]
        else:
            try:
                artifact = Artifact(int(artifact_id))
            except QiitaDBUnknownIDError:
                raise HTTPError(422, reason="Artifact %s doesn't exist" % artifact_id)
                self.finish()
            if artifact.visibility != "public":
                raise HTTPError(422, reason="Artifact %s is not public" % artifact_id)
                self.finish()

            study = artifact.study
            if study is None:
                raise HTTPError(
                    422, reason="Artifact %s doesn't belong to a study" % artifact_id
                )
                self.finish()
            artifact_ids = [artifact.id]

        if study.status != "public":
            raise HTTPError(422, reason="Not a public study")
            self.finish()

        study_info = study.info
        study_info["study_id"] = study.id
        study_info["study_title"] = study.title
        study_info["shared_with"] = [s.id for s in study.shared_with]
        study_info["status"] = study.status
        study_info["ebi_study_accession"] = study.ebi_study_accession
        study_info["ebi_submission_status"] = study.ebi_submission_status

        # Clean up StudyPerson objects to string for display
        email = '<a href="mailto:{email}">{name} ({affiliation})</a>'
        pi = study.info["principal_investigator"]
        study_info["principal_investigator"] = email.format(
            **{"name": pi.name, "email": pi.email, "affiliation": pi.affiliation}
        )

        study_info["owner"] = study.owner.id
        # Add needed info that is not part of the initial info pull
        study_info["publications"] = []
        for pub, is_doi in study.publications:
            if is_doi:
                study_info["publications"].append(pubmed_linkifier([pub]))
            else:
                study_info["publications"].append(doi_linkifier([pub]))
        study_info["publications"] = ", ".join(study_info["publications"])

        if study_info["ebi_study_accession"]:
            links = "".join(
                [
                    EBI_LINKIFIER.format(a)
                    for a in study_info["ebi_study_accession"].split(",")
                ]
            )
            study_info["ebi_study_accession"] = "%s (%s)" % (
                links,
                study_info["ebi_submission_status"],
            )

        self.render(
            "public.html",
            study_info=study_info,
            artifacts_info=get_artifacts_information(artifact_ids, False),
        )
