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
    token_url = "https://hmz_auth_hostname/token"
    prepared_url = "https://hmz_api_hostname/v1/vaults/vault_id/operations/prepared"

    with requests_mock.mock() as m:
        m.post(
            token_url,
            json={
                "access_token": "test_token",
            },
            status_code=200,
        )

        m.get(
            prepared_url,
            json={
                "vaultId": "test_vault_id",
                "accounts": [
                    {"accountId": "test_account_id_1"},
                    {"accountId": "test_account_id_2"},
                ],
                "transactions": [
                    {
                        "transactionId": "test_transaction_id",
                        "signedPayload": "test_payload",
                    }
                ],
                "manifests": [{"manifestId": "test_manifest_id"}],
            },
        )

        response = client.get(
            "api/frontend/v1alpha1/documents",
            headers={
                "X-SSL-CERT": component_cert,
                "X-SSL-CLIENT-VERIFY": "SUCCESS",
            },
        )

    assert response.status_code == 200
    assert response.json == {
        "documents": [
            {
                "id": "test_transaction_id",
                "content": (
                    '{"vaultId": "test_vault_id", "accounts": [], "transactions":'
                    ' [{"transactionId": "test_transaction_id", "signedPayload":'
                    ' "test_payload"}], "manifests": []}'
                ),
                "metadata": "",
            },
            {
                "id": "test_account_id_1",
                "content": (
                    '{"vaultId": "test_vault_id", "accounts": [{"accountId":'
                    ' "test_account_id_1"}], "transactions": [], "manifests": []}'
                ),
                "metadata": "",
            },
            {
                "id": "test_account_id_2",
                "content": (
                    '{"vaultId": "test_vault_id", "accounts": [{"accountId":'
                    ' "test_account_id_2"}], "transactions": [], "manifests": []}'
                ),
                "metadata": "",
            },
            {
                "id": "test_manifest_id",
                "content": (
                    '{"vaultId": "test_vault_id", "accounts": [], "transactions": [],'
                    ' "manifests": [{"manifestId": "test_manifest_id"}]}'
                ),
                "metadata": "",
            },
        ],
        "count": 4,
    }


def test_empty_download(client):
    token_url = "https://hmz_auth_hostname/token"
    prepared_url = "https://hmz_api_hostname/v1/vaults/vault_id/operations/prepared"

    with requests_mock.mock() as m:
        m.post(
            token_url,
            json={
                "access_token": "test_token",
            },
            status_code=200,
        )

        m.get(
            prepared_url,
            json={
                "vaultId": "test_vault_id",
                "accounts": [],
                "transactions": [],
                "manifests": [],
            },
        )

        response = client.get(
            "api/frontend/v1alpha1/documents",
            headers={
                "X-SSL-CERT": component_cert,
                "X-SSL-CLIENT-VERIFY": "SUCCESS",
            },
        )

    assert response.status_code == 200
    assert response.json == {
        "documents": [],
        "count": 0,
    }


@pytest.mark.parametrize("seed", ["passphrase"], indirect=True)
def test_encrypted_download(seed, client):
    token_url = "https://hmz_auth_hostname/token"
    prepared_url = "https://hmz_api_hostname/v1/vaults/vault_id/operations/prepared"

    with requests_mock.mock() as m:
        m.post(
            token_url,
            json={
                "access_token": "test_token",
            },
            status_code=200,
        )

        m.get(
            prepared_url,
            json={
                "vaultId": "test_vault_id",
                "accounts": [
                    {"accountId": "test_account_id_1"},
                    {"accountId": "test_account_id_2"},
                ],
                "transactions": [
                    {
                        "transactionId": "test_transaction_id",
                        "signedPayload": "test_payload",
                    }
                ],
                "manifests": [{"manifestId": "test_manifest_id"}],
            },
        )

        response = client.get(
            "api/frontend/v1alpha1/documents",
            headers={
                "X-SSL-CERT": component_cert,
                "X-SSL-CLIENT-VERIFY": "SUCCESS",
            },
        )

    assert response.status_code == 200
    assert response.json["documents"][0]["id"] == "test_transaction_id"
    assert crypt.decrypt(response.json["documents"][0]["content"], seed) == (
        '{"vaultId": "test_vault_id", "accounts": [], "transactions":'
        ' [{"transactionId": "test_transaction_id", "signedPayload":'
        ' "test_payload"}], "manifests": []}'
    )
    assert response.json["documents"][0]["metadata"] == ""
    assert response.json["documents"][1]["id"] == "test_account_id_1"
    assert crypt.decrypt(response.json["documents"][1]["content"], seed) == (
        '{"vaultId": "test_vault_id", "accounts": [{"accountId":'
        ' "test_account_id_1"}], "transactions": [], "manifests": []}'
    )
    assert response.json["documents"][1]["metadata"] == ""
    assert response.json["documents"][2]["id"] == "test_account_id_2"
    assert crypt.decrypt(response.json["documents"][2]["content"], seed) == (
        '{"vaultId": "test_vault_id", "accounts": [{"accountId":'
        ' "test_account_id_2"}], "transactions": [], "manifests": []}'
    )
    assert response.json["documents"][2]["metadata"] == ""
    assert response.json["documents"][3]["id"] == "test_manifest_id"
    assert crypt.decrypt(response.json["documents"][3]["content"], seed) == (
        '{"vaultId": "test_vault_id", "accounts": [], "transactions": [],'
        ' "manifests": [{"manifestId": "test_manifest_id"}]}'
    )
    assert response.json["documents"][3]["metadata"] == ""
    assert response.json["count"] == 4


def test_docs_upload(client):
    payload = {
        "documents": [
            {
                "id": "test_account_id_2",
                "content": (
                    '{"vaultId": "test_vault_id", "accounts": [{"accountId":'
                    ' "test_account_id_2"}], "transactions": [], "manifests": []}'
                ),
                "metadata": "",
            },
            {
                "id": "test_account_id_1",
                "content": (
                    '{"vaultId": "test_vault_id", "accounts": [{"accountId":'
                    ' "test_account_id_1"}], "transactions": [], "manifests": []}'
                ),
                "metadata": "",
            },
            {
                "id": "test_manifest_id",
                "content": (
                    '{"vaultId": "test_vault_id", "accounts": [], "transactions": [],'
                    ' "manifests": [{"manifestId": "test_manifest_id"}]}'
                ),
                "metadata": "",
            },
            {
                "id": "test_transaction_id",
                "content": (
                    '{"vaultId": "test_vault_id", "accounts": [], "transactions":'
                    ' [{"transactionId": "test_transaction_id", "signedPayload":'
                    ' "test_payload"}], "manifests": []}'
                ),
                "metadata": "",
            },
        ],
        "count": 4,
    }

    token_url = "https://hmz_auth_hostname/token"
    signed_url = "https://hmz_api_hostname/v1/vaults/operations/signed"

    with requests_mock.mock() as m:
        m.post(
            token_url,
            json={
                "access_token": "test_token",
            },
            status_code=200,
        )

        m.post(
            signed_url,
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

        response = client.post(
            "api/frontend/v1alpha1/documents",
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
                {"accountId": "test_account_id_2"},
                {"accountId": "test_account_id_1"},
            ],
            "transactions": [
                {
                    "transactionId": "test_transaction_id",
                    "signedPayload": "test_payload",
                }
            ],
            "manifests": [{"manifestId": "test_manifest_id"}],
            "vaults": [],
        }


def test_empty_upload(client):
    payload = {
        "documents": [],
        "count": 0,
    }

    token_url = "https://hmz_auth_hostname/token"
    signed_url = "https://hmz_api_hostname/v1/vaults/operations/signed"

    with requests_mock.mock() as m:
        m.post(
            token_url,
            json={
                "access_token": "test_token",
            },
            status_code=200,
        )

        m.post(
            signed_url,
            status_code=200,
        )

        response = client.post(
            "api/frontend/v1alpha1/documents",
            headers={
                "X-SSL-CERT": component_cert,
                "X-SSL-CLIENT-VERIFY": "SUCCESS",
            },
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 204

        # latest_request = m.last_request
        assert not m.called


@pytest.mark.parametrize("seed", ["passphrase"], indirect=True)
def test_encrypted_upload(seed, client):
    payload = {
        "documents": [
            {
                "id": "test_account_id_2",
                "metadata": "",
            },
            {
                "id": "test_account_id_1",
                "metadata": "",
            },
            {
                "id": "test_manifest_id",
                "metadata": "",
            },
            {
                "id": "test_transaction_id",
                "metadata": "",
            },
        ],
        "count": 4,
    }

    payload["documents"][0]["content"] = crypt.encrypt(
        (
            '{"vaultId": "test_vault_id", "accounts": [{"accountId":'
            ' "test_account_id_2"}], "transactions": [], "manifests": []}'
        ),
        seed,
    )
    payload["documents"][1]["content"] = crypt.encrypt(
        (
            '{"vaultId": "test_vault_id", "accounts": [{"accountId":'
            ' "test_account_id_1"}], "transactions": [], "manifests": []}'
        ),
        seed,
    )
    payload["documents"][2]["content"] = crypt.encrypt(
        (
            '{"vaultId": "test_vault_id", "accounts": [], "transactions": [],'
            ' "manifests": [{"manifestId": "test_manifest_id"}]}'
        ),
        seed,
    )
    payload["documents"][3]["content"] = crypt.encrypt(
        (
            '{"vaultId": "test_vault_id", "accounts": [], "transactions":'
            ' [{"transactionId": "test_transaction_id", "signedPayload":'
            ' "test_payload"}], "manifests": []}'
        ),
        seed,
    )

    token_url = "https://hmz_auth_hostname/token"
    signed_url = "https://hmz_api_hostname/v1/vaults/operations/signed"

    with requests_mock.mock() as m:
        m.post(
            token_url,
            json={
                "access_token": "test_token",
            },
            status_code=200,
        )

        m.post(
            signed_url,
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

        response = client.post(
            "api/frontend/v1alpha1/documents",
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
                {"accountId": "test_account_id_2"},
                {"accountId": "test_account_id_1"},
            ],
            "transactions": [
                {
                    "transactionId": "test_transaction_id",
                    "signedPayload": "test_payload",
                }
            ],
            "manifests": [{"manifestId": "test_manifest_id"}],
            "vaults": [],
        }


def test_docs_upload_multiple_batches(client):
    """25 documents should be split into two upload requests: 20 + 5."""
    documents = [
        {
            "id": f"test_account_id_{i}",
            "content": json.dumps(
                {
                    "vaultId": "test_vault_id",
                    "accounts": [{"accountId": f"test_account_id_{i}"}],
                    "transactions": [],
                    "manifests": [],
                }
            ),
            "metadata": "",
        }
        for i in range(25)
    ]
    payload = {"documents": documents, "count": 25}

    token_url = "https://hmz_auth_hostname/token"
    signed_url = "https://hmz_api_hostname/v1/vaults/operations/signed"

    with requests_mock.mock() as m:
        m.post(token_url, json={"access_token": "test_token"}, status_code=200)
        m.post(
            signed_url,
            json={"accounts": [], "transactions": [], "manifests": [], "vaults": []},
            status_code=200,
        )

        response = client.post(
            "api/frontend/v1alpha1/documents",
            headers={
                "X-SSL-CERT": component_cert,
                "X-SSL-CLIENT-VERIFY": "SUCCESS",
            },
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 204

        # Two batches (20 + 5) => two calls to the signed upload endpoint
        signed_calls = [
            req for req in m.request_history if req.url == signed_url
        ]
        assert len(signed_calls) == 2

        first_batch = decoder.MultipartDecoder(
            signed_calls[0].body, signed_calls[0].headers["Content-Type"], "utf-8"
        ).parts
        second_batch = decoder.MultipartDecoder(
            signed_calls[1].body, signed_calls[1].headers["Content-Type"], "utf-8"
        ).parts

        first_accounts = json.loads(first_batch[0].text)["accounts"]
        second_accounts = json.loads(second_batch[0].text)["accounts"]

        assert len(first_accounts) == 20
        assert len(second_accounts) == 5
        # No overlap / no drops across the batch boundary
        all_ids = {a["accountId"] for a in first_accounts} | {
            a["accountId"] for a in second_accounts
        }
        assert all_ids == {f"test_account_id_{i}" for i in range(25)}


def test_docs_upload_continues_after_batch_failure(client):
    """If one batch's upload fails, later batches should still be sent
    (i.e. the whole run should not abort on a single batch failure)."""
    documents = [
        {
            "id": f"test_account_id_{i}",
            "content": json.dumps(
                {
                    "vaultId": "test_vault_id",
                    "accounts": [{"accountId": f"test_account_id_{i}"}],
                    "transactions": [],
                    "manifests": [],
                }
            ),
            "metadata": "",
        }
        for i in range(25)  # 2 batches: 20 + 5
    ]
    payload = {"documents": documents, "count": 25}

    token_url = "https://hmz_auth_hostname/token"
    signed_url = "https://hmz_api_hostname/v1/vaults/operations/signed"

    with requests_mock.mock() as m:
        m.post(token_url, json={"access_token": "test_token"}, status_code=200)
        # First batch fails (500), second batch succeeds
        m.post(
            signed_url,
            [
                {"status_code": 500},
                {
                    "json": {
                        "accounts": [],
                        "transactions": [],
                        "manifests": [],
                        "vaults": [],
                    },
                    "status_code": 200,
                },
            ],
        )

        response = client.post(
            "api/frontend/v1alpha1/documents",
            headers={
                "X-SSL-CERT": component_cert,
                "X-SSL-CLIENT-VERIFY": "SUCCESS",
            },
            data=json.dumps(payload),
            content_type="application/json",
        )

        # The run should complete (not raise/abort) despite the first
        # batch failing — both batches should have been attempted.
        assert response.status_code == 204

        signed_calls = [
            req for req in m.request_history if req.url == signed_url
        ]
        assert len(signed_calls) == 2


@pytest.mark.parametrize("batch_upload_size", [5], indirect=True)
def test_docs_upload_respects_custom_batch_size(batch_upload_size, client):
    """With BATCH_UPLOAD_SIZE=5, 12 documents should split into 5 + 5 + 2."""
    documents = [
        {
            "id": f"test_account_id_{i}",
            "content": json.dumps(
                {
                    "vaultId": "test_vault_id",
                    "accounts": [{"accountId": f"test_account_id_{i}"}],
                    "transactions": [],
                    "manifests": [],
                }
            ),
            "metadata": "",
        }
        for i in range(12)
    ]
    payload = {"documents": documents, "count": 12}

    token_url = "https://hmz_auth_hostname/token"
    signed_url = "https://hmz_api_hostname/v1/vaults/operations/signed"

    with requests_mock.mock() as m:
        m.post(token_url, json={"access_token": "test_token"}, status_code=200)
        m.post(
            signed_url,
            json={"accounts": [], "transactions": [], "manifests": [], "vaults": []},
            status_code=200,
        )

        response = client.post(
            "api/frontend/v1alpha1/documents",
            headers={
                "X-SSL-CERT": component_cert,
                "X-SSL-CLIENT-VERIFY": "SUCCESS",
            },
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 204

        signed_calls = [req for req in m.request_history if req.url == signed_url]
        assert len(signed_calls) == 3  # 5 + 5 + 2

        batch_sizes = []
        for call in signed_calls:
            parts = decoder.MultipartDecoder(
                call.body, call.headers["Content-Type"], "utf-8"
            ).parts
            accounts = json.loads(parts[0].text)["accounts"]
            batch_sizes.append(len(accounts))

        assert batch_sizes == [5, 5, 2]
