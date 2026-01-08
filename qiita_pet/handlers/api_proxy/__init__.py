# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

# This is the only folder in qiita_pet that should import outside qiita_pet
# The idea is that this proxies the call and response dicts we expect from the
# Qiita API once we build it. This will be removed and replaced with API calls
# when the API is complete.
from .artifact import (
    artifact_get_info,
    artifact_get_prep_req,
    artifact_get_req,
    artifact_graph_get_req,
    artifact_post_req,
    artifact_status_put_req,
    artifact_types_get_req,
)
from .ontology import ontology_patch_handler
from .prep_template import (
    new_prep_template_get_req,
    prep_template_ajax_get_req,
    prep_template_delete_req,
    prep_template_filepaths_get_req,
    prep_template_get_req,
    prep_template_graph_get_req,
    prep_template_jobs_get_req,
    prep_template_patch_req,
    prep_template_post_req,
    prep_template_samples_get_req,
    prep_template_summary_get_req,
)
from .processing import (
    job_ajax_get_req,
    job_ajax_patch_req,
    list_commands_handler_get_req,
    list_options_handler_get_req,
    workflow_handler_patch_req,
    workflow_handler_post_req,
    workflow_run_post_req,
)
from .sample_template import (
    analyses_associated_with_study,
    get_sample_template_processing_status,
    sample_template_category_get_req,
    sample_template_filepaths_get_req,
    sample_template_get_req,
    sample_template_meta_cats_get_req,
    sample_template_samples_get_req,
)
from .studies import (
    data_types_get_req,
    study_delete_req,
    study_files_get_req,
    study_get_req,
    study_get_tags_request,
    study_patch_request,
    study_prep_get_req,
    study_tags_request,
)
from .user import user_jobs_get_req
from .util import check_access, check_fp

__version__ = "2026.01"

__all__ = [
    "prep_template_summary_get_req",
    "data_types_get_req",
    "study_get_req",
    "sample_template_filepaths_get_req",
    "prep_template_summary_get_req",
    "prep_template_post_req",
    "prep_template_delete_req",
    "artifact_get_prep_req",
    "prep_template_graph_get_req",
    "prep_template_filepaths_get_req",
    "prep_template_jobs_get_req",
    "artifact_get_req",
    "artifact_status_put_req",
    "prep_template_get_req",
    "study_delete_req",
    "study_prep_get_req",
    "sample_template_get_req",
    "artifact_graph_get_req",
    "artifact_types_get_req",
    "artifact_post_req",
    "artifact_get_info",
    "sample_template_meta_cats_get_req",
    "sample_template_samples_get_req",
    "prep_template_samples_get_req",
    "sample_template_category_get_req",
    "new_prep_template_get_req",
    "study_files_get_req",
    "prep_template_ajax_get_req",
    "study_tags_request",
    "study_patch_request",
    "study_get_tags_request",
    "prep_template_patch_req",
    "ontology_patch_handler",
    "list_commands_handler_get_req",
    "list_options_handler_get_req",
    "workflow_handler_post_req",
    "workflow_handler_patch_req",
    "workflow_run_post_req",
    "job_ajax_get_req",
    "analyses_associated_with_study",
    "get_sample_template_processing_status",
    "user_jobs_get_req",
    "job_ajax_patch_req",
    "check_access",
    "check_fp",
]
