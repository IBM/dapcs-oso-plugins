#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024, 2025
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#
""""""

import logging
import sys

from flask import jsonify, request
from flask.views import MethodView

from pydantic import ValidationError

from oso.framework.plugin import current_oso_plugin_app

from .types import MessagesRequest, MessagesStatusRequest, MessagesStatusResponse
from .utils import model_dump

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)


class CustomerServerMessagesToSignApi(MethodView):
    """Fireblocks KeyLink Customer Server API /messagesToSign."""

    ENDPOINT = "/".join(__name__.split(".")[-2:])

    def post(self):
        json_data = request.get_json()

        try:
            messages_request = MessagesRequest.model_validate(json_data)

        except Exception as e:
            logger.error("Could not validate MessagesStatusRequest")
            logger.debug(f"Request: {json_data}, Error: {e}")
            raise ValidationError("Could not validate MessagesStatusRequest")

        messages_status_response: MessagesStatusResponse = (
            current_oso_plugin_app().messagesToSign(messages_request)
        )

        logger.debug(
            f"messagesToSign response object: {model_dump(messages_status_response)}"
        )

        return jsonify(model_dump(messages_status_response))


class CustomerServerMessagesStatusApi(MethodView):
    """Fireblocks KeyLink Customer Server API /messagesStatus."""

    ENDPOINT = "/".join(__name__.split(".")[-2:])

    def post(self):
        json_data = request.get_json()

        try:
            messages_status_request = MessagesStatusRequest.model_validate(json_data)

        except Exception as e:
            logger.error("Could not validate MessagesStatusRequest")
            logger.debug(f"Request: {json_data}, Error: {e}")
            raise ValidationError("Could not validate MessagesStatusRequest")

        # You don't really get type checking from current_oso_plugin
        messages_status_response: MessagesStatusResponse = (
            current_oso_plugin_app().messagesStatus(messages_status_request)
        )

        return jsonify(model_dump(messages_status_response))
