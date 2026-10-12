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
import requests
import requests_mock
from common.certs import component_cert

from oso_ripple_plugins.common import errors
from oso_ripple_plugins.frontend_plugin.frontend_plugin_manager import (
    FrontendPluginManager,
)

TOKEN_URL = "https://hmz_auth_hostname/token"
SIGNED_URL = "https://hmz_api_hostname/v1/vaults/operations/signed"


def make_documents(count=1):
    return [
        {
            "id": f"tx-{n}",
            "content": json.dumps(
                {
                    "vaultId": "test_vault_id",
                    "accounts": [],
                    "transactions": [
                        {"transactionId": f"tx-{n}", "signedPayload": "p"}
                    ],
                    "manifests": [],
                }
            ),
            "metadata": "",
        }
        for n in range(count)
    ]


@pytest.fixture
def no_sleep(mocker):
    return mocker.patch(
        "oso_ripple_plugins.frontend_plugin.frontend_plugin_manager.time.sleep"
    )


def mock_token(m):
    m.post(TOKEN_URL, json={"access_token": "test_token"}, status_code=200)


def test_transient_failure_is_retried_then_succeeds(set_env, no_sleep):
    with requests_mock.mock() as m:
        mock_token(m)
        m.post(
            SIGNED_URL,
            [
                {"status_code": 500},
                {"status_code": 502},
                {"json": {}, "status_code": 200},
            ],
        )

        fpm = FrontendPluginManager()
        fpm.bulk_upload(make_documents())

        signed_calls = [r for r in m.request_history if r.url == SIGNED_URL]
        assert len(signed_calls) == 3


def test_broadcast_error_after_exhausted_retries(set_env, no_sleep):
    with requests_mock.mock() as m:
        mock_token(m)
        m.post(SIGNED_URL, status_code=503)

        fpm = FrontendPluginManager()
        with pytest.raises(errors.BroadcastError):
            fpm.bulk_upload(make_documents())

        signed_calls = [r for r in m.request_history if r.url == SIGNED_URL]
        assert len(signed_calls) == fpm.broadcast_retries


def test_401_refreshes_token_and_retries(set_env, no_sleep):
    with requests_mock.mock() as m:
        mock_token(m)
        m.post(
            SIGNED_URL,
            [{"status_code": 401}, {"json": {}, "status_code": 200}],
        )

        fpm = FrontendPluginManager()
        fpm.bulk_upload(make_documents())

        token_calls = [r for r in m.request_history if r.url == TOKEN_URL]
        assert len(token_calls) == 2


def test_client_error_is_not_retried(set_env, no_sleep):
    with requests_mock.mock() as m:
        mock_token(m)
        m.post(SIGNED_URL, status_code=400)

        fpm = FrontendPluginManager()
        with pytest.raises(errors.BroadcastError):
            fpm.bulk_upload(make_documents())

        signed_calls = [r for r in m.request_history if r.url == SIGNED_URL]
        assert len(signed_calls) == 1


def test_connection_error_is_retried(set_env, no_sleep):
    with requests_mock.mock() as m:
        mock_token(m)
        m.post(
            SIGNED_URL,
            [
                {"exc": requests.exceptions.ConnectTimeout},
                {"json": {}, "status_code": 200},
            ],
        )

        fpm = FrontendPluginManager()
        fpm.bulk_upload(make_documents())

        signed_calls = [r for r in m.request_history if r.url == SIGNED_URL]
        assert len(signed_calls) == 2


def test_upload_endpoint_returns_503_when_broadcast_fails(client, no_sleep):
    with requests_mock.mock() as m:
        mock_token(m)
        m.post(SIGNED_URL, status_code=503)

        response = client.post(
            "api/frontend/v1alpha1/documents",
            headers={
                "X-SSL-CERT": component_cert,
                "X-SSL-CLIENT-VERIFY": "SUCCESS",
            },
            data=json.dumps({"documents": make_documents(), "count": 1}),
            content_type="application/json",
        )

        assert response.status_code == 503


def test_upload_endpoint_returns_204_on_success(client, no_sleep):
    with requests_mock.mock() as m:
        mock_token(m)
        m.post(SIGNED_URL, json={}, status_code=200)

        response = client.post(
            "api/frontend/v1alpha1/documents",
            headers={
                "X-SSL-CERT": component_cert,
                "X-SSL-CLIENT-VERIFY": "SUCCESS",
            },
            data=json.dumps({"documents": make_documents(), "count": 1}),
            content_type="application/json",
        )

        assert response.status_code == 204


PREPARED_URL = "https://hmz_api_hostname/v1/vaults/vault_id/operations/prepared"


def test_server_expires_in_overrides_configured_lifetime(set_env):
    """TOKEN_EXP says 4h, but if the server grants a shorter expires_in the
    refresh logic must honor the server's lifetime."""
    with requests_mock.mock() as m:
        m.post(TOKEN_URL, json={"access_token": "t", "expires_in": 1})

        fpm = FrontendPluginManager()
        # a 1s lifetime is always inside the 10s refresh buffer, so every
        # get_token() refreshes: first call generates + refreshes (2 requests),
        # the second refreshes again (1 more)
        fpm.get_token()
        fpm.get_token()

        token_calls = [r for r in m.request_history if r.url == TOKEN_URL]
        assert len(token_calls) == 3


def test_no_expires_in_keeps_configured_lifetime(set_env):
    with requests_mock.mock() as m:
        mock_token(m)  # no expires_in -> fall back to TOKEN_EXP (4h)

        fpm = FrontendPluginManager()
        fpm.get_token()
        fpm.get_token()

        token_calls = [r for r in m.request_history if r.url == TOKEN_URL]
        assert len(token_calls) == 1


def test_download_refreshes_token_on_401(set_env):
    empty_vault = {
        "vaultId": "vault_id",
        "accounts": [],
        "transactions": [],
        "manifests": [],
    }
    with requests_mock.mock() as m:
        mock_token(m)
        m.get(
            PREPARED_URL,
            [
                {"status_code": 401},
                {"json": empty_vault, "status_code": 200},
            ],
        )

        fpm = FrontendPluginManager()
        documents = fpm.bulk_download()

        assert documents == []
        token_calls = [r for r in m.request_history if r.url == TOKEN_URL]
        prepared_calls = [r for r in m.request_history if r.url == PREPARED_URL]
        assert len(token_calls) == 2
        assert len(prepared_calls) == 2
