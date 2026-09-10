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

import pytest
import requests_mock
from common.certs import component_cert
from requests_toolbelt.multipart import decoder

from oso_ripple_plugins.common import crypt


def test_docs_download(client):
    mock_url = "https://backend/v1/feed/download?clean=true"

    with requests_mock.mock() as m:
        m.get(
            mock_url,
            json={
                "accounts": [
                    {"accountId": "account_test1"},
                    {"accountId": "account_test2"},
                ],
                "transactions": [{"transactionId": "transaction_test"}],
                "manifests": [{"manifestId": "manifest_test"}],
                "rewraps": [{"rewrapSecretMaterialsId": "rewrap_test"}],
                "vaults": [{"vaultId": "vault_test"}],
            },
            status_code=200,
        )

        response = client.get(
            "api/backend/v1alpha1/documents",
            headers={
                "X-SSL-CERT": component_cert,
                "X-SSL-CLIENT-VERIFY": "SUCCESS",
            },
        )

    assert response.status_code == 200
    assert response.json == {
        "documents": [
            {
                "id": "transaction_test",
                "content": (
                    '{"accounts": [], "transactions": [{"transactionId":'
                    ' "transaction_test"}], "manifests": [], "rewraps": [], "vaults": []}'
                ),
                "metadata": "",
            },
            {
                "id": "account_test1",
                "content": (
                    '{"accounts": [{"accountId": "account_test1"}], "transactions": [],'
                    ' "manifests": [], "rewraps": [], "vaults": []}'
                ),
                "metadata": "",
            },
            {
                "id": "account_test2",
                "content": (
                    '{"accounts": [{"accountId": "account_test2"}], "transactions": [],'
                    ' "manifests": [], "rewraps": [], "vaults": []}'
                ),
                "metadata": "",
            },
            {
                "id": "manifest_test",
                "content": (
                    '{"accounts": [], "transactions": [], "manifests": [{"manifestId":'
                    ' "manifest_test"}], "rewraps": [], "vaults": []}'
                ),
                "metadata": "",
            },
            {
                "id": "rewrap_test",
                "content": (
                    '{"accounts": [], "transactions": [], "manifests": [], "rewraps":'
                    ' [{"rewrapSecretMaterialsId": "rewrap_test"}], "vaults": []}'
                ),
                "metadata": "",
            },
        ],
        "count": 5,
    }


@pytest.mark.parametrize("seed", ["passphrase"], indirect=True)
def test_encrypted_download(seed, client):
    mock_url = "https://backend/v1/feed/download?clean=true"

    with requests_mock.mock() as m:
        m.get(
            mock_url,
            json={
                "accounts": [
                    {"accountId": "account_test1", "signedPayload": "account_test1_signed"},
                    {"accountId": "account_test2", "signedPayload": "account_test2_signed"},
                ],
                "transactions": [
                    {"transactionId": "transaction_test", "signedPayload": "transaction_test_signed"}
                ],
                "manifests": [
                    {"manifestId": "manifest_test", "signedPayload": "manifest_test_signed"}
                ],
                "rewraps": [
                    {"rewrapSecretMaterialsId": "rewrap_test", "signedPayload": "rewrap_test_signed"}
                ],
                "vaults": [{"vaultId": "vault_test"}],
            },
            status_code=200,
        )

        response = client.get(
            "api/backend/v1alpha1/documents",
            headers={
                "X-SSL-CERT": component_cert,
                "X-SSL-CLIENT-VERIFY": "SUCCESS",
            },
        )

    assert response.status_code == 200
    assert response.json["count"] == 5

    # bulk_download encrypts only signedPayload fields inside the JSON;
    # the outer content is still valid JSON — only the ciphered field needs decrypting.
    doc0 = json.loads(response.json["documents"][0]["content"])
    assert response.json["documents"][0]["id"] == "transaction_test"
    assert crypt.decrypt(doc0["transactions"][0]["signedPayloadCiphered"], seed) == "transaction_test_signed"
    assert response.json["documents"][0]["metadata"] == ""

    doc1 = json.loads(response.json["documents"][1]["content"])
    assert response.json["documents"][1]["id"] == "account_test1"
    assert crypt.decrypt(doc1["accounts"][0]["signedPayloadCiphered"], seed) == "account_test1_signed"
    assert response.json["documents"][1]["metadata"] == ""

    doc2 = json.loads(response.json["documents"][2]["content"])
    assert response.json["documents"][2]["id"] == "account_test2"
    assert crypt.decrypt(doc2["accounts"][0]["signedPayloadCiphered"], seed) == "account_test2_signed"
    assert response.json["documents"][2]["metadata"] == ""

    doc3 = json.loads(response.json["documents"][3]["content"])
    assert response.json["documents"][3]["id"] == "manifest_test"
    assert crypt.decrypt(doc3["manifests"][0]["signedPayloadCiphered"], seed) == "manifest_test_signed"
    assert response.json["documents"][3]["metadata"] == ""

    doc4 = json.loads(response.json["documents"][4]["content"])
    assert response.json["documents"][4]["id"] == "rewrap_test"
    assert crypt.decrypt(doc4["rewraps"][0]["signedPayloadCiphered"], seed) == "rewrap_test_signed"
    assert response.json["documents"][4]["metadata"] == ""


def test_empty_download(client):
    mock_url = "https://backend/v1/feed/download?clean=true"

    with requests_mock.mock() as m:
        m.get(
            mock_url,
            json={},
            status_code=200,
        )

        response = client.get(
            "api/backend/v1alpha1/documents",
            headers={
                "X-SSL-CERT": component_cert,
                "X-SSL-CLIENT-VERIFY": "SUCCESS",
            },
        )

    assert response.status_code == 200
    assert response.json == {"documents": [], "count": 0}


def test_docs_upload(client):
    payload = {
        "documents": [
            {
                "id": "test_id",
                "content": json.dumps({
                "vaultId": "test_vault_id",
                "accounts": [
                    {"accountId": "account_test1", "signedPayload": "account_test1_signed"},
                    {"accountId": "account_test2", "signedPayload": "account_test2_signed"},
                ],
                "transactions": [
                    {"transactionId": "transaction_test", "signedPayload": "transaction_test_signed"},
                ],
                "manifests": [
                    {"manifestId": "manifest_test", "signedPayload": "manifest_test_signed"},
                ],
                "rewraps": [
                    {"rewrapSecretMaterialsId": "rewrap_test", "signedPayload": "rewrap_test_signed"},
                ],
                "vaults": [
                    {"vaultId": "vault_test", "signedPayload": "vault_test_signed"},
                ],
            }),
                "signature": "",
                "metadata": None,
            }
        ]
    }

    mock_url = "https://backend/v1/feed/upload"

    with requests_mock.mock() as m:
        m.post(
            mock_url,
            json={},
            status_code=200,
        )

        response = client.post(
            "api/backend/v1alpha1/documents",
            headers={
                "X-SSL-CERT": component_cert,
                "X-SSL-CLIENT-VERIFY": "SUCCESS",
            },
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 204

        latest_request = m.last_request

        parts = decoder.MultipartDecoder(
            latest_request.body, latest_request.headers["Content-Type"], "utf-8"
        ).parts

        assert json.loads(parts[0].text) == {
            "accounts": [
                {"accountId": "account_test1", "signedPayload": "account_test1_signed"},
                {"accountId": "account_test2", "signedPayload": "account_test2_signed"},
            ],
            "manifests": [
                {"manifestId": "manifest_test", "signedPayload": "manifest_test_signed"}
            ],
            "transactions": [
                {
                    "transactionId": "transaction_test",
                    "signedPayload": "transaction_test_signed",
                }
            ],
            "rewraps": [
                {"rewrapSecretMaterialsId": "rewrap_test", "signedPayload": "rewrap_test_signed"}
            ],
            "vaultId": "test_vault_id",
        }


def test_empty_upload(client):
    payload = {"documents": []}

    mock_url = "https://backend/v1/feed/upload"

    with requests_mock.mock() as m:
        m.post(
            mock_url,
            status_code=200,
        )

        response = client.post(
            "api/backend/v1alpha1/documents",
            headers={
                "X-SSL-CERT": component_cert,
                "X-SSL-CLIENT-VERIFY": "SUCCESS",
            },
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 204
        assert not m.called


@pytest.mark.parametrize("seed", ["passphrase"], indirect=True)
def test_encrypted_upload(seed, client):
    # Content mirrors what bulk_download produces when SEED is set:
    # the outer JSON structure is plain, only signedPayload fields are ciphered.
    payload = {
        "documents": [
            {
                "id": "test_id",
                "signature": "",
                "metadata": None,
                "content": json.dumps({
                    "vaultId": "test_vault_id",
                    "accounts": [
                        {
                            "accountId": "account_test1",
                            "signedPayloadCiphered": crypt.encrypt("account_test1_signed", seed),
                        },
                        {
                            "accountId": "account_test2",
                            "signedPayloadCiphered": crypt.encrypt("account_test2_signed", seed),
                        },
                    ],
                    "transactions": [
                        {
                            "transactionId": "transaction_test",
                            "signedPayloadCiphered": crypt.encrypt("transaction_test_signed", seed),
                        },
                    ],
                    "manifests": [
                        {
                            "manifestId": "manifest_test",
                            "signedPayloadCiphered": crypt.encrypt("manifest_test_signed", seed),
                        },
                    ],
                    "rewraps": [
                        {
                            "rewrapSecretMaterialsId": "rewrap_test",
                            "signedPayloadCiphered": crypt.encrypt("rewrap_test_signed", seed),
                        },
                    ],
                    "vaults": [],
                }),
            }
        ]
    }

    mock_url = "https://backend/v1/feed/upload"

    with requests_mock.mock() as m:
        m.post(
            mock_url,
            json={},
            status_code=200,
        )

        response = client.post(
            "api/backend/v1alpha1/documents",
            headers={
                "X-SSL-CERT": component_cert,
                "X-SSL-CLIENT-VERIFY": "SUCCESS",
            },
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 204

        latest_request = m.last_request

        parts = decoder.MultipartDecoder(
            latest_request.body, latest_request.headers["Content-Type"], "utf-8"
        ).parts

        assert json.loads(parts[0].text) == {
            "accounts": [
                {"accountId": "account_test1", "signedPayload": "account_test1_signed"},
                {"accountId": "account_test2", "signedPayload": "account_test2_signed"},
            ],
            "manifests": [
                {"manifestId": "manifest_test", "signedPayload": "manifest_test_signed"}
            ],
            "transactions": [
                {
                    "transactionId": "transaction_test",
                    "signedPayload": "transaction_test_signed",
                }
            ],
            "rewraps": [
                {"rewrapSecretMaterialsId": "rewrap_test", "signedPayload": "rewrap_test_signed"}
            ],
            "vaultId": "test_vault_id",
        }
