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
"""Implementation of the ZenML ClearML orchestrator."""

import json
import os
import sys
import time
from typing import TYPE_CHECKING, Any, Dict, Optional, Type, Union, cast
from uuid import uuid4

from pydantic import validator

from zenml.client import Client
from zenml.config.base_settings import BaseSettings
from zenml.config.global_config import GlobalConfiguration
from zenml.constants import (
    ENV_ZENML_LOCAL_STORES_PATH,
)
from zenml.entrypoints import StepEntrypointConfiguration
from zenml.enums import StackComponentType
from zenml.logger import get_logger
from zenml.orchestrators import (
    ContainerizedOrchestrator,
)
from zenml.orchestrators import utils as orchestrator_utils
from zenml.stack import Stack, StackValidator
from zenml.utils import string_utils
from zenml.integrations.clearml.flavors import ClearMLOrchestratorConfig, ClearMLOrchestratorSettings

if TYPE_CHECKING:
    from zenml.models.pipeline_deployment_models import (
        PipelineDeploymentResponseModel,
    )

logger = get_logger(__name__)

ENV_ZENML_DOCKER_ORCHESTRATOR_RUN_ID = "ZENML_DOCKER_ORCHESTRATOR_RUN_ID"


class ClearMLOrchestrator(ContainerizedOrchestrator):
    """Orchestrator responsible for running pipelines locally using Docker.

    This orchestrator does not allow for concurrent execution of steps and also
    does not support running on a schedule.
    """

    @property
    def config(self) -> ClearMLOrchestratorConfig:
        """Returns the `ClearMLOrchestratorConfig` config.

        Returns:
            The configuration.
        """
        return cast(ClearMLOrchestratorConfig, self._config)

    @property
    def settings_class(self) -> Optional[Type["BaseSettings"]]:
        """Settings class for the Local Docker orchestrator.

        Returns:
            The settings class.
        """
        return ClearMLOrchestratorSettings

    @property
    def validator(self) -> Optional[StackValidator]:
        """Ensures there is an image builder in the stack.

        Returns:
            A `StackValidator` instance.
        """
        return StackValidator(
            required_components={StackComponentType.IMAGE_BUILDER}
        )

    def get_orchestrator_run_id(self) -> str:
        """Returns the active orchestrator run id.

        Raises:
            RuntimeError: If the environment variable specifying the run id
                is not set.

        Returns:
            The orchestrator run id.
        """
        try:
            return os.environ[ENV_ZENML_DOCKER_ORCHESTRATOR_RUN_ID]
        except KeyError:
            raise RuntimeError(
                "Unable to read run id from environment variable "
                f"{ENV_ZENML_DOCKER_ORCHESTRATOR_RUN_ID}."
            )

    def prepare_or_run_pipeline(
        self,
        deployment: "PipelineDeploymentResponseModel",
        stack: "Stack",
    ) -> Any:
        """Sequentially runs all pipeline steps in local Docker containers.

        Args:
            deployment: The pipeline deployment to prepare or run.
            stack: The stack the pipeline will run on.
        """
        if deployment.schedule:
            logger.warning(
                "Local Docker Orchestrator currently does not support the"
                "use of schedules. The `schedule` will be ignored "
                "and the pipeline will be run immediately."
            )

        from docker.client import DockerClient

        docker_client = DockerClient.from_env()
        entrypoint = StepEntrypointConfiguration.get_entrypoint_command()

        # Add the local stores path as a volume mount
        stack.check_local_paths()
        local_stores_path = GlobalConfiguration().local_stores_path
        volumes = {
            local_stores_path: {
                "bind": local_stores_path,
                "mode": "rw",
            }
        }
        orchestrator_run_id = str(uuid4())
        environment = {
            ENV_ZENML_DOCKER_ORCHESTRATOR_RUN_ID: orchestrator_run_id,
            ENV_ZENML_LOCAL_STORES_PATH: local_stores_path,
        }
        start_time = time.time()

        # Run each step
        for step_name, step in deployment.step_configurations.items():
            if self.requires_resources_in_orchestration_environment(step):
                logger.warning(
                    "Specifying step resources is not supported for the local "
                    "Docker orchestrator, ignoring resource configuration for "
                    "step %s.",
                    step.config.name,
                )

            arguments = StepEntrypointConfiguration.get_entrypoint_arguments(
                step_name=step_name, deployment_id=deployment.id
            )

            settings = cast(
                ClearMLOrchestratorSettings,
                self.get_settings(step),
            )
            image = self.get_image(deployment=deployment, step_name=step_name)

            user = None
            if sys.platform != "win32":
                user = os.getuid()
            logger.info("Running step `%s` in Docker:", step_name)
            logs = docker_client.containers.run(
                image=image,
                entrypoint=entrypoint,
                command=arguments,
                user=user,
                volumes=volumes,
                environment=environment,
                stream=True,
                extra_hosts={"host.docker.internal": "host-gateway"},
                **settings.run_args,
            )

            for line in logs:
                logger.info(line.strip().decode())

        run_duration = time.time() - start_time
        run_id = orchestrator_utils.get_run_id_for_orchestrator_run_id(
            orchestrator=self, orchestrator_run_id=orchestrator_run_id
        )
        run_model = Client().zen_store.get_run(run_id)
        logger.info(
            "Pipeline run `%s` has finished in %s.",
            run_model.name,
            string_utils.get_human_readable_time(run_duration),
        )
