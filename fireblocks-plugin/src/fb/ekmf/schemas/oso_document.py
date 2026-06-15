#
# (c) Copyright IBM Corp. 2026
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

from __future__ import annotations

import base64
import json
import uuid
from enum import StrEnum
from typing import Annotated, Any, Generic, Literal, TypeAlias, TypeVar

from pydantic import (
    BaseModel,
    BeforeValidator,
    PlainSerializer,
    field_serializer,
    field_validator,
    model_validator,
)

from .parser import parse_xml
from .simple_exchange import SimpleExchangeModel

Base64Bytes = Annotated[
    bytes,
    BeforeValidator(lambda v: base64.b64decode(v) if isinstance(v, str) else v),
    PlainSerializer(lambda v: base64.b64encode(v).decode(), return_type=str),
]

HexBytes = Annotated[
    bytes,
    BeforeValidator(lambda v: bytes.fromhex(v) if isinstance(v, str) else v),
    PlainSerializer(lambda v: v.hex(), return_type=str),
]


class WrappingKeyContent(BaseModel):
    key_id: uuid.UUID
    public_key: Base64Bytes
    key_hash: HexBytes


class EkmfPayloadContent(BaseModel):
    wrapping_key_id: uuid.UUID
    transport_key: SimpleExchangeModel
    payload: SimpleExchangeModel

    @field_validator("transport_key", "payload", mode="before")
    @classmethod
    def _decode_base64_xml(cls, v: Any) -> Any:
        if isinstance(v, str):
            return parse_xml(base64.b64decode(v))
        return v

    @field_serializer("transport_key", "payload")
    @classmethod
    def _encode_base64_xml(cls, v: SimpleExchangeModel) -> str:
        return base64.b64encode(v.raw_xml).decode()


class ImportedKey(BaseModel):
    key_label: str
    hash: HexBytes
    checksum: HexBytes


class ImportResultContent(BaseModel):
    keys: list[ImportedKey]


class DocumentType(StrEnum):
    INIT = "init"
    WRAPPING_KEY = "wrapping_key"
    EKMF_PAYLOAD = "ekmf_payload"
    IMPORT_RESULT = "import_result"


class InitAddonMeta(BaseModel):
    document_type: Literal[DocumentType.INIT] = DocumentType.INIT


class WrappingKeyAddonMeta(BaseModel):
    document_type: Literal[DocumentType.WRAPPING_KEY] = DocumentType.WRAPPING_KEY


class EkmfPayloadAddonMeta(BaseModel):
    document_type: Literal[DocumentType.EKMF_PAYLOAD] = DocumentType.EKMF_PAYLOAD


class ImportResultAddonMeta(BaseModel):
    document_type: Literal[DocumentType.IMPORT_RESULT] = DocumentType.IMPORT_RESULT


AddonMetaT = TypeVar("AddonMetaT")


class EkmfMetadata(BaseModel, Generic[AddonMetaT]):
    ekmf_addon: AddonMetaT


ContentT = TypeVar("ContentT")
MetadataT = TypeVar("MetadataT")


class OSODocument(BaseModel, Generic[ContentT, MetadataT]):
    id: str
    content: ContentT
    metadata: MetadataT

    @model_validator(mode="before")
    @classmethod
    def _parse_stringified_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for field in ("content", "metadata"):
                value = data.get(field)
                if isinstance(value, str):
                    try:
                        parsed = json.loads(value)
                        if isinstance(parsed, dict):
                            data[field] = parsed
                    except (json.JSONDecodeError, ValueError):
                        pass
        return data

    @field_serializer("content", "metadata")
    @classmethod
    def _stringify_field(cls, value: Any) -> Any:
        if isinstance(value, BaseModel):
            return value.model_dump_json()
        return value


InitDocument: TypeAlias = OSODocument[str, EkmfMetadata[InitAddonMeta]]
WrappingKeyDocument: TypeAlias = OSODocument[
    WrappingKeyContent, EkmfMetadata[WrappingKeyAddonMeta]
]
EkmfPayloadDocument: TypeAlias = OSODocument[
    EkmfPayloadContent, EkmfMetadata[EkmfPayloadAddonMeta]
]
ImportResultDocument: TypeAlias = OSODocument[
    ImportResultContent, EkmfMetadata[ImportResultAddonMeta]
]


class WrappingKey(BaseModel):
    key_id: uuid.UUID
    private_key: Base64Bytes


class KeygenResult(BaseModel):
    result: WrappingKeyDocument
    wrapping_key: WrappingKey


class WrapRequest(BaseModel):
    document: EkmfPayloadDocument
    wrapping_key: WrappingKey


class KeyBlob(BaseModel):
    key_label: str
    encrypted_key: Base64Bytes


class ImportKeysResult(BaseModel):
    result: ImportResultDocument
    key_blobs: list[KeyBlob]
