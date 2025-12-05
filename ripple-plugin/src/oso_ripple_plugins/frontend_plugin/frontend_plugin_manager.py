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
        self.vault_id = os.environ["VAULTID"]

        self.seed = os.environ.get("SEED", "")

        self.root_cert_b64 = os.environ.get("ROOTCERT")
        with tempfile.NamedTemporaryFile(delete=False) as root_cert_file:
            self.verify = self._write_root_cert(root_cert_file)

        if "TOKEN_EXP" not in os.environ:
            raise errors.ConfigError("TOKEN_EXP not found")
        self.token_exp = os.environ.get("TOKEN_EXP")

        self.token_exp_in_secs = utils.parse_wait_time(self.token_exp)
        if self.token_exp_in_secs == 0:
            raise errors.ConfigError("TOKEN_EXP format is invalid")

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

    def bulk_download(self) -> list:
        self.logger.info("Performing bulk download from frontend")
        token = self.get_token()
        url = f"https://{self.hmz_api_hostname}/v1/vaults/{self.vault_id}/operations/prepared"
        response = requests.get(
            url=url,
            headers={"Authorization": "Bearer " + token},
            stream=True,
            verify=self.verify,
        )
        response.raise_for_status()
        vault_json = response.json()
        self.logger.info("Bulk download finished successfully")

        empty_content = {
            "vaultId": "",
            "accounts": [],
            "transactions": [],
            "manifests": [],
        }

        def write_document_set(documents, content_key: str, id_key: str):
            for item in vault_json.get(content_key, []):
                self.logger.info(
                    f"Saving document from {content_key} for bulk download"
                )

                try:
                    document_id = item.get(id_key)
                    self.logger.info(f"Saving document {document_id} for bulk download")

                    content = copy.deepcopy(empty_content)
                    content["vaultId"] = vault_json["vaultId"]
                    content.setdefault(content_key, []).append(item)

                    # Encrypt content
                    if len(self.seed) > 0:
                        data = crypt.encrypt(json.dumps(content), self.seed)
                    else:
                        data = json.dumps(content)

                    documents.append(
                        {"id": document_id, "content": data, "metadata": ""}
                    )

                    self.logger.info(
                        f"Successfully saved document {document_id} for bulk download"
                    )
                except Exception as e:
                    self.logger.exception(e)
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
        vaults = []
        transactions = []
        accounts = []
        manifests = []

        self.logger.info("Saving documents for bulk upload")
        for document in documents:
            try:
                document_id = document["id"]
                self.logger.info(f"Saving document {document_id} for bulk upload")
                # Decrypt content
                if len(self.seed) > 0:
                    contents = json.loads(crypt.decrypt(document["content"], self.seed))
                else:
                    contents = json.loads(document["content"])

                transactions.extend(contents.get("transactions", []))
                accounts.extend(contents.get("accounts", []))
                manifests.extend(contents.get("manifests", []))
                vaults.extend(contents.get("vaults", []))

                self.logger.info(
                    f"Successfully saved document {document_id} for bulk upload"
                )
            except Exception as e:
                self.logger.exception(e)
                continue

        content = {
            "accounts": accounts,
            "transactions": transactions,
            "manifests": manifests,
            "vaults": vaults,
        }

        self.logger.info("Performing bulk upload to frontend")
        token = self.get_token()
        try:
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as vault_file:
                json.dump(content, vault_file)

            files = {"files": open(vault_file.name, "rb")}
            response = requests.post(
                url=f"https://{self.hmz_api_hostname}/v1/vaults/operations/signed",
                headers={"Authorization": "Bearer " + token},
                files=files,
                verify=self.verify,
            )
            response.raise_for_status()
        except Exception as e:
            raise e
        finally:
            os.remove(vault_file.name)
        self.logger.info("Bulk upload finished successfully")

    def backend_status(self):
        pass
