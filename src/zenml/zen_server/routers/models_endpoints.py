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
    MODEL_VERSIONS,
    MODELS,
    VERSION_1,
)
from zenml.enums import PermissionType
from zenml.models import (
    ModelFilter,
    ModelResponse,
    ModelUpdate,
    ModelVersionFilter,
    ModelVersionResponse,
    Page,
)
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
    prefix=API + VERSION_1 + MODELS,
    tags=["models"],
    responses={401: error_response},
)


@router.get(
    "",
    response_model=Page[ModelResponse],
    responses={401: error_response, 404: error_response, 422: error_response},
)
@handle_exceptions
def list_models(
    model_filter_model: ModelFilter = Depends(make_dependable(ModelFilter)),
    hydrate: bool = False,
    _: AuthContext = Security(authorize, scopes=[PermissionType.READ]),
) -> Page[ModelResponse]:
    """Get models according to query filters.

    Args:
        model_filter_model: Filter model used for pagination, sorting,
            filtering
        hydrate: Flag deciding whether to hydrate the output model(s)
            by including metadata fields in the response.

    Returns:
        The models according to query filters.
    """
    return zen_store().list_models(
        model_filter_model=model_filter_model,
        hydrate=hydrate,
    )


@router.get(
    "/{model_name_or_id}",
    response_model=ModelResponse,
    responses={401: error_response, 404: error_response, 422: error_response},
)
@handle_exceptions
def get_model(
    model_name_or_id: Union[str, UUID],
    hydrate: bool = True,
    _: AuthContext = Security(authorize, scopes=[PermissionType.READ]),
) -> ModelResponse:
    """Get a model by name or ID.

    Args:
        model_name_or_id: The name or ID of the model to get.
        hydrate: Flag deciding whether to hydrate the output model(s)
            by including metadata fields in the response.

    Returns:
        The model with the given name or ID.
    """
    return zen_store().get_model(model_name_or_id, hydrate=hydrate)


@router.put(
    "/{model_id}",
    response_model=ModelResponse,
    responses={401: error_response, 404: error_response, 422: error_response},
)
@handle_exceptions
def update_model(
    model_id: UUID,
    model_update: ModelUpdate,
    _: AuthContext = Security(authorize, scopes=[PermissionType.WRITE]),
) -> ModelResponse:
    """Updates a model.

    Args:
        model_id: Name of the stack.
        model_update: Stack to use for the update.

    Returns:
        The updated model.
    """
    return zen_store().update_model(
        model_id=model_id,
        model_update=model_update,
    )


@router.delete(
    "/{model_name_or_id}",
    responses={401: error_response, 404: error_response, 422: error_response},
)
@handle_exceptions
def delete_model(
    model_name_or_id: Union[str, UUID],
    _: AuthContext = Security(authorize, scopes=[PermissionType.WRITE]),
) -> None:
    """Delete a model by name or ID.

    Args:
        model_name_or_id: The name or ID of the model to delete.
    """
    zen_store().delete_model(model_name_or_id)


#################
# Model Versions
#################


@router.get(
    "/{model_name_or_id}" + MODEL_VERSIONS,
    response_model=Page[ModelVersionResponse],
    responses={401: error_response, 404: error_response, 422: error_response},
)
@handle_exceptions
def list_model_versions(
    model_name_or_id: Union[str, UUID],
    model_version_filter_model: ModelVersionFilter = Depends(
        make_dependable(ModelVersionFilter)
    ),
    hydrate: bool = False,
    _: AuthContext = Security(authorize, scopes=[PermissionType.READ]),
) -> Page[ModelVersionResponse]:
    """Get model versions according to query filters.

    This endpoint serves the purpose of allowing scoped filtering by model_id.

    Args:
        model_name_or_id: The name or ID of the model to list in.
        model_version_filter_model: Filter model used for pagination, sorting,
            filtering
        hydrate: Flag deciding whether to hydrate the output model(s)
            by including metadata fields in the response.

    Returns:
        The model versions according to query filters.
    """
    return zen_store().list_model_versions(
        model_name_or_id=model_name_or_id,
        model_version_filter_model=model_version_filter_model,
        hydrate=hydrate,
    )