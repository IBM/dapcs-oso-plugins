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
from typing import Dict, List

import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning

from oso_ripple_plugins.common import crypt, errors

urllib3.disable_warnings(InsecureRequestWarning)


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

        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Cold-bridge endpoints configured: {self.vault_bridge_map}")

    def backend_status(self):
        # Check status on all bridge endpoints
        status_errors = []
        for vault_id, endpoint in self.vault_bridge_map.items():
            try:
                response = requests.get(f"{endpoint}/v1/feed/status", timeout=3)
                response.raise_for_status()
            except Exception as e:
                status_errors.append(f"Bridge for vault {vault_id} ({endpoint}): {e}")
        if status_errors:
            raise Exception("; ".join(status_errors))

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
            self.logger.info(f"Bulk download from bridge {endpoint} finished successfully")

            for section, id_key, type_name in sections:
                for item in response_json.get(section, []):
                    # Encrypt if seed is set
                    if self.seed and "signedPayload" in item:
                        item["signedPayloadCiphered"] = crypt.encrypt(item["signedPayload"], self.seed)
                        del item["signedPayload"]

                    # Build content and metadata
                    content = {
                        "accounts": [item] if section == "accounts" else [],
                        "transactions": [item] if section == "transactions" else [],
                        "manifests": [item] if section == "manifests" else [],
                        "rewraps": [item] if section == "rewraps" else [],
                        "vaults": [],
                    }

                    documents.append({
                        "id": item[id_key],
                        "content": json.dumps(content),
                        "metadata": "",
                    })

        self.logger.info("Bulk download finished successfully")
        return documents

    def bulk_upload(self, documents):
        v_tx= {}
        v_ac= {}
        v_ma= {}
        v_rw= {}

        self.logger.info("Saving documents for bulk upload")
        for document in documents:
            try:
                contents = json.loads(document["content"])
                vaultid= contents.get("vaultId")

                if vaultid not in v_tx:
                    v_tx[vaultid]=[]
                    v_ac[vaultid]=[]
                    v_ma[vaultid]=[]
                    v_rw[vaultid]=[]
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
                            item["signedPayload"] = crypt.decrypt(item["signedPayloadCiphered"], self.seed)
                            del item["signedPayloadCiphered"]
                        storage.append(item)

                self.logger.info(f"Saving document {document['id']} for bulk upload")

            except Exception as e:
                self.logger.exception(e)
                continue

        self.logger.info("Performing bulk upload to backend")
        for vaultid in v_tx.keys():
            # Route upload to the bridge that owns this vault
            endpoint = self.vault_bridge_map.get(vaultid)
            if not endpoint:
                self.logger.error(f"No bridge endpoint found for vault {vaultid}, skipping")
                continue

            content = {
                "vaultId": vaultid,
                "accounts": v_ac[vaultid],
                "transactions": v_tx[vaultid],
                "manifests": v_ma[vaultid],
                "rewraps": v_rw[vaultid],
            }
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
            except requests.HTTPError as http_err:
                self.logger.error(f"HTTP error uploading vault {vaultid}: {http_err}")
            except Exception as err:
                self.logger.error(f"Unexpected error uploading vault {vaultid}: {err}")
            finally:
                if vault_file_name:
                    os.remove(vault_file_name)

        self.logger.info("Bulk upload finished successfully")
