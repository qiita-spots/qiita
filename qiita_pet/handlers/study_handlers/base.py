# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------
from markdown2 import Markdown
from tornado.escape import json_decode
from tornado.web import HTTPError, authenticated

from qiita_pet.handlers.api_proxy import (
    study_delete_req,
    study_files_get_req,
    study_get_req,
    study_get_tags_request,
    study_patch_request,
    study_prep_get_req,
    study_tags_request,
)
from qiita_pet.handlers.base_handlers import BaseHandler
from qiita_pet.handlers.util import doi_linkifier, pubmed_linkifier, to_int
from qiita_pet.util import EBI_LINKIFIER


class StudyIndexHandler(BaseHandler):
    @authenticated
    def get(self, study_id):
        study = to_int(study_id)
        level = self.get_argument("level", "")
        message = self.get_argument("message", "")
        prep_id = self.get_argument("prep_id", default=None)

        study_info = study_get_req(study, self.current_user.id)
        if study_info["status"] != "success":
            raise HTTPError(404, reason=study_info["message"])

        if message != "" and level != "":
            study_info["level"] = level
            study_info["message"] = message

        if prep_id:
            msg = f"'{prep_id}' is not a valid preparation for this study"
            study_info["study_info"]["prep_id"] = to_int(prep_id, msg)

            # prep_id is an integer - confirm that it's a valid prep_id.
            prep_info = study_prep_get_req(study, self.current_user.id)
            if prep_info["status"] != "success":
                raise HTTPError(404, reason=prep_info["message"])

            prep_ids = []
            for prep_type in prep_info["info"]:
                # prep_type will be either '18S', '16S', or similarly named.
                # generate a list of prep-ids from the preps in each list.
                prep_ids += [x["id"] for x in prep_info["info"][prep_type]]

            if study_info["study_info"]["prep_id"] not in prep_ids:
                raise HTTPError(
                    400,
                    reason=(f"'{prep_id}' is not a valid preparation for this study"),
                )

        self.render("study_base.html", **study_info)


class StudyBaseInfoAJAX(BaseHandler):
    @authenticated
    def get(self):
        study_id = self.get_argument("study_id")
        study = to_int(study_id)
        res = study_get_req(study, self.current_user.id)
        study_info = res["study_info"]
        pdoi = [doi_linkifier([p]) for p in study_info["publication_doi"]]
        ppid = [pubmed_linkifier([p]) for p in study_info["publication_pid"]]

        email = '<a href="mailto:{email}">{name} ({affiliation})</a>'
        pi = email.format(**study_info["principal_investigator"])
        if study_info["lab_person"]:
            contact = email.format(**study_info["lab_person"])
        else:
            contact = None
        share_access = (
            self.current_user.id in study_info["shared_with"]
            or self.current_user.id == study_info["owner"]
        )

        ebi_info = study_info["ebi_submission_status"]
        ebi_study_accession = study_info["ebi_study_accession"]
        if ebi_study_accession:
            links = "".join(
                [EBI_LINKIFIER.format(a) for a in ebi_study_accession.split(",")]
            )
            ebi_info = "%s (%s)" % (links, study_info["ebi_submission_status"])

        markdowner = Markdown()
        study_info["notes"] = markdowner.convert(study_info["notes"])

        self.render(
            "study_ajax/base_info.html",
            study_info=study_info,
            publications=", ".join(pdoi + ppid),
            pi=pi,
            contact=contact,
            editable=res["editable"],
            share_access=share_access,
            ebi_info=ebi_info,
        )


class StudyDeleteAjax(BaseHandler):
    @authenticated
    def post(self):
        study_id = self.get_argument("study_id")
        self.write(study_delete_req(int(study_id), self.current_user.id))


class DataTypesMenuAJAX(BaseHandler):
    @authenticated
    def get(self):
        study_id = to_int(self.get_argument("study_id"))
        # Retrieve the prep template information for the menu
        prep_info = study_prep_get_req(study_id, self.current_user.id)
        # Make sure study exists
        if prep_info["status"] != "success":
            raise HTTPError(404, reason=prep_info["message"])

        prep_info = prep_info["info"]

        self.render(
            "study_ajax/data_type_menu.html", prep_info=prep_info, study_id=study_id
        )


class StudyFilesAJAX(BaseHandler):
    @authenticated
    def get(self):
        study_id = to_int(self.get_argument("study_id"))
        atype = self.get_argument("artifact_type")
        pt_id = self.get_argument("prep_template_id")

        res = study_files_get_req(self.current_user.id, study_id, pt_id, atype)

        self.render("study_ajax/artifact_file_selector.html", **res)


class StudyGetTags(BaseHandler):
    @authenticated
    def get(self):
        response = study_tags_request()
        self.write(response)


class StudyTags(BaseHandler):
    @authenticated
    def get(self, study_id):
        study_id = to_int(study_id)

        response = study_get_tags_request(self.current_user.id, study_id)
        self.write(response)


class Study(BaseHandler):
    @authenticated
    def patch(self, study_id):
        """Patches a study in the system

        Follows the JSON PATCH specification:
        https://tools.ietf.org/html/rfc6902
        """
        study_id = to_int(study_id)
        data = json_decode(self.request.body)

        req_op = data.get("op")
        req_path = data.get("path")
        req_value = data.get("value")
        req_from = data.get("from", None)

        response = study_patch_request(
            self.current_user.id, study_id, req_op, req_path, req_value, req_from
        )
        self.write(response)
