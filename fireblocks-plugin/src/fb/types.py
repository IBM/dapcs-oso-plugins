#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024, 2025
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

# https://github.com/fireblocks/fireblocks-agent/blob/main/api/customer-server.api.yml

from typing import Dict, List, Optional, Annotated
from pydantic import BaseModel, Field, Json, field_serializer, ConfigDict
from enum import auto, StrEnum
from uuid import UUID


class UpperStrEnum(StrEnum):
    @staticmethod
    def _generate_next_value_(name, *args):
        return name.upper()


class MessageState(UpperStrEnum):
    PENDING_SIGN = auto()
    SIGNED = auto()
    FAILED = auto()


class RequestType(UpperStrEnum):
    KEY_LINK_PROOF_OF_OWNERSHIP_REQUEST = auto()
    KEY_LINK_TX_SIGN_REQUEST = auto()


class ResponseType(UpperStrEnum):
    KEY_LINK_PROOF_OF_OWNERSHIP_RESPONSE = auto()
    KEY_LINK_TX_SIGN_RESPONSE = auto()


class Algorithm(UpperStrEnum):
    ECDSA_SECP256K1 = auto()
    EDDSA_ED25519 = auto()


class MessagesStatusRequest(BaseModel):
    requestsIds: List[UUID]


class PayloadSignatureData(BaseModel):
    signature: str
    service: str


class MessageToSign(BaseModel):
    message: str
    index: int


class TxMetadataSignature(BaseModel):
    id: str
    type: str
    signature: str


class TxMetadata(BaseModel):
    txMetaData: str
    txMetaDataSignatures: List[TxMetadataSignature]


class MessagePayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tenantId: UUID
    request_type: Annotated[RequestType, Field(alias="type")]
    algorithm: Algorithm
    signingDeviceKeyId: str
    keyId: UUID
    messagesToSign: List[MessageToSign]
    requestId: Optional[UUID] = None
    txId: Optional[UUID] = None
    timestamp: Optional[int] = None
    version: Optional[str] = None
    metadata: Optional[Dict] = None


class Message(BaseModel):
    payloadSignatureData: PayloadSignatureData
    payload: Json[MessagePayload]

    @field_serializer("payload")
    def serialize_payload(self, payload: MessagePayload) -> str:
        return payload.model_dump_json()


class TransportMetadata(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    requestId: UUID
    request_type: Annotated[RequestType, Field(alias="type")]


class MessageEnvelope(BaseModel):
    message: Message
    transportMetadata: TransportMetadata


class MessagesRequest(BaseModel):
    messages: List[MessageEnvelope]


class SignedMessage(BaseModel):
    message: str
    signature: str
    index: int


# Sum type?
class MessageResponse(BaseModel):
    signedMessages: Optional[List[SignedMessage]] = None
    errorMessage: Optional[str] = None


class MessageStatus(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    response_type: Annotated[ResponseType, Field(alias="type")]
    status: MessageState
    requestId: UUID
    response: MessageResponse


class MessagesStatusResponse(BaseModel):
    statuses: List[MessageStatus]


class Error(BaseModel):
    code: str
    message: str
