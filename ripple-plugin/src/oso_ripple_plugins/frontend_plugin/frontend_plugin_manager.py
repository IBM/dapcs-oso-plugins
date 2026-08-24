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


import base64
import copy
import io
import json
import logging
import os
import sys
import tempfile
import time
import uuid
from functools import lru_cache
from typing import IO, Tuple, Union

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from oso_ripple_plugins.common import crypt, errors, utils


class FrontendPluginManager:
    def __init__(self):
        if "SK" not in os.environ:
            raise errors.ConfigError("SK not found")
        private_key_b64 = os.environ["SK"]
        private_key_decoded = base64.b64decode(private_key_b64)
        self.private_key = load_pem_private_key(private_key_decoded, password=None)
        self.public_key = base64.b64encode(
            self.private_key.public_key().public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        ).decode("utf-8")

        if "HMZ_AUTH_HOSTNAME" not in os.environ:
            raise errors.ConfigError("HMZ_AUTH_HOSTNAME not found")
        self.hmz_auth_hostname = os.environ["HMZ_AUTH_HOSTNAME"]

        if "HMZ_API_HOSTNAME" not in os.environ:
            raise errors.ConfigError("HMZ_API_HOSTNAME not found")
        self.hmz_api_hostname = os.environ["HMZ_API_HOSTNAME"]

        if "VAULTID" not in os.environ:
            raise errors.ConfigError("VAULTID not found")
        self.vaultids = os.environ["VAULTID"].split()

        self.seed = os.environ.get("SEED", "")

        self.root_cert_b64 = os.environ.get("ROOTCERT")
        with tempfile.NamedTemporaryFile(delete=False) as root_cert_file:
            self.verify = self._write_root_cert(root_cert_file)

        if "TOKEN_EXP" not in os.environ:
            raise errors.ConfigError("TOKEN_EXP not found")
        self.token_exp = os.environ["TOKEN_EXP"]

        self.token_exp_in_secs = utils.parse_wait_time(self.token_exp)
        if self.token_exp_in_secs == 0:
            raise errors.ConfigError("TOKEN_EXP format is invalid")

        try:
            self.batch_size = int(os.environ.get("BATCH_UPLOAD_SIZE", 20))
        except ValueError:
            raise errors.ConfigError("BATCH_UPLOAD_SIZE must be a valid integer")

        if self.batch_size <= 0:
            raise errors.ConfigError("BATCH_UPLOAD_SIZE must be a positive integer")

        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _sign(self, challenge: str = str(uuid.uuid4())) -> bytes:
        """
        Sign the challenge string and then convert the signature into a DER format.

        Parameters:

            challenge (`str`):

                An unique challenge string.

        Returns:

            `bytes`:

                A DER encoded signature as a byte string.
        """
        if isinstance(self.private_key, ed25519.Ed25519PrivateKey):
            """
            An ED25519 signature produces a 64-byte sequence which has to be converted
            into the correct DER structure:

            0x30 : DER Composite structure header
            0x44 : length (68) of following payload
            0x02 : type of payload (int)
            0x20 : length (32) of (int) payload
                 : 32-byte length payload (r), first half of ``hexsig``
            0x02 : type of payload (int)
            0x20 : length (32) of (int) payload
                 : 32-byte length payload (s), second half of ``hexsig``
            """
            hexsig = self.private_key.sign(
                bytes(challenge, "utf-8"),
            ).hex()
            return bytes.fromhex("30440220" + hexsig[:64] + "0220" + hexsig[64:])

        elif isinstance(self.private_key, ec.EllipticCurvePrivateKey):
            return self.private_key.sign(
                data=bytes(challenge, "utf-8"),
                signature_algorithm=ec.ECDSA(hashes.SHA256()),
            )

        else:
            raise Exception(f"Key type not supported: {type(self.private_key)}")

    @lru_cache()  # Cache result - token + timestamp
    def _get_token(self) -> Tuple[str, float]:
        self.logger.info("Generating new JWT access token...")
        challenge = str(uuid.uuid4())
        signature = self._sign(challenge)
        data = {
            "client_id": "customer_api",
            "grant_type": "password",
            "challenge": challenge,
            "public_key": self.public_key,
            "signature": base64.b64encode(signature).decode("utf-8"),
        }

        response = requests.post(
            f"https://{self.hmz_auth_hostname}/token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            verify=self.verify,
        )

        response.raise_for_status()
        response_json = response.json()
        token = response_json.get("access_token")
        if not token:
            raise Exception("Could not get token from response json")

        self.logger.info("Successfully generated new JWT access token")
        return token, time.time()

    def _write_root_cert(self, root_cert_file: IO[bytes]) -> Union[str, bool]:
        if self.root_cert_b64:
            rootcert = base64.b64decode(self.root_cert_b64)
            root_cert_file.write(rootcert)
            root_cert_file.seek(0)
            return root_cert_file.name
        else:
            return True

    def get_token(self) -> str:
        self.logger.info("Obtaining JWT access token...")
        token, exp_time = self._get_token()
        if (
            time.time() - (exp_time - int(os.environ.get("TOKEN_EXP_BUFF", 10)))
        ) > self.token_exp_in_secs:  # gen new token if within 10 secs of expiry
            self._get_token.cache_clear()
            token, exp_time = self._get_token()
        self.logger.info("Successfully obtained JWT access token")
        return token

    def _write_document_set(self, documents: list, vault_json: dict, vaultid: str,
                            empty_content: dict, content_key: str, id_key: str) -> None:
        """Append OSO documents built from one content section of a vault response."""
        for item in vault_json.get(content_key, []):
            try:
                document_id = item.get(id_key)

                if not document_id:
                    self.logger.warning(
                        "Missing %s in vault %s for %s",
                        id_key,
                        vaultid,
                        content_key,
                    )
                    continue

                self.logger.info(
                    "Saving document %s from %s (vault %s)",
                    document_id,
                    content_key,
                    vaultid,
                )

                content = copy.deepcopy(empty_content)
                content.setdefault(content_key, []).append(item)

                # Encrypt content if seed provided
                if self.seed:
                    for section in ["transactions", "manifests", "accounts"]:
                        for section_item in content.get(section, []):
                            if "signedPayload" in section_item:
                                section_item["signedPayloadCiphered"] = crypt.encrypt(
                                    section_item["signedPayload"],
                                    self.seed,
                                )
                                del section_item["signedPayload"]

                data = json.dumps(content)

                documents.append(
                    {
                        "id": document_id,
                        "content": data,
                        "metadata": "",
                    }
                )

                self.logger.info(
                    "Successfully saved document %s (vault %s)",
                    document_id,
                    vaultid,
                )

            except Exception:
                self.logger.exception(
                    "Failed processing document in vault %s (%s)",
                    vaultid,
                    content_key,
                )
                continue

    def bulk_download(self) -> list:
        self.logger.info("Performing bulk download from frontend")
        token = self.get_token()

        documents = []

        for vaultid in self.vaultids:
            url = f"https://{self.hmz_api_hostname}/v1/vaults/{vaultid}/operations/prepared"

            try:
                response = requests.get(
                    url=url,
                    headers={"Authorization": f"Bearer {token}"},
                    verify=self.verify,
                    timeout=30,
                )
            except requests.exceptions.RequestException as e:
                self.logger.error(
                    "Network error while downloading vault %s: %s",
                    vaultid,
                    str(e),
                )
                continue

            status = response.status_code

            # ---- Handle non-success HTTP codes ----
            if not (200 <= status < 300):
                self.logger.error(
                    "Download rejected for vault %s: status=%s body=%s",
                    vaultid,
                    status,
                    response.text[:2000],
                )
                continue

            # ---- Handle 204 - empty response ----
            if status == 204 or not response.content:
                self.logger.info(
                    "No content returned for vault %s (status=%s)",
                    vaultid,
                    status,
                )
                continue

            # ---- Parse JSON safely ----
            try:
                vault_json = response.json()
            except ValueError:
                self.logger.error(
                    "Invalid JSON for vault %s: %s",
                    vaultid,
                    response.text[:2000],
                )
                continue

            self.logger.info("Bulk download finished successfully for vault %s", vaultid)

            empty_content = {
                "vaultId": vault_json.get("vaultId", vaultid),
                "accounts": [],
                "transactions": [],
                "manifests": [],
            }

            for content_key, id_key in [
                ("transactions", "transactionId"),
                ("accounts", "accountId"),
                ("manifests", "manifestId"),
            ]:
                self._write_document_set(
                    documents, vault_json, vaultid, empty_content, content_key, id_key
                )

        return documents

    def bulk_upload(self, documents):
        BATCH_SIZE = self.batch_size

        def send_batch(content):
            self.logger.info(
                "Performing bulk upload to harmonize (batch size=%s)",
                len(content.get("transactions", []))
                + len(content.get("accounts", []))
                + len(content.get("manifests", [])),
            )

            try:
                token = self.get_token()

                json_bytes = json.dumps(content).encode("utf-8")
                file_obj = io.BytesIO(json_bytes)

                files = {
                    "files": ("batch.json", file_obj, "application/json")
                }

                response = requests.post(
                    url=f"https://{self.hmz_api_hostname}/v1/vaults/operations/signed",
                    headers={
                        "Authorization": f"Bearer {token}"
                        # DO NOT set Content-Type manually
                    },
                    files=files,
                    verify=self.verify,
                    timeout=60,
                )

            except requests.exceptions.RequestException as e:
                self.logger.error("Network error during bulk upload: %s", str(e))
                raise

            status = response.status_code

            if not (200 <= status < 300):
                self.logger.error(
                    "Backend rejected batch: status=%s body=%s",
                    status,
                    response.text[:2000],  # prevent huge logs
                )
                response.raise_for_status()

            self.logger.info("Batch upload successful (status=%s)", status)

        # ---- Batch accumulators ----
        vaults = []
        transactions = []
        accounts = []
        manifests = []
        doc_count = 0

        self.logger.info("Saving documents for bulk upload")

        for document in documents:
            try:
                document_id = document.get("id")

                if not document_id:
                    self.logger.warning("Skipping document without id")
                    continue

                self.logger.info(
                    "Processing document %s for bulk upload",
                    document_id,
                )

                contents = json.loads(document["content"])

                # Decrypt if needed
                if self.seed:
                    for section in ("transactions", "accounts", "manifests"):
                        for item in contents.get(section, []):
                            if "signedPayloadCiphered" in item:
                                item["signedPayload"] = crypt.decrypt(
                                    item["signedPayloadCiphered"],
                                    self.seed,
                                )
                                del item["signedPayloadCiphered"]

                transactions.extend(contents.get("transactions", []))
                accounts.extend(contents.get("accounts", []))
                manifests.extend(contents.get("manifests", []))
                vaults.extend(contents.get("vaults", []))

                doc_count += 1

                # Flush every BATCH_SIZE documents
                if doc_count >= BATCH_SIZE:
                    try:
                        send_batch({
                            "accounts": accounts,
                            "transactions": transactions,
                            "manifests": manifests,
                            "vaults": vaults,
                        })
                    except Exception:
                        self.logger.exception("Batch flush failed; continuing")
                    finally:
                        # Always reset accumulators so later batches are not polluted
                        vaults = []
                        transactions = []
                        accounts = []
                        manifests = []
                        doc_count = 0

                self.logger.info(
                    "Successfully processed document %s",
                    document_id,
                )

            except Exception:
                self.logger.exception(
                    "Failed processing document %s",
                    document.get("id"),
                )
                continue

        # ---- Send remaining documents ----
        if doc_count > 0:
            send_batch({
                "accounts": accounts,
                "transactions": transactions,
                "manifests": manifests,
                "vaults": vaults,
            })

        self.logger.info("Bulk upload finished successfully")

    def backend_status(self):
        pass
