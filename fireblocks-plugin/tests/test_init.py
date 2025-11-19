#
# (c) Copyright IBM Corp. 2025
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
import pytest

from uuid import uuid4
from flask.testing import FlaskClient

from oso.framework.plugin import PluginProtocol, create_app, current_oso_plugin_app

from fb.types import MessagesRequest, MessagesStatusRequest


@pytest.mark.parametrize("mode", ["frontend", "backend"])
def test_plugin_modes(
    monkeypatch,
    mode,
    _setup_app,
    _enable_mtls,
):
    monkeypatch.setenv("PLUGIN__MODE", mode)
    monkeypatch.setenv(
        "PLUGIN__APPLICATION",
        "fb.plugin:FBPlugin",
    )

    _enable_mtls()
    _setup_app()

    app = create_app()
    assert app is not None
    with app.app_context():
        assert isinstance(current_oso_plugin_app(), PluginProtocol)


@pytest.mark.parametrize("mode", ["frontend"])
def test_frontend_messages_to_sign_empty(mode, client: FlaskClient):
    response = client.post(
        "/internal/messagesToSign",
        data=MessagesRequest(messages=[]).model_dump_json(
            by_alias=True, exclude_none=True
        ),
        content_type="application/json",
        headers={
            "X-TEST-SSL-VERIFY": "True",
            "X-TEST-SSL-FINGERPRINT": "VALID",
        },
    )
    assert response.status_code == 200
    assert response.data == b'{"statuses":[]}\n'


@pytest.mark.parametrize("mode", ["frontend"])
def test_frontend_messages_status_empty(mode, client):
    response = client.post(
        "/internal/messagesStatus",
        data=MessagesStatusRequest(requestsIds=[]).model_dump_json(
            by_alias=True, exclude_none=True
        ),
        content_type="application/json",
        headers={
            "X-TEST-SSL-VERIFY": "True",
            "X-TEST-SSL-FINGERPRINT": "VALID",
        },
    )
    assert response.status_code == 200
    assert response.data == b'{"statuses":[]}\n'


@pytest.mark.parametrize("mode", ["backend"])
def test_backend_messages_to_sign_empty(mode, client):
    response = client.post(
        "/internal/messagesToSign",
        data=MessagesRequest(messages=[]).model_dump_json(
            by_alias=True, exclude_none=True
        ),
        content_type="application/json",
        headers={
            "X-TEST-SSL-VERIFY": "True",
            "X-TEST-SSL-FINGERPRINT": "VALID",
        },
    )
    assert response.status_code == 404


@pytest.mark.parametrize("mode", ["backend"])
def test_backend_messages_status_empty(mode, client):
    response = client.post(
        "/internal/messagesStatus",
        data=MessagesStatusRequest(requestsIds=[]).model_dump_json(
            by_alias=True, exclude_none=True
        ),
        content_type="application/json",
        headers={
            "X-TEST-SSL-VERIFY": "True",
            "X-TEST-SSL-FINGERPRINT": "VALID",
        },
    )
    assert response.status_code == 404


@pytest.mark.parametrize("mode", ["frontend"])
def test_frontend_messages_status_non_exist(mode, client):
    response = client.post(
        "/internal/messagesStatus",
        data=MessagesStatusRequest(requestsIds=[uuid4()]).model_dump_json(
            by_alias=True, exclude_none=True
        ),
        content_type="application/json",
        headers={
            "X-TEST-SSL-VERIFY": "True",
            "X-TEST-SSL-FINGERPRINT": "VALID",
        },
    )
    assert response.status_code == 200
    assert response.data == b'{"statuses":[]}\n'
