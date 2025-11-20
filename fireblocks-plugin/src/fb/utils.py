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

import logging
import pydantic

from typing import Any


def model_dump_json(model: pydantic.BaseModel) -> str:
    return model.model_dump_json(by_alias=True, exclude_none=True)


def model_dump(model: pydantic.BaseModel) -> dict[str, Any]:
    return model.model_dump(by_alias=True, exclude_none=True)


def log_error(
    logger: logging.Logger, msg: str, debug_msg: str, error_type: type[Exception]
) -> None:
    logger.error(msg)
    logger.debug(debug_msg)
    raise error_type(msg)
