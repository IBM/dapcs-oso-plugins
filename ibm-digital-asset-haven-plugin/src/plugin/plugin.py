#
# (c) Copyright IBM Corp. 2025
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
""""""

from functools import cached_property

import json
import logging
import requests
import sys

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

from oso.framework.data.types import V1_3
from oso.framework.plugin.base import PluginProtocol
from oso.framework.plugin import current_oso_plugin

FRONTEND_PORT=3002
BACKEND_PORT =3003

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Plugin(PluginProtocol):
    frontendknownids = []
    backendknownids = []

    class Config(BaseSettings):
        model_config = SettingsConfigDict(env_prefix="ISV__")

    def __init__(self) -> None:
        super().__init__()
        self.config = self.Config()

    @cached_property
    def mode(self) -> Literal["frontend", "backend"]:
        return current_oso_plugin().config.mode

    def to_oso(self) -> V1_3.DocumentList:
        logger.debug(f"Entering to_oso(): ({self.mode})")

        docs: list[V1_3.Document] = []
        url: str

        try:
            match self.mode:
                case "frontend":
                    operations = get(get_operations_endpoint(FRONTEND_PORT))
                    for op in operations:
                        id = op["uuid"]
                        assert id
                        if id not in self.frontendknownids:
                            docs.append(V1_3.Document(
                                id=id,
                                content=json.dumps(op),
                                metadata=""))
                            self.frontendknownids.append(id)
                        else:
                            logger.debug(f"to_oso() ignoring operation handled previoulsy: id={id}")

                case "backend":
                    responses = get(get_completed_endpoint(BACKEND_PORT))
                    if responses:
                        for key, value in responses.items():
                            if key not in self.backendknownids:
                                docs.append(V1_3.Document(
                                    id=key,
                                    content=json.dumps(value),
                                    metadata=""))
                                self.backendknownids.append(key)
                            else:
                                logger.debug(f"to_oso() ignoring operation handled previoulsy: id={key}")
            
        except Exception as e:
            logger.error(f"ERROR: could not get documents: {e}")
        
        logger.debug(f"to_oso() returning: {len(docs)} documents")

        return V1_3.DocumentList(documents=docs, count=len(docs))


    def to_isv(self, oso: V1_3.DocumentList) -> list[str]:
        logger.debug(f"entering to_isv: ({self.mode})")
        failedPosts=0
        for doc in oso.documents:
            try:
                match self.mode:
                    case "frontend":
                        data = { doc.id : json.loads(doc.content) }
                        post(get_completed_endpoint(FRONTEND_PORT), data)

                    case "backend":
                        data = [ json.loads(doc.content) ]
                        post(get_operations_endpoint(BACKEND_PORT), data)

            except Exception as e:
                logger.error(f"ERROR: could not post document: {doc.id}, Error: {e}")
                failures += 1
                continue

        logger.debug(f"to_isv() returning: {failedPosts=}")
        return ["OK"]


    def status(self) -> V1_3.ComponentStatus:
        if self.mode == "frontend":
            return V1_3.ComponentStatus(
                status_code=200,
                status="OK",
                errors=[],
            )

        else:
            status_url = f"http://localhost:3003/status"
            try:
                resp = requests.get(status_url, timeout=5)
                resp.raise_for_status()

                # If successful, process the response (e.g., print text or parse JSON)
                logger.debug(f"hsm-driver status successful!")

                # TODO: check hsm driver health
                return V1_3.ComponentStatus(
                    status_code=200,
                    status="OK",
                    errors=[],
                )

            except Exception as err:
                logger.debug(f"Error in HSM Driver Status response: {err}")

                return V1_3.ComponentStatus(
                    status_code=503,
                    status="Waiting for HSM Driver Status",
                    errors=[],
                )

            healthcheck_url = f"http://localhost:3003/healthcheck"
            try:
                resp = requests.get(healthcheck_url, timeout=5)
                resp.raise_for_status()

                # If successful, process the response (e.g., print text or parse JSON)
                logger.debug(f"hsm-driver healthcheck successful!")

                # TODO: check hsm driver health
                return V1_3.ComponentStatus(
                    status_code=200,
                    status="OK",
                    errors=[],
                )

            except Exception as err:
                logger.debug(f"Error in HSM Driver HealthCheck response: {err}")

                return V1_3.ComponentStatus(
                    status_code=503,
                    status="Waiting for HSM Driver HealthCheck",
                    errors=[],
                )


def post(url: str, data: any) -> None:
    logger.debug(f"Entering post(): {url=}")
    response = requests.post(url=url, json=data)
    response.raise_for_status()


def get(url: str) -> any:
    logger.debug(f"get(): {url=}")
    response = requests.get(url=url, timeout=2)
    response.raise_for_status()
    if response.text:
        return json.loads(response.text)
    return []


def get_operations_endpoint(port: str) -> str:
    return f"http://localhost:{port}/operations"


def get_completed_endpoint(port: str) -> str:
    return f"http://localhost:{port}/completed"

