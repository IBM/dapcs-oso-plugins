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

from threading import Lock
from typing import Any

from .schemas import DocumentType

STATUS_IDLE = "idle"
STATUS_KEYGEN_PENDING = "keygen_pending"
STATUS_KEY_AVAILABLE = "key_available"
STATUS_PAYLOAD_SUBMITTED = "payload_submitted"
STATUS_PROCESSING = "processing"
STATUS_COMPLETED = "completed"


class EkmfStateError(Exception):
    pass


class EkmfImportState:
    def __init__(self) -> None:
        self._lock = Lock()
        self._status: str = STATUS_IDLE
        self._import_id: str | None = None
        self._outbound: list[dict[str, Any]] = []
        self._inbound: dict[DocumentType, dict[str, Any]] = {}
        self._signing_keys: list[dict[str, Any]] = []

    @property
    def status(self) -> str:
        with self._lock:
            return self._status

    @property
    def import_id(self) -> str | None:
        with self._lock:
            return self._import_id

    def start_import(self, import_id: str) -> None:
        with self._lock:
            self._status = STATUS_KEYGEN_PENDING
            self._import_id = import_id
            self._outbound.clear()
            self._inbound.clear()

    def transition(self, new_status: str) -> None:
        with self._lock:
            self._status = new_status

    def reset(self) -> None:
        with self._lock:
            self._status = STATUS_IDLE
            self._import_id = None
            self._outbound.clear()
            self._inbound.clear()

    def enqueue_outbound(self, doc_envelope: dict[str, Any]) -> None:
        with self._lock:
            self._outbound.append(doc_envelope)

    def drain_outbound(self) -> list[dict[str, Any]]:
        with self._lock:
            drained = list(self._outbound)
            self._outbound.clear()
            return drained

    def cache_inbound(self, doc_type: DocumentType, doc: dict[str, Any]) -> None:
        with self._lock:
            self._inbound[doc_type] = doc
            if doc_type == DocumentType.WRAPPING_KEY:
                self._status = STATUS_KEY_AVAILABLE
            elif doc_type == DocumentType.IMPORT_RESULT:
                self._status = STATUS_COMPLETED

    def get_cached(self, doc_type: DocumentType) -> dict[str, Any] | None:
        with self._lock:
            return self._inbound.get(doc_type)

    def set_signing_keys(self, keys: list[dict[str, Any]]) -> None:
        with self._lock:
            self._signing_keys = list(keys)

    @property
    def signing_keys(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._signing_keys)
