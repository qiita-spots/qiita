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
from .sample_template import (
    sample_template_post_req, sample_template_put_req,
    sample_template_summary_get_req, sample_template_delete_req,
    sample_template_filepaths_get_req, sample_template_get_req,
    sample_template_meta_cats_get_req, sample_template_samples_get_req,
    sample_template_category_get_req)
from .prep_template import (
    prep_template_summary_get_req, prep_template_post_req,
    prep_template_delete_req, prep_template_get_req,
    prep_template_graph_get_req, prep_template_filepaths_get_req,
    prep_template_samples_get_req,
    new_prep_template_get_req, prep_template_ajax_get_req,
    prep_template_patch_req)
from .studies import (
    data_types_get_req, study_get_req, study_prep_get_req, study_delete_req,
    study_files_get_req)
from .artifact import (artifact_graph_get_req, artifact_types_get_req,
                       artifact_post_req, artifact_get_req,
                       artifact_status_put_req, artifact_delete_req,
                       artifact_summary_get_request,
                       artifact_summary_post_request)
from .ontology import ontology_patch_handler
from .processing import (
    list_commands_handler_get_req, process_artifact_handler_get_req)

__version__ = "0.2.0-dev"

__all__ = ['prep_template_summary_get_req', 'sample_template_post_req',
           'sample_template_put_req', 'data_types_get_req',
           'study_get_req', 'sample_template_summary_get_req',
           'sample_template_delete_req', 'sample_template_filepaths_get_req',
           'prep_template_summary_get_req', 'prep_template_post_req',
           'prep_template_delete_req',
           'prep_template_graph_get_req', 'prep_template_filepaths_get_req',
           'artifact_get_req', 'artifact_status_put_req',
           'artifact_delete_req', 'prep_template_get_req', 'study_delete_req',
           'study_prep_get_req', 'sample_template_get_req',
           'artifact_graph_get_req', 'artifact_types_get_req',
           'artifact_post_req',
           'sample_template_meta_cats_get_req',
           'sample_template_samples_get_req', 'prep_template_samples_get_req',
           'sample_template_category_get_req', 'new_prep_template_get_req',
           'study_files_get_req', 'prep_template_ajax_get_req',
           'prep_template_patch_req', 'ontology_patch_handler',
           'artifact_summary_get_request', 'artifact_summary_post_request',
           'list_commands_handler_get_req', 'process_artifact_handler_get_req']
