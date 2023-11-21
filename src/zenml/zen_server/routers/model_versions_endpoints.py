#  Copyright (c) ZenML GmbH 2023. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at:
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#  or implied. See the License for the specific language governing
#  permissions and limitations under the License.
"""Endpoint definitions for models."""

from typing import Union
from uuid import UUID

from fastapi import APIRouter, Depends, Security

from zenml.constants import (
    API,
    ARTIFACTS,
    MODEL_VERSIONS,
    RUNS,
    VERSION_1,
)
from zenml.enums import PermissionType
from zenml.models import (
    ModelVersionArtifactFilter,
    ModelVersionArtifactResponse,
    ModelVersionFilter,
    ModelVersionPipelineRunFilter,
    ModelVersionPipelineRunResponse,
    ModelVersionResponse,
    ModelVersionUpdate,
)
from zenml.models.v2.base.page import Page
from zenml.zen_server.auth import AuthContext, authorize
from zenml.zen_server.exceptions import error_response
from zenml.zen_server.utils import (
    handle_exceptions,
    make_dependable,
    zen_store,
)

#########
# Models
#########

router = APIRouter(
    prefix=API + VERSION_1 + MODEL_VERSIONS,
    tags=["model_versions"],
    responses={401: error_response},
)

#################
# Model Versions
#################


@router.get(
    "",
    response_model=Page[ModelVersionResponse],
    responses={401: error_response, 404: error_response, 422: error_response},
)
@handle_exceptions
def list_model_versions(
    model_version_filter_model: ModelVersionFilter = Depends(
        make_dependable(ModelVersionFilter)
    ),
    hydrate: bool = False,
    _: AuthContext = Security(authorize, scopes=[PermissionType.READ]),
) -> Page[ModelVersionResponse]:
    """Get model versions according to query filters.

    Args:
        model_version_filter_model: Filter model used for pagination, sorting,
            filtering
        hydrate: Flag deciding whether to hydrate the output model(s)
            by including metadata fields in the response.

    Returns:
        The model versions according to query filters.
    """
    return zen_store().list_model_versions(
        model_version_filter_model=model_version_filter_model,
        hydrate=hydrate,
    )


@router.get(
    "/{model_version_id}",
    response_model=ModelVersionResponse,
    responses={401: error_response, 404: error_response, 422: error_response},
)
@handle_exceptions
def get_model_version(
    model_version_id: UUID,
    hydrate: bool = True,
    _: AuthContext = Security(authorize, scopes=[PermissionType.READ]),
) -> ModelVersionResponse:
    """Get a model version by ID.

    Args:
        model_version_id: id of the model version to be retrieved.
        hydrate: Flag deciding whether to hydrate the output model(s)
            by including metadata fields in the response.

    Returns:
        The model version with the given name or ID.
    """
    return zen_store().get_model_version(
        model_version_id=model_version_id,
        hydrate=hydrate,
    )


@router.put(
    "/{model_version_id}",
    response_model=ModelVersionResponse,
    responses={401: error_response, 404: error_response, 422: error_response},
)
@handle_exceptions
def update_model_version(
    model_version_id: UUID,
    model_version_update_model: ModelVersionUpdate,
    _: AuthContext = Security(authorize, scopes=[PermissionType.WRITE]),
) -> ModelVersionResponse:
    """Get all model versions by filter.

    Args:
        model_version_id: The ID of model version to be updated.
        model_version_update_model: The model version to be updated.

    Returns:
        An updated model version.
    """
    return zen_store().update_model_version(
        model_version_id=model_version_id,
        model_version_update_model=model_version_update_model,
    )


@router.delete(
    "/{model_version_id}",
    responses={401: error_response, 404: error_response, 422: error_response},
)
@handle_exceptions
def delete_model_version(
    model_version_id: UUID,
    _: AuthContext = Security(authorize, scopes=[PermissionType.WRITE]),
) -> None:
    """Delete a model by name or ID.

    Args:
        model_version_id: The name or ID of the model version to delete.
    """
    zen_store().delete_model_version(model_version_id)


##########################
# Model Version Artifacts
##########################


@router.get(
    "/{model_version_id}" + ARTIFACTS,
    response_model=Page[ModelVersionArtifactResponse],
    responses={401: error_response, 404: error_response, 422: error_response},
)
@handle_exceptions
def list_model_version_artifact_links(
    model_version_id: UUID,
    model_version_artifact_link_filter_model: ModelVersionArtifactFilter = Depends(
        make_dependable(ModelVersionArtifactFilter)
    ),
    hydrate: bool = False,
    _: AuthContext = Security(authorize, scopes=[PermissionType.READ]),
) -> Page[ModelVersionArtifactResponse]:
    """Get model version to artifact links according to query filters.

    Args:
        model_version_id: ID of the model version containing links.
        model_version_artifact_link_filter_model: Filter model used for
            pagination, sorting, filtering.
        hydrate: Flag deciding whether to hydrate the output model(s)
            by including metadata fields in the response.

    Returns:
        The model version to artifact links according to query filters.
    """
    return zen_store().list_model_version_artifact_links(
        model_version_id=model_version_id,
        model_version_artifact_link_filter_model=model_version_artifact_link_filter_model,
        hydrate=hydrate,
    )


@router.delete(
    "/{model_version_id}"
    + ARTIFACTS
    + "/{model_version_artifact_link_name_or_id}",
    responses={401: error_response, 404: error_response, 422: error_response},
)
@handle_exceptions
def delete_model_version_artifact_link(
    model_version_id: UUID,
    model_version_artifact_link_name_or_id: Union[str, UUID],
    _: AuthContext = Security(authorize, scopes=[PermissionType.WRITE]),
) -> None:
    """Deletes a model version link.

    Args:
        model_version_id: ID of the model version containing the link.
        model_version_artifact_link_name_or_id: name or ID of the model version
            to artifact link to be deleted.
    """
    zen_store().delete_model_version_artifact_link(
        model_version_id,
        model_version_artifact_link_name_or_id,
    )


##############################
# Model Version Pipeline Runs
##############################


@router.get(
    "/{model_version_id}" + RUNS,
    response_model=Page[ModelVersionPipelineRunResponse],
    responses={401: error_response, 404: error_response, 422: error_response},
)
@handle_exceptions
def list_model_version_pipeline_run_links(
    model_version_id: UUID,
    model_version_pipeline_run_link_filter_model: ModelVersionPipelineRunFilter = Depends(
        make_dependable(ModelVersionPipelineRunFilter)
    ),
    hydrate: bool = False,
    _: AuthContext = Security(authorize, scopes=[PermissionType.READ]),
) -> Page[ModelVersionPipelineRunResponse]:
    """Get model version to pipeline run links according to query filters.

    Args:
        model_version_id: ID of the model version containing the link.
        model_version_pipeline_run_link_filter_model: Filter model used for
            pagination, sorting and filtering.
        hydrate: Flag deciding whether to hydrate the output model(s)
            by including metadata fields in the response.

    Returns:
        The model version to pipeline run links according to query filters.
    """
    return zen_store().list_model_version_pipeline_run_links(
        model_version_id=model_version_id,
        model_version_pipeline_run_link_filter_model=model_version_pipeline_run_link_filter_model,
        hydrate=hydrate,
    )


@router.delete(
    "/{model_version_id}"
    + RUNS
    + "/{model_version_pipeline_run_link_name_or_id}",
    responses={401: error_response, 404: error_response, 422: error_response},
)
@handle_exceptions
def delete_model_version_pipeline_run_link(
    model_version_id: UUID,
    model_version_pipeline_run_link_name_or_id: Union[str, UUID],
    _: AuthContext = Security(authorize, scopes=[PermissionType.WRITE]),
) -> None:
    """Deletes a model version link.

    Args:
        model_version_id: name or ID of the model version containing the link.
        model_version_pipeline_run_link_name_or_id: name or ID of the model version link to be deleted.
    """
    zen_store().delete_model_version_pipeline_run_link(
        model_version_id=model_version_id,
        model_version_pipeline_run_link_name_or_id=model_version_pipeline_run_link_name_or_id,
    )