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
    mock_url = "https://backend/v1/feed/download?clean=True"

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
                    ' "transaction_test"}], "manifests": [], "vaults": []}'
                ),
                "metadata": "",
            },
            {
                "id": "account_test1",
                "content": (
                    '{"accounts": [{"accountId": "account_test1"}], "transactions": [],'
                    ' "manifests": [], "vaults": []}'
                ),
                "metadata": "",
            },
            {
                "id": "account_test2",
                "content": (
                    '{"accounts": [{"accountId": "account_test2"}], "transactions": [],'
                    ' "manifests": [], "vaults": []}'
                ),
                "metadata": "",
            },
            {
                "id": "manifest_test",
                "content": (
                    '{"accounts": [], "transactions": [], "manifests": [{"manifestId":'
                    ' "manifest_test"}], "vaults": []}'
                ),
                "metadata": "",
            },
        ],
        "count": 4,
    }


@pytest.mark.parametrize("seed", ["passphrase"], indirect=True)
def test_encrypted_download(seed, client):
    mock_url = "https://backend/v1/feed/download?clean=True"

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

    assert response.json["documents"][0]["id"] == "transaction_test"
    assert crypt.decrypt(response.json["documents"][0]["content"], seed) == (
        '{"accounts": [], "transactions": [{"transactionId":'
        ' "transaction_test"}], "manifests": [], "vaults": []}'
    )
    assert response.json["documents"][0]["metadata"] == ""
    assert response.json["documents"][1]["id"] == "account_test1"
    assert crypt.decrypt(response.json["documents"][1]["content"], seed) == (
        '{"accounts": [{"accountId": "account_test1"}], "transactions": [],'
        ' "manifests": [], "vaults": []}'
    )
    assert response.json["documents"][1]["metadata"] == ""
    assert response.json["documents"][2]["id"] == "account_test2"
    assert crypt.decrypt(response.json["documents"][2]["content"], seed) == (
        '{"accounts": [{"accountId": "account_test2"}], "transactions": [],'
        ' "manifests": [], "vaults": []}'
    )
    assert response.json["documents"][2]["metadata"] == ""
    assert response.json["documents"][3]["id"] == "manifest_test"
    assert crypt.decrypt(response.json["documents"][3]["content"], seed) == (
        '{"accounts": [], "transactions": [], "manifests": [{"manifestId":'
        ' "manifest_test"}], "vaults": []}'
    )
    assert response.json["documents"][3]["metadata"] == ""
    assert response.json["count"] == 4
    assert response.status_code == 200


def test_empty_download(client):
    mock_url = "https://backend/v1/feed/download?clean=True"

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
                "content": """{
                    "vaultId": "test_vault_id",
                    "accounts": [
                        {"accountId": "account_test1", "signedPayload": "account_test1_signed"},
                        {"accountId": "account_test2", "signedPayload": "account_test2_signed"}
                    ],
                    "transactions": [
                        { "transactionId": "transaction_test", "signedPayload": "transaction_test_signed"}
                    ],
                    "manifests": [
                        {"manifestId": "manifest_test", "signedPayload": "manifest_test_signed"}
                    ],
                    "vaults": [
                        {"vaultId": "vault_test", "signedPayload": "vault_test_signed"}
                    ]
                }""",
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
    payload = {"documents": [{"id": "test_id", "signature": "", "metadata": None}]}

    payload["documents"][0]["content"] = crypt.encrypt(
        """
    {
        "vaultId": "test_vault_id",
        "accounts": [
            {"accountId": "account_test1", "signedPayload": "account_test1_signed"},
            {"accountId": "account_test2", "signedPayload": "account_test2_signed"}
        ],
        "transactions": [
            {"transactionId": "transaction_test", "signedPayload": "transaction_test_signed"}
        ],
        "manifests": [
            {"manifestId": "manifest_test", "signedPayload": "manifest_test_signed"}
        ],
        "vaults": [
            {"vaultId": "vault_test", "signedPayload": "vault_test_signed"}
        ]
    }""",
        seed,
    )

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
            "vaultId": "test_vault_id",
        }
