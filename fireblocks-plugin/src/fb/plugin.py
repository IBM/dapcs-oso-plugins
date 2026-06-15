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
import logging

from typing import Any, List, Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

from werkzeug.exceptions import NotFound

from oso.framework.data.types import V1_3
from oso.framework.plugin.base import PluginProtocol
from oso.framework.plugin import current_oso_plugin


from .utils import log_error, model_dump_json

from .customer_server import (
    CustomerServerMessagesStatusApi,
    CustomerServerMessagesToSignApi,
)

from .ekmf import (
    CKM,
    EkmfAddonClient,
    EkmfAddonError,
    EkmfImportState,
    Grep11Client,
    SigningKeyStore,
    parse_ekmf_document_type,
)

from .ekmf.schemas import (
    DocumentType,
    EkmfPayloadDocument,
    KeyBlob,
    WrappingKey,
)

from .ekmf_views import (
    EkmfImportInitApi,
    EkmfImportKeyApi,
    EkmfImportPayloadApi,
    EkmfImportResultApi,
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


# Fireblocks messages are pre-hashed, so secp256k1 data is signed raw with
# CKM_ECDSA (no additional digest).
KEY_TYPE_TO_MECHANISM = {
    "secp256k1": CKM.ECDSA,
    "ed25519": CKM.IBM_ED25519_SHA512,
}


class FBPlugin(PluginProtocol):
    class Config(BaseSettings):
        hot_mode: bool = False
        ekmf_addon_port: int | None = None
        ekmf_approver_fingerprints: str = ""
        grep11_endpoint: str = "localhost"
        grep11_port: int = 9876
        keystore_path: str = "/data/ekmf"
        model_config = SettingsConfigDict(env_prefix="FB__")

    internalViews = {
        "messagesToSign": CustomerServerMessagesToSignApi(),
        "messagesStatus": CustomerServerMessagesStatusApi(),
    }

    externalViews = {
        "ekmf/import/init": EkmfImportInitApi(),
        "ekmf/import/key": EkmfImportKeyApi(),
        "ekmf/import/payload": EkmfImportPayloadApi(),
        "ekmf/import/result": EkmfImportResultApi(),
    }

    def __init__(self) -> None:
        super().__init__()
        self.config = self.Config()
        self.signing_error = None

        self.signed_statuses: List[MessageStatus] = []
        self.pending_messages: List[MessageEnvelope] = []

        self.ekmf_state = EkmfImportState()

    @cached_property
    def ekmf_client(self) -> EkmfAddonClient:
        if self.config.ekmf_addon_port is not None:
            return EkmfAddonClient(
                base_url=f"http://localhost:{self.config.ekmf_addon_port}"
            )

        return EkmfAddonClient()

    @cached_property
    def grep11_client(self) -> Grep11Client:
        return Grep11Client(
            endpoint=f"{self.config.grep11_endpoint}:{self.config.grep11_port}"
        )

    @cached_property
    def keystore(self) -> SigningKeyStore:
        return SigningKeyStore(self.config.keystore_path)

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

    def to_oso(self) -> V1_3.DocumentList:
        logger.debug("Entering to_oso()")

        docs: list[V1_3.Document] = []

        match self.mode:
            case "frontend":
                logger.debug(f"to_oso: {self.pending_messages=}")

                for message in self.pending_messages:
                    document = V1_3.Document(
                        id=str(message.transportMetadata.requestId),
                        content=model_dump_json(message),
                        metadata="",
                    )

                    docs.append(document)

                self.pending_messages.clear()

            case "backend":
                logger.debug(f"to_oso: {self.signed_statuses=}")

                for message_status in self.signed_statuses:
                    document = V1_3.Document(
                        id=str(message_status.requestId),
                        content=model_dump_json(message_status),
                        metadata="",
                    )

                    docs.append(document)

                self.signed_statuses.clear()

        for envelope in self.ekmf_state.drain_outbound():
            docs.append(V1_3.Document(**envelope))

        logger.debug(f"to_oso() returning: {docs=}")

        return V1_3.DocumentList(documents=docs, count=len(docs))

    def to_isv(self, oso: V1_3.DocumentList) -> list[str]:
        logger.debug(f"entering to_isv: {oso=}")

        match self.mode:
            case "frontend":
                for doc in oso.documents:
                    doc_type = parse_ekmf_document_type(doc.model_dump())

                    if doc_type in (
                        DocumentType.WRAPPING_KEY,
                        DocumentType.IMPORT_RESULT,
                    ):
                        self.ekmf_state.cache_inbound(doc_type, doc.model_dump())
                        continue

                    if doc_type is not None:
                        logger.info(f"Skipping unexpected EKMF document: {doc_type}")
                        continue

                    try:
                        message_status = MessageStatus.model_validate_json(doc.content)

                    except Exception as e:
                        logger.error("ERROR: could not validate message")
                        logger.debug(f"Invalid doc: {doc=}, Error {e}")
                        continue

                    self.signed_statuses.append(message_status)

            case "backend":
                for doc in oso.documents:
                    doc_type = parse_ekmf_document_type(doc.model_dump())

                    if doc_type == DocumentType.INIT:
                        self._dispatch_keygen()
                        continue

                    if doc_type == DocumentType.EKMF_PAYLOAD:
                        self._dispatch_wrap(doc.model_dump())
                        continue

                    if doc_type is not None:
                        logger.info(f"Skipping unexpected EKMF document: {doc_type}")
                        continue

                    try:
                        message_envelope = MessageEnvelope.model_validate_json(
                            doc.content
                        )

                    except Exception as e:
                        logger.error("ERROR: could not validate message")
                        logger.debug(f"Invalid doc: {doc=}, Error {e}")
                        continue

                    message_status = self.sign(message_envelope)

                    logger.debug(
                        "Appending signed message status:"
                        f" {model_dump_json(message_status)}"
                    )

                    self.signed_statuses.append(message_status)

        return ["OK"]

    def _dispatch_keygen(self) -> None:
        """Generate the EKMF transport wrapping key through the addon."""
        logger.info("Dispatching EKMF keygen to the addon")

        try:
            keygen_result = self.ekmf_client.keygen()

        except EkmfAddonError as e:
            logger.error("ekmf addon /keygen failed")
            logger.debug(f"Status: {e.status_code}, Body: {e.body}")
            return

        # The addon is stateless; the wrap request must include this bundle.
        self.keystore.save_wrapping_key(
            keygen_result.wrapping_key.model_dump(mode="json")
        )

        # Only the document (no private key) flows back through OSO.
        self.ekmf_state.enqueue_outbound(keygen_result.result.model_dump(mode="json"))

    def _dispatch_wrap(self, doc_raw: dict[str, Any]) -> None:
        """Unwrap and import the EKMF-wrapped signing keys through the addon."""
        logger.info("Dispatching EKMF wrap to the addon")

        wrapping_key_raw = self.keystore.load_wrapping_key()

        if wrapping_key_raw is None:
            logger.error(
                "No wrapping key available for ekmf wrap; was keygen dispatched?"
            )
            return

        try:
            payload_doc = EkmfPayloadDocument.model_validate(doc_raw)
            wrapping_key = WrappingKey.model_validate(wrapping_key_raw)

        except Exception as e:
            logger.error("ekmf wrap document validation error")
            logger.debug(f"Error: {e}")
            return

        # Fireblocks only signs with ed25519 and secp256k1 keys; fail the
        # import up front instead of persisting blobs that can never sign.
        key_types = self._payload_key_types(payload_doc)

        unsupported = sorted(
            {
                key_type
                for key_type in key_types.values()
                if key_type not in KEY_TYPE_TO_MECHANISM
            }
        )

        if unsupported:
            logger.error(
                "Rejecting EKMF import: unsupported key type(s)"
                f" {unsupported}; only"
                f" {sorted(KEY_TYPE_TO_MECHANISM)} keys can be imported"
            )
            return

        try:
            import_result = self.ekmf_client.wrap(payload_doc, wrapping_key)

        except EkmfAddonError as e:
            logger.error("ekmf addon /wrap failed")
            logger.debug(f"Status: {e.status_code}, Body: {e.body}")
            return

        self._persist_imported_keys(key_types, import_result.key_blobs)

        self.ekmf_state.enqueue_outbound(import_result.result.model_dump(mode="json"))

    @staticmethod
    def _payload_key_types(payload_doc: EkmfPayloadDocument) -> dict[str, str]:
        key_types: dict[str, str] = {}

        for src_key in payload_doc.content.payload.keys:
            key_type = "aes"

            if src_key.key_type == "EccKey":
                curve = src_key.key_data.curve

                if curve == "EDWARDS_CURVE_25519":
                    key_type = "ed25519"

                elif curve == "SECP256K1_CURVE":
                    key_type = "secp256k1"

            key_types[src_key.key_data.key_label] = key_type

        return key_types

    def _persist_imported_keys(
        self, key_types: dict[str, str], key_blobs: list[KeyBlob]
    ) -> None:
        new_keys = [
            {
                "key_label": blob.key_label,
                "key_type": key_types.get(blob.key_label, "aes"),
                "encrypted_key": blob.encrypted_key,
            }
            for blob in key_blobs
        ]

        # Merge with previously imported keys so a later import cannot drop
        # blobs that are already registered with Fireblocks.
        new_labels = {key["key_label"] for key in new_keys}

        existing_keys = [
            {"key_label": label, "key_type": key_type, "encrypted_key": blob}
            for label, key_type, blob in self.keystore.get_all_keys()
            if label not in new_labels
        ]

        self.keystore.save_keys(existing_keys + new_keys)

        logger.info(f"Persisted {len(new_keys)} imported signing key(s)")

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
                mechanisms = self.grep11_client.get_mechanism_list()

            except Exception as e:
                logger.info("Error getting status")
                logger.debug(f"Error: {e}")

                return V1_3.ComponentStatus(
                    status_code=500,
                    status="Internal Server Error",
                    errors=[
                        V1_3.Error(
                            code="1",
                            message="Could not get the GREP11 mechanism list",
                        )
                    ],
                )

            errors = [
                V1_3.Error(
                    code="1",
                    message=f"GREP11 server does not support {mechanism.name}",
                )
                for mechanism in KEY_TYPE_TO_MECHANISM.values()
                if mechanism not in mechanisms
            ]

            if errors:
                return V1_3.ComponentStatus(
                    status_code=500, status="Internal Server Error", errors=errors
                )

            return V1_3.ComponentStatus(status_code=200, status="OK", errors=[])

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

        key_id = message_envelope.message.payload.signingDeviceKeyId

        key_entry = next(
            (key for key in self.keystore.get_all_keys() if key[0] == key_id), None
        )

        for message_to_sign in message_envelope.message.payload.messagesToSign:
            try:
                if key_entry is None:
                    raise Exception(f"No imported key found for key id: '{key_id}'")

                _, key_type, key_blob = key_entry

                if key_type not in KEY_TYPE_TO_MECHANISM:
                    raise Exception(
                        f"Key type '{key_type}' is not supported for signing"
                    )

                signature = self.grep11_client.sign_single(
                    data=bytes.fromhex(message_to_sign.message),
                    key_blob=key_blob,
                    mechanism=KEY_TYPE_TO_MECHANISM[key_type],
                ).hex()

            except Exception as e:
                self.signing_error = True
                logger.info("Error signing message")
                logger.debug(f"Error: {e}")

                message_status.status = MessageState.FAILED
                continue

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


def infer_response_type(message_type: RequestType) -> ResponseType:
    match message_type:
        case RequestType.KEY_LINK_PROOF_OF_OWNERSHIP_REQUEST:
            return ResponseType.KEY_LINK_PROOF_OF_OWNERSHIP_RESPONSE

        case RequestType.KEY_LINK_TX_SIGN_REQUEST:
            return ResponseType.KEY_LINK_TX_SIGN_RESPONSE
