# Copyright (c) 2025 IBM Corp.
# All rights reserved.
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


import json
import logging
import os
import sys
import tempfile
import time
from typing import Dict, List

import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning

from oso_ripple_plugins.common import crypt, errors

urllib3.disable_warnings(InsecureRequestWarning)


# (counter prefix in the cold-bridge status payload, category key in uploads)
SIGNING_CATEGORIES = (
    ("transaction", "transactions"),
    ("account", "accounts"),
    ("manifest", "manifests"),
    ("rewrap", "rewraps"),
)


class BackendPluginManager:
    def __init__(self):
        # Build vault_id -> bridge endpoint map from indexed env vars:
        # Vault__Ids__0, Vault__Ids__1, ... and COLD_BRIDGE_ENDPOINT__0, COLD_BRIDGE_ENDPOINT__1, ...
        self.vault_bridge_map = {}
        i = 0
        while True:
            vault_id = os.environ.get(f"Vault__Ids__{i}")
            endpoint = os.environ.get(f"COLD_BRIDGE_ENDPOINT__{i}")
            if vault_id is None or endpoint is None:
                break
            self.vault_bridge_map[vault_id] = endpoint
            i += 1

        self.seed = os.environ.get("OSOENCRYPTIONPASS", "")
        self.signing_stall_secs = int(os.environ.get("SIGNING_STALL_SECS", "300"))

        # vault_id -> {"expected": {category: count}, "uploaded_at": float,
        #              "last_progress_at": float, "last_counters": dict | None},
        # recorded by bulk_upload() after each successful per-vault upload and
        # consumed by backend_status(). The backend runs a single gunicorn
        # worker, so instance state is shared by all requests.
        self._signing_state = {}

        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Cold-bridge endpoints configured: {self.vault_bridge_map}")

    def backend_status(self):
        # Check status on all bridge endpoints and hold the plugin at 503
        # (SigningInProgress) until every vault that received an upload shows
        # its feed fully signed, so the output bridge cannot harvest early.
        status_errors = []
        in_progress = {}
        for vault_id, endpoint in self.vault_bridge_map.items():
            try:
                response = requests.get(f"{endpoint}/v1/feed/status", timeout=3)
                response.raise_for_status()
            except Exception as e:
                status_errors.append(f"Bridge for vault {vault_id} ({endpoint}): {e}")
                continue

            state = self._signing_state.get(vault_id)
            if state is None:
                continue

            try:
                counters = response.json()
            except ValueError:
                self.logger.warning(
                    f"Cold-bridge status response for vault {vault_id} is not"
                    " JSON; skipping signing-progress check"
                )
                continue

            expected = state["expected"]
            pending = {}
            shortfall = {}
            for prefix, category in SIGNING_CATEGORIES:
                to_sign = int(counters.get(f"{prefix}ToSign") or 0)
                signed = int(counters.get(f"{prefix}Signed") or 0)
                if to_sign > 0:
                    pending[category] = to_sign
                # Guard the window where the cold vault has not yet registered
                # the uploaded feed: all-zero counters right after an upload
                # mean "not started", not "done".
                if signed < int(expected.get(category, 0)):
                    shortfall[category] = int(expected.get(category, 0)) - signed

            if not pending and not shortfall:
                self.logger.info(
                    f"Signing complete for vault {vault_id}, feed counters: {counters}"
                )
                del self._signing_state[vault_id]
                continue

            now = time.time()
            if counters != state["last_counters"]:
                state["last_counters"] = counters
                state["last_progress_at"] = now
            elif now - state["last_progress_at"] > self.signing_stall_secs:
                self.logger.error(
                    f"Signing for vault {vault_id} stalled for over"
                    f" {self.signing_stall_secs}s with operations outstanding"
                    f" (pending={pending}, shortfall={shortfall},"
                    f" counters={counters}); reporting ready with a partial"
                    " result set"
                )
                del self._signing_state[vault_id]
                continue

            in_progress[vault_id] = {"pending": pending, "shortfall": shortfall}

        if status_errors:
            raise Exception("; ".join(status_errors))

        if in_progress:
            self.logger.info(f"Signing in progress: {in_progress}")
            raise errors.SigningInProgress(f"{in_progress}")

    def bulk_download(self) -> List[Dict]:
        documents = []
        sections = [
            ("transactions", "transactionId", "transaction"),
            ("accounts", "accountId", "account"),
            ("manifests", "manifestId", "manifest"),
            ("rewraps", "rewrapSecretMaterialsId", "rewrap"),
        ]

        # Download from all bridge endpoints and merge results
        for vault_id, endpoint in self.vault_bridge_map.items():
            response = requests.get(f"{endpoint}/v1/feed/download?clean=true")
            response.raise_for_status()
            response_json = response.json()
            self.logger.info(
                f"Bulk download from bridge {endpoint} finished successfully"
            )

            for section, id_key, type_name in sections:
                for item in response_json.get(section, []):
                    # Encrypt if seed is set
                    if self.seed and "signedPayload" in item:
                        item["signedPayloadCiphered"] = crypt.encrypt(
                            item["signedPayload"], self.seed
                        )
                        del item["signedPayload"]

                    # Build content and metadata
                    content = {
                        "accounts": [item] if section == "accounts" else [],
                        "transactions": [item] if section == "transactions" else [],
                        "manifests": [item] if section == "manifests" else [],
                        "rewraps": [item] if section == "rewraps" else [],
                        "vaults": [],
                    }

                    documents.append(
                        {
                            "id": item[id_key],
                            "content": json.dumps(content),
                            "metadata": "",
                        }
                    )

        self.logger.info("Bulk download finished successfully")
        return documents

    def bulk_upload(self, documents):
        v_tx = {}
        v_ac = {}
        v_ma = {}
        v_rw = {}

        self.logger.info("Saving documents for bulk upload")
        for document in documents:
            try:
                contents = json.loads(document["content"])
                vaultid = contents.get("vaultId")

                if vaultid not in v_tx:
                    v_tx[vaultid] = []
                    v_ac[vaultid] = []
                    v_ma[vaultid] = []
                    v_rw[vaultid] = []
                # Map sections to their storage dict
                section_map = {
                    "transactions": v_tx[vaultid],
                    "accounts": v_ac[vaultid],
                    "manifests": v_ma[vaultid],
                    "rewraps": v_rw[vaultid],
                }

                for section, storage in section_map.items():
                    for item in contents.get(section, []):
                        if self.seed and "signedPayloadCiphered" in item:
                            item["signedPayload"] = crypt.decrypt(
                                item["signedPayloadCiphered"], self.seed
                            )
                            del item["signedPayloadCiphered"]
                        storage.append(item)

                self.logger.info(f"Saving document {document['id']} for bulk upload")

            except Exception as e:
                self.logger.exception(e)
                continue

        self.logger.info("Performing bulk upload to backend")
        attempted = 0
        failed = []
        for vaultid in v_tx.keys():
            # Route upload to the bridge that owns this vault
            endpoint = self.vault_bridge_map.get(vaultid)
            if not endpoint:
                self.logger.error(
                    f"No bridge endpoint found for vault {vaultid}, skipping"
                )
                continue

            content = {
                "vaultId": vaultid,
                "accounts": v_ac[vaultid],
                "transactions": v_tx[vaultid],
                "manifests": v_ma[vaultid],
                "rewraps": v_rw[vaultid],
            }
            attempted += 1
            vault_file_name = None
            try:
                with tempfile.NamedTemporaryFile(mode="w", delete=False) as vault_file:
                    vault_file_name = vault_file.name
                    json.dump(content, vault_file)

                files = {"files": (vaultid, open(vault_file.name, "rb"))}
                response = requests.post(
                    url=f"{endpoint}/v1/feed/upload",
                    files=files,
                )
                response.raise_for_status()
                self.logger.info(f"Successfully uploaded vault {vaultid}")

                # Remember how much work was handed to this vault so that
                # backend_status() can hold off the output bridge (503) until
                # the feed counters show everything has been signed. Recorded
                # only after a successful upload: a failed vault gets no state
                # and is never gated on.
                now = time.time()
                self._signing_state[vaultid] = {
                    "expected": {
                        "transactions": len(v_tx[vaultid]),
                        "accounts": len(v_ac[vaultid]),
                        "manifests": len(v_ma[vaultid]),
                        "rewraps": len(v_rw[vaultid]),
                    },
                    "uploaded_at": now,
                    "last_progress_at": now,
                    "last_counters": None,
                }
            except requests.HTTPError as http_err:
                self.logger.error(f"HTTP error uploading vault {vaultid}: {http_err}")
                failed.append(vaultid)
            except Exception as err:
                self.logger.error(f"Unexpected error uploading vault {vaultid}: {err}")
                failed.append(vaultid)
            finally:
                if vault_file_name:
                    os.remove(vault_file_name)

        if failed:
            self.logger.error(
                f"Upload failed for vaults {failed}; their documents were not"
                " handed to the cold vault and will not be gated on"
            )
            if len(failed) == attempted:
                raise Exception(f"Bulk upload failed for all vaults: {failed}")

        self.logger.info("Bulk upload finished successfully")
