#
# (c) Copyright IBM Corp. 2024, 2025
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

import sys
import json
import logging

from typing import List, cast, Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

from werkzeug.exceptions import NotFound

from oso.framework.data.types import V1_3, V1_5
from oso.framework.plugin.base import PluginProtocol
from oso.framework.plugin import current_oso_plugin, current_oso_plugin_app
from oso.framework.plugin.addons.signing_server import SigningServerAddon, KeyType


from .utils import log_error, model_dump_json

from .customer_server import (
    CustomerServerMessagesStatusApi,
    CustomerServerMessagesToSignApi,
)

from .types import (
    MessageEnvelope,
    MessageResponse,
    MessageState,
    MessagesStatusResponse,
    MessageStatus,
    MessagesStatusRequest,
    MessagesRequest,
    RequestType,
    ResponseType,
    SignedMessage,
)


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)


class FBPlugin(PluginProtocol):
    class Config(BaseSettings):
        hot_mode: bool = False
        min_keys: int = 1
        model_config = SettingsConfigDict(env_prefix="FB__")

    internalViews = {
        "messagesToSign": CustomerServerMessagesToSignApi(),
        "messagesStatus": CustomerServerMessagesStatusApi(),
    }

    def __init__(self) -> None:
        super().__init__()
        self.config = self.Config()
        self.signing_error = None

        self.signed_statuses: List[MessageStatus] = []
        self.pending_messages: List[MessageEnvelope] = []

    @cached_property
    def signing_server(self) -> SigningServerAddon:
        signing_server = cast(
            SigningServerAddon, current_oso_plugin().addons["SigningServer"]
        )

        all_keys_info = []

        for key_type in KeyType:
            try:
                keys = signing_server.list_keys(key_type)

            except Exception as e:
                logger.info("Error listing keys")
                logger.debug(f"Error: {e}")

            needed_keys = current_oso_plugin_app().Config().min_keys - len(keys)

            for _ in range(needed_keys):
                try:
                    key_id, pub_key_pem = signing_server.generate_key_pair(key_type)

                except Exception as e:
                    logger.info("Error generating keys")
                    logger.debug(f"Error: {e}")

                all_keys_info.append(
                    {
                        "key_type": key_type.name,
                        "key_id": key_id,
                        "public_key_pem": pub_key_pem,
                    }
                )

        logger.info(f"Generated Keys: '{json.dumps(all_keys_info)}'")

        return signing_server

    @cached_property
    def mode(self) -> Literal["frontend", "backend"]:
        return current_oso_plugin().config.mode

    def messagesToSign(
        self, messages_request: MessagesRequest
    ) -> MessagesStatusResponse:
        logger.debug(
            f"Entering messagesToSign() with '{model_dump_json(messages_request)}'"
        )

        messages_status_response = MessagesStatusResponse(statuses=[])

        match current_oso_plugin().config.mode:
            case "frontend":
                # HOT mode (non-OSO) -> sign the messages now
                if self.config.hot_mode:
                    for message in messages_request.messages:
                        messages_status_response.statuses.append(self.sign(message))

                else:
                    for message in messages_request.messages:
                        self.pending_messages.append(message)

                        response_type = infer_response_type(
                            message.transportMetadata.request_type
                        )
                        # Because the message hasn't been signed,
                        # there is no signedMessages/MessageResponse
                        message_response = MessageResponse()

                        message_status = MessageStatus(
                            response_type=response_type,
                            status=MessageState.PENDING_SIGN,
                            requestId=message.transportMetadata.requestId,
                            response=message_response,
                        )

                        messages_status_response.statuses.append(message_status)

            case "backend":
                log_error(
                    logger=logger,
                    msg="messagesToSign() not supported in backend mode",
                    debug_msg=f"Mode is: {self.mode}",
                    error_type=NotFound,
                )

        logger.debug(
            f"messagesToSign returning {model_dump_json(messages_status_response)}",
        )

        return messages_status_response

    def messagesStatus(
        self, messages_status_request: MessagesStatusRequest
    ) -> MessagesStatusResponse:
        logger.debug(
            "Entering messagesStatus() with"
            f" {model_dump_json(messages_status_request)}",
        )

        if current_oso_plugin().config.mode != "frontend":
            log_error(
                logger=logger,
                msg="Cannot get messagesStatus when mode is not frontend",
                debug_msg=f"Mode is: {self.mode}",
                error_type=NotFound,
            )

        messages_status_response = MessagesStatusResponse(statuses=[])

        for message in self.pending_messages:
            if (
                message.transportMetadata.requestId
                in messages_status_request.requestsIds
            ):
                response_type = infer_response_type(
                    message.transportMetadata.request_type
                )
                message_response = MessageResponse()

                message_status = MessageStatus(
                    response_type=response_type,
                    status=MessageState.PENDING_SIGN,
                    requestId=message.transportMetadata.requestId,
                    response=message_response,
                )

                messages_status_response.statuses.append(message_status)

        updated_signed_statuses: List[MessageStatus] = []

        for message_status in self.signed_statuses:
            if message_status.requestId in messages_status_request.requestsIds:
                messages_status_response.statuses.append(message_status)

            else:
                updated_signed_statuses.append(message_status)

        self.signed_statuses = updated_signed_statuses

        logger.debug(
            f"messagesStatus returning {model_dump_json(messages_status_response)}",
        )

        return messages_status_response

    def to_oso(self) -> V1_5.DocumentList:
        logger.debug("Entering to_oso()")

        docs: list[V1_5.Document] = []

        match self.mode:
            case "frontend":
                logger.debug(f"to_oso: {self.pending_messages=}")

                for message in self.pending_messages:
                    document = V1_5.Document(
                        id=str(message.transportMetadata.requestId),
                        content=model_dump_json(message),
                    )
                    docs.append(document)

                self.pending_messages.clear()

            case "backend":
                logger.debug(f"to_oso: {self.signed_statuses=}")

                for message_status in self.signed_statuses:
                    document = V1_5.Document(
                        id=str(message_status.requestId),
                        content=model_dump_json(message_status),
                    )
                    docs.append(document)

                self.signed_statuses.clear()

        logger.debug(f"to_oso() returning: {docs=}")
        return V1_5.DocumentList(documents=docs, count=len(docs))

    def to_isv(self, oso: V1_5.DocumentList) -> list[str]:
        """Convert OSO document list to ISV format.

        The framework strips mk_rotation / mk_rotation_done documents before
        this method is called, so the plugin only sees normal signing documents.
        """
        logger.debug(f"entering to_isv: {oso=}")

        match self.mode:
            case "frontend":
                for doc in oso.documents:
                    try:
                        message_status = MessageStatus.model_validate_json(doc.content)
                    except Exception as e:
                        logger.error("ERROR: could not validate message status")
                        logger.debug(f"Invalid doc: {doc=}, Error {e}")
                        continue
                    self.signed_statuses.append(message_status)

            case "backend":
                for doc in oso.documents:
                    try:
                        message_envelope = MessageEnvelope.model_validate_json(
                            doc.content
                        )
                    except Exception as e:
                        logger.error("ERROR: could not validate message envelope")
                        logger.debug(f"Invalid doc: {doc=}, Error {e}")
                        continue

                    message_status = self.sign(message_envelope)
                    logger.debug(
                        "Appending signed message status:"
                        f" {model_dump_json(message_status)}"
                    )
                    self.signed_statuses.append(message_status)

        return ["OK"]

    def rewrap(self, rotation_id: str) -> V1_5.MkRotationDoneMetadata:
        """ISV post-rewrap hook (optional).

        The framework already drove :meth:`~SigningServerAddon.rewrap_keys`
        before calling this method.  Use this hook for any Fireblocks-specific
        actions that must follow a master-key rotation, for example publishing
        new public key PEMs to the Fireblocks console.

        Parameters
        ----------
        rotation_id : str
            Rotation event ID echoed from the framework.

        Returns
        -------
        V1_5.MkRotationDoneMetadata
            The framework merges any additional ``rewrapped_key_ids`` returned
            here with those it already collected from the SigningServer addon.
        """
        logger.info(
            f"FBPlugin.rewrap() hook called rotation_id={rotation_id}. "
            "Add Fireblocks-specific post-rewrap actions here."
        )
        # Example: publish new public keys to Fireblocks API.
        # new_pub_keys = {
        #     key_id: self.signing_server.get_key_pem(key_id)
        #     for key_type in KeyType
        #     for key_id in self.signing_server.list_keys(key_type)
        # }
        # self._publish_keys_to_fireblocks(new_pub_keys)

        # Return an empty done doc; the framework already collected the IDs.
        return V1_5.MkRotationDoneMetadata(
            rotation_id=rotation_id,
            rewrapped_key_ids=[],
        )

    def status(self) -> V1_3.ComponentStatus:
        if self.mode == "frontend":
            return V1_3.ComponentStatus(
                status_code=200,
                status="OK",
                errors=[],
            )

        else:
            if self.signing_error:
                return V1_3.ComponentStatus(
                    status_code=500,
                    status="ERROR",
                    errors=[
                        V1_3.Error(
                            code="SIGNING-FAILED",
                            message="Backend failed to sign the documents",
                        )
                    ],
                )
            try:
                component_status = self.signing_server.health_check()

            except Exception as e:
                logger.info("Error getting status")
                logger.debug(f"Error: {e}")

            logger.debug(f"signing server status received: {component_status=}")

            return component_status

    def sign(self, message_envelope: MessageEnvelope) -> MessageStatus:
        logger.debug(f"sign: {model_dump_json(message_envelope)}")

        response_type = infer_response_type(
            message_envelope.transportMetadata.request_type
        )
        message_response = MessageResponse(signedMessages=[])

        message_status = MessageStatus(
            response_type=response_type,
            status=MessageState.SIGNED,
            requestId=message_envelope.transportMetadata.requestId,
            response=message_response,
        )

        for message_to_sign in message_envelope.message.payload.messagesToSign:
            # TODO: Continue on error
            try:
                signature = self.signing_server.sign(
                    key_id=message_envelope.message.payload.signingDeviceKeyId,
                    data=bytes.fromhex(message_to_sign.message),
                )

            except Exception as e:
                self.signing_error = True
                logger.info("Error signing message")
                logger.debug(f"Error: {e}")

            signed_message = SignedMessage(
                index=message_to_sign.index,
                signature=signature,
                message=message_to_sign.message,
            )

            message_status.response.signedMessages.append(signed_message)

        logger.debug(
            f"sign returns signed messages: {model_dump_json(message_status)}",
        )

        return message_status


def get_signing_api_endpoint() -> str:
    return "http://localhost:9080/signing/api/v2"


def infer_response_type(message_type: RequestType) -> ResponseType:
    match message_type:
        case RequestType.KEY_LINK_PROOF_OF_OWNERSHIP_REQUEST:
            return ResponseType.KEY_LINK_PROOF_OF_OWNERSHIP_RESPONSE

        case RequestType.KEY_LINK_TX_SIGN_REQUEST:
            return ResponseType.KEY_LINK_TX_SIGN_RESPONSE
