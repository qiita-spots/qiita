# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------


from qiita_db.handlers.oauth2 import authenticate_oauth

from .rest_handler import RESTHandler

# terms used more than once
_STUDY = "study"
_PREP = "prep"
_FILEPATH = "filepath"
_STATUS = "status"
_ARTIFACT = "artifact"
_SAMPLE = "sample"
_METADATA = "metadata"
_TEMPLATE = "template"
_ID = "id"
_PROCESSING = "processing"
_TYPE = "type"

# payload keys
STUDY_ID = f"{_STUDY}_{_ID}"
STUDY_SAMPLE_METADATA_FILEPATH = f"{_STUDY}_{_SAMPLE}_{_METADATA}_{_FILEPATH}"
PREP_TEMPLATES = f"{_PREP}_{_TEMPLATE}s"
PREP_ID = f"{_PREP}_{_ID}"
PREP_STATUS = f"{_PREP}_{_STATUS}"
PREP_SAMPLE_METADATA_FILEPATH = f"{_PREP}_{_SAMPLE}_{_METADATA}_{_FILEPATH}"
PREP_DATA_TYPE = f"{_PREP}_data_{_TYPE}"
PREP_HUMAN_FILTERING = f"{_PREP}_human_filtering"
PREP_ARTIFACTS = f"{_PREP}_{_ARTIFACT}s"
ARTIFACT_ID = f"{_ARTIFACT}_{_ID}"
ARTIFACT_STATUS = f"{_ARTIFACT}_{_STATUS}"
ARTIFACT_PARENT_IDS = f"{_ARTIFACT}_parent_{_ID}s"
ARTIFACT_BASAL_ID = f"{_ARTIFACT}_basal_{_ID}"
ARTIFACT_PROCESSING_ID = f"{_ARTIFACT}_{_PROCESSING}_{_ID}"
ARTIFACT_PROCESSING_NAME = f"{_ARTIFACT}_{_PROCESSING}_name"
ARTIFACT_PROCESSING_ARGUMENTS = f"{_ARTIFACT}_{_PROCESSING}_arguments"
ARTIFACT_FILEPATHS = f"{_ARTIFACT}_{_FILEPATH}s"
ARTIFACT_FILEPATH = f"{_ARTIFACT}_{_FILEPATH}"
ARTIFACT_FILEPATH_TYPE = f"{_ARTIFACT}_{_FILEPATH}_{_TYPE}"
ARTIFACT_FILEPATH_ID = f"{_ARTIFACT}_{_FILEPATH}_{_ID}"


def _most_recent_template_path(template):
    """Obtain the most recent available template filepath"""
    filepaths = template.get_filepaths()

    # the test dataset shows that a prep can exist without a prep template
    if len(filepaths) == 0:
        return None

    # [0] -> the highest file by ID
    # [1] -> the filepath
    return filepaths[0][1]


def _set_study(payload, study):
    """Set study level information"""
    filepath = _most_recent_template_path(study.sample_template)

    payload[STUDY_ID] = study.id
    payload[STUDY_SAMPLE_METADATA_FILEPATH] = filepath


def _set_prep_templates(payload, study):
    """Set prep template level information"""
    template_data = []
    for pt in study.prep_templates():
        _set_prep_template(template_data, pt)
    payload[PREP_TEMPLATES] = template_data


def _get_human_filtering(prep_template):
    """Obtain the human filtering if applied"""
    # .current_human_filtering does not describe what the human filter is
    # so we will examine the first artifact off the prep
    if prep_template.artifact is not None:
        return prep_template.artifact.human_reads_filter_method


def _set_prep_template(template_payload, prep_template):
    """Set an individual prep template information"""
    filepath = _most_recent_template_path(prep_template)

    current_template = {}
    current_template[PREP_ID] = prep_template.id
    current_template[PREP_STATUS] = prep_template.status
    current_template[PREP_SAMPLE_METADATA_FILEPATH] = filepath
    current_template[PREP_DATA_TYPE] = prep_template.data_type()
    current_template[PREP_HUMAN_FILTERING] = _get_human_filtering(prep_template)

    _set_artifacts(current_template, prep_template)

    template_payload.append(current_template)


def _get_artifacts(prep_template):
    """Get artifact information associated with a prep"""
    if prep_template.artifact is None:
        return []

    pending_artifact_objects = [
        prep_template.artifact,
    ]
    all_artifact_objects = set(pending_artifact_objects[:])

    while pending_artifact_objects:
        artifact = pending_artifact_objects.pop()
        pending_artifact_objects.extend(artifact.children)
        all_artifact_objects.update(set(artifact.children))

    return sorted(all_artifact_objects, key=lambda artifact: artifact.id)


def _set_artifacts(template_payload, prep_template):
    """Set artifact information specific to a prep"""
    prep_artifacts = []

    if prep_template.artifact is None:
        basal_id = None
    else:
        basal_id = prep_template.artifact.id

    for artifact in _get_artifacts(prep_template):
        _set_artifact(prep_artifacts, artifact, basal_id)
    template_payload[PREP_ARTIFACTS] = prep_artifacts


def _set_artifact(prep_artifacts, artifact, basal_id):
    """Set artifact specific information"""
    artifact_payload = {}
    artifact_payload[ARTIFACT_ID] = artifact.id

    # Prep uses .status, artifact uses .visibility
    # favoring .status as visibility implies a UI
    artifact_payload[ARTIFACT_STATUS] = artifact.visibility

    parents = [parent.id for parent in artifact.parents]
    artifact_payload[ARTIFACT_PARENT_IDS] = parents if parents else None
    artifact_payload[ARTIFACT_BASAL_ID] = basal_id

    _set_artifact_processing(artifact_payload, artifact)
    _set_artifact_filepaths(artifact_payload, artifact)

    prep_artifacts.append(artifact_payload)


def _set_artifact_processing(artifact_payload, artifact):
    """Set processing parameter information associated with an artifact"""
    processing_parameters = artifact.processing_parameters
    if processing_parameters is None:
        artifact_processing_id = None
        artifact_processing_name = None
        artifact_processing_arguments = None
    else:
        command = processing_parameters.command
        artifact_processing_id = command.id
        artifact_processing_name = command.name
        artifact_processing_arguments = processing_parameters.values

    artifact_payload[ARTIFACT_PROCESSING_ID] = artifact_processing_id
    artifact_payload[ARTIFACT_PROCESSING_NAME] = artifact_processing_name
    artifact_payload[ARTIFACT_PROCESSING_ARGUMENTS] = artifact_processing_arguments


def _set_artifact_filepaths(artifact_payload, artifact):
    """Set filepath information associated with an artifact"""
    artifact_filepaths = []
    for filepath_data in artifact.filepaths:
        local_payload = {}
        local_payload[ARTIFACT_FILEPATH] = filepath_data["fp"]
        local_payload[ARTIFACT_FILEPATH_ID] = filepath_data["fp_id"]
        local_payload[ARTIFACT_FILEPATH_TYPE] = filepath_data["fp_type"]
        artifact_filepaths.append(local_payload)

    # the test study includes an artifact which does not have filepaths
    if len(artifact_filepaths) == 0:
        artifact_filepaths = None

    artifact_payload[ARTIFACT_FILEPATHS] = artifact_filepaths


class StudyAssociationHandler(RESTHandler):
    @authenticate_oauth
    def get(self, study_id):
        study = self.safe_get_study(study_id)
        if study is None:
            return

        # schema:
        #  STUDY_ID: <int>,
        #  STUDY_SAMPLE_METADATA_FILEPATH: <path>,
        #  PREP_TEMPLATES: None | list[dict]
        #      PREP_ID: <int>,
        #      PREP_STATUS: <str>,
        #      PREP_SAMPLE_METADATA_FILEPATH: <path>,
        #      PREP_DATA_TYPE: <str>,
        #      PREP_HUMAN_FILTERING: None | <str>,
        #      PREP_ARTIFACTS: None | list[dict]
        #          ARTIFACT_ID: <int>,
        #          ARTIFACT_STATUS: <str>,
        #          ARTIFACT_PARENT_IDS: None | list[int],
        #          ARTIFACT_BASAL_ID: None | <int>,
        #          ARTIFACT_PROCESSING_ID: None | <int>,
        #          ARTIFACT_PROCESSING_NAME: None | <str,
        #          ARTIFACT_PROCESSING_ARGUMENTS: None | dict[noschema]
        #          ARTIFACT_FILEPATHS: None | list[dict]
        #              ARTIFACT_FILEPATH_ID: <int>,
        #              ARTIFACT_FILEPATH: <path>,
        #              ARTIFACT_FILEPATH_TYPE': <str>
        #
        payload = {}
        _set_study(payload, study)
        _set_prep_templates(payload, study)
        self.write(payload)
        self.finish()
