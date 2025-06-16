#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2025
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
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
