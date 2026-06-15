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
import logging
import os
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

_FILENAME = "signing_keys.json"
_WRAPPING_KEY_FILENAME = "wrapping_key.json"


class SigningKeyStore:
    """Persists imported GREP11 key blobs and the EKMF wrapping key bundle
    across pod restarts between operator iterations."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.mkdir(parents=True, exist_ok=True)
        self._keys: dict[str, dict] = self._load()

    def save_keys(self, keys: list[dict]) -> None:
        """Atomically persist imported key blobs.

        Each entry has key_label, key_type, and encrypted_key (GREP11 key blob).
        """
        data = {}
        for key in keys:
            data[key["key_label"]] = {
                "key_type": key["key_type"],
                "encrypted_key": base64.b64encode(key["encrypted_key"]).decode(),
            }

        self._atomic_write(self._path / _FILENAME, data)
        self._keys = data
        logger.info("Saved %d signing key(s) to keystore", len(data))

    def save_wrapping_key(self, wrapping_key: dict) -> None:
        self._atomic_write(self._path / _WRAPPING_KEY_FILENAME, wrapping_key)
        logger.info("Saved wrapping key %s to keystore", wrapping_key.get("key_id"))

    def load_wrapping_key(self) -> dict | None:
        target = self._path / _WRAPPING_KEY_FILENAME
        if not target.is_file():
            return None
        with open(target) as f:
            data = json.load(f)
        logger.info("Loaded wrapping key %s from keystore", data.get("key_id"))
        return data

    def _atomic_write(self, target: Path, data: dict) -> None:
        fd, tmp = tempfile.mkstemp(dir=self._path, suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(data, f)
            os.replace(tmp, target)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    def get_all_keys(self) -> list[tuple[str, str, bytes]]:
        """Return stored keys as (key_label, key_type, key_blob) tuples."""
        result = []
        for key_label, entry in self._keys.items():
            blob = base64.b64decode(entry["encrypted_key"])
            result.append((key_label, entry["key_type"], blob))
        return result

    def _load(self) -> dict[str, dict]:
        target = self._path / _FILENAME
        if not target.is_file():
            return {}
        with open(target) as f:
            data = json.load(f)
        logger.info("Loaded %d signing key(s) from keystore", len(data))
        return data
