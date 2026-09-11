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


import copy
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
)


class BackendPluginManager:
    def __init__(self):
        self.cold_bridge_endpoint = os.environ.get(
            "COLD_BRIDGE_ENDPOINT", "http://localhost:8080"
        )
        self.seed = os.environ.get("SEED", "")
        self.state_file = os.environ.get(
            "SIGNING_STATE_FILE", "/tmp/backend_signing_state.json"
        )
        self.signing_stall_secs = int(os.environ.get("SIGNING_STALL_SECS", "300"))

        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.logger.info(
            f"Cold-bridge endpoint configured as: {self.cold_bridge_endpoint}"
        )

    def _load_signing_state(self):
        try:
            with open(self.state_file) as f:
                return json.load(f)
        except (OSError, ValueError):
            return None

    def _save_signing_state(self, state):
        try:
            with open(self.state_file, "w") as f:
                json.dump(state, f)
        except OSError as e:
            self.logger.error(f"Could not persist signing state: {e}")

    def _clear_signing_state(self):
        try:
            os.remove(self.state_file)
        except OSError:
            pass

    def backend_status(self):
        response = requests.get(
            f"{self.cold_bridge_endpoint}/v1/feed/status",
            timeout=3,
        )
        response.raise_for_status()

        state = self._load_signing_state()
        if state is None:
            return

        try:
            counters = response.json()
        except ValueError:
            self.logger.warning(
                "Cold-bridge status response is not JSON;"
                " skipping signing-progress check"
            )
            return

        expected = state.get("expected", {})
        pending = {}
        shortfall = {}
        for prefix, category in SIGNING_CATEGORIES:
            to_sign = int(counters.get(f"{prefix}ToSign") or 0)
            signed = int(counters.get(f"{prefix}Signed") or 0)
            if to_sign > 0:
                pending[category] = to_sign
            # Guard the window where the cold vault has not yet registered the
            # uploaded feed: all-zero counters right after an upload mean
            # "not started", not "done".
            if signed < int(expected.get(category, 0)):
                shortfall[category] = int(expected.get(category, 0)) - signed

        if not pending and not shortfall:
            self.logger.info(f"Signing complete, feed counters: {counters}")
            self._clear_signing_state()
            return

        now = time.time()
        if counters != state.get("last_counters"):
            state["last_counters"] = counters
            state["last_progress_at"] = now
            self._save_signing_state(state)
        elif now - state.get("last_progress_at", now) > self.signing_stall_secs:
            self.logger.error(
                f"Signing stalled for over {self.signing_stall_secs}s with"
                f" operations outstanding (pending={pending},"
                f" shortfall={shortfall}, counters={counters});"
                " reporting ready with a partial result set"
            )
            self._clear_signing_state()
            return

        self.logger.info(f"Signing in progress, feed counters: {counters}")
        raise errors.SigningInProgress(f"pending={pending} shortfall={shortfall}")

    def bulk_download(self) -> List[Dict]:
        response = requests.get(
            f"{self.cold_bridge_endpoint}/v1/feed/download?clean=True"
        )
        response.raise_for_status()
        response_json = response.json()

        self.logger.info("Bulk download finished successfully")

        empty_content = {
            "accounts": [],
            "transactions": [],
            "manifests": [],
            "vaults": [],
        }

        def write_document_set(documents, content_key: str, id_key: str):
            for item in response_json.get(content_key, []):
                self.logger.debug(
                    f"Saving document from {content_key} for bulk download"
                )

                try:
                    document_id = item.get(id_key)
                    self.logger.debug(f"Saving document {document_id} for bulk download")

                    content = copy.deepcopy(empty_content)
                    content.setdefault(content_key, []).append(item)

                    # Encrypt content
                    if len(self.seed) > 0:
                        data = crypt.encrypt(json.dumps(content), self.seed)
                    else:
                        data = json.dumps(content)

                    documents.append(
                        {"id": item.get(id_key), "content": data, "metadata": ""}
                    )

                    self.logger.debug(
                        f"Successfully saved document {document_id} for bulk download"
                    )
                except Exception as err:
                    self.logger.exception(err)
                    continue

        documents = []
        for content_key, id_key in [
            ("transactions", "transactionId"),
            ("accounts", "accountId"),
            ("manifests", "manifestId"),
        ]:
            write_document_set(documents, content_key, id_key)

        return documents

    def bulk_upload(self, documents):
        vault_id = None
        transactions = []
        accounts = []
        manifests = []

        self.logger.info("Saving documents for bulk upload")
        for document in documents:
            try:
                document_id = document["id"]
                self.logger.debug(f"Saving document {document_id} for bulk upload")

                # Decrypt content
                if len(self.seed) > 0:
                    contents = json.loads(crypt.decrypt(document["content"], self.seed))
                else:
                    contents = json.loads(document["content"])

                transactions.extend(contents.get("transactions", []))
                accounts.extend(contents.get("accounts", []))
                manifests.extend(contents.get("manifests", []))

                if vault_id is None:
                    vault_id = contents.get("vaultId")

                self.logger.debug(
                    f"Successfully saved document {document_id} for bulk upload"
                )
            except Exception as e:
                self.logger.exception(e)
                continue

        if not vault_id:
            return Exception("Could not get vault id")

        content = {
            "vaultId": vault_id,
            "accounts": accounts,
            "transactions": transactions,
            "manifests": manifests,
        }

        # Remember how much work was handed to the cold vault so that
        # backend_status() can hold off the output bridge (503) until the
        # feed counters show everything has been signed.
        now = time.time()
        self._save_signing_state(
            {
                "expected": {
                    "transactions": len(transactions),
                    "accounts": len(accounts),
                    "manifests": len(manifests),
                },
                "uploaded_at": now,
                "last_progress_at": now,
                "last_counters": None,
            }
        )

        self.logger.info("Performing bulk upload to backend")

        try:
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as vault_file:
                json.dump(content, vault_file)

            files = {"files": (vault_id, open(vault_file.name, "rb"))}
            response = requests.post(
                url=f"{self.cold_bridge_endpoint}/v1/feed/upload",
                files=files,
            )
            response.raise_for_status()
        except Exception as e:
            raise e
        finally:
            os.remove(vault_file.name)

        self.logger.info("Bulk upload finished successfully")
