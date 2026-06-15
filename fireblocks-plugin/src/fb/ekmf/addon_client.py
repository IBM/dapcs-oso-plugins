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

import json
import os
from typing import Any

import requests

from .schemas import (
    DocumentType,
    EkmfPayloadContent,
    EkmfPayloadDocument,
    ImportKeysResult,
    ImportResultContent,
    ImportResultDocument,
    InitDocument,
    KeygenResult,
    WrappingKey,
    WrappingKeyContent,
    WrappingKeyDocument,
    WrapRequest,
)

ENV_VAR = "EKMF_ADDON_PORT"


def parse_ekmf_document_type(doc: dict[str, Any]) -> DocumentType | None:
    metadata_raw = doc.get("metadata")
    if not metadata_raw:
        return None
    if isinstance(metadata_raw, str):
        try:
            metadata = json.loads(metadata_raw)
        except (json.JSONDecodeError, ValueError):
            return None
    elif isinstance(metadata_raw, dict):
        metadata = metadata_raw
    else:
        return None
    addon_meta = metadata.get("ekmf_addon")
    if not isinstance(addon_meta, dict):
        return None
    doc_type = addon_meta.get("document_type")
    try:
        return DocumentType(doc_type)
    except ValueError:
        return None


class EkmfAddonError(Exception):
    def __init__(self, message: str, status_code: int = 0, body: Any = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class EkmfAddonClient:
    def __init__(self, base_url: str | None = None, timeout: float = 30.0) -> None:
        if base_url:
            self._base_url = base_url.rstrip("/")
        else:
            port = os.environ.get(ENV_VAR)
            if not port:
                raise RuntimeError(f"{ENV_VAR} is not set; cannot reach EKMF Add-On")
            self._base_url = f"http://localhost:{port}"
        self._timeout = timeout

    def init_import(self) -> InitDocument:
        data = self._post("/addon/ekmf/import/init")
        return InitDocument.model_validate(data)

    def extract_key(self, doc: WrappingKeyDocument) -> WrappingKeyContent:
        data = self._post("/addon/ekmf/import/key", json=doc.model_dump(mode="json"))
        return WrappingKeyContent.model_validate(data)

    def package_payload(self, content: EkmfPayloadContent) -> EkmfPayloadDocument:
        data = self._post(
            "/addon/ekmf/import/payload", json=content.model_dump(mode="json")
        )
        return EkmfPayloadDocument.model_validate(data)

    def extract_result(self, doc: ImportResultDocument) -> ImportResultContent:
        data = self._post("/addon/ekmf/import/result", json=doc.model_dump(mode="json"))
        return ImportResultContent.model_validate(data)

    def keygen(self) -> KeygenResult:
        data = self._post("/addon/ekmf/import/keygen")
        return KeygenResult.model_validate(data)

    def wrap(
        self, payload_doc: EkmfPayloadDocument, wrapping_key: WrappingKey
    ) -> ImportKeysResult:
        request = WrapRequest(document=payload_doc, wrapping_key=wrapping_key)
        data = self._post(
            "/addon/ekmf/import/wrap", json=request.model_dump(mode="json")
        )
        return ImportKeysResult.model_validate(data)

    def _post(self, path: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        try:
            response = requests.post(url, timeout=self._timeout, **kwargs)
        except requests.RequestException as exc:
            raise EkmfAddonError(f"add-on call failed: {exc}") from exc

        if response.status_code >= 400:
            raise EkmfAddonError(
                f"add-on returned {response.status_code}",
                status_code=response.status_code,
                body=self._safe_json(response),
            )
        return self._safe_json(response)

    @staticmethod
    def _safe_json(response: requests.Response) -> dict[str, Any]:
        try:
            return response.json()
        except ValueError:
            return {"raw": response.text}
