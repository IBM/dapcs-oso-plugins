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

import json
from typing import TypeVar
import uuid
import pydantic
import pytest
import requests_mock

from fb.plugin import FBPlugin, get_signing_api_endpoint
from fb.types import MessagesRequest, MessagesStatusRequest, MessagesStatusResponse

from oso.framework.data.types import V1_3, V1_5
from oso.framework.plugin import current_oso_plugin_app
from oso.framework.plugin.addons.signing_server._key import KeyType


T = TypeVar("T", bound=pydantic.BaseModel)


def load_model(file_path: str, model: type[T]) -> T:
    with open(file_path, "r") as file:
        json_data = json.load(file)

    model_instance = model.model_validate(json_data)
    return model_instance


unsigned_doc = load_model("tests/data/unsigned_doc.json", V1_5.Document)

signed_doc = load_model("tests/data/signed_doc.json", V1_5.Document)

messages_request = load_model("tests/data/messages_request.json", MessagesRequest)


@pytest.mark.parametrize("mode", ["frontend"])
def test_frontend_isv2oso(mode, client):
    response = client.post(
        "/internal/messagesToSign",
        data=messages_request.model_dump_json(),
        content_type="application/json",
        headers={
            "X-TEST-SSL-VERIFY": "True",
            "X-TEST-SSL-FINGERPRINT": "VALID",
        },
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "statuses": [
            {
                "requestId": "a4963c1f-f2be-4e3c-9a3a-0d2627aaf9bc",
                "response": {},
                "status": "PENDING_SIGN",
                "type": "KEY_LINK_PROOF_OF_OWNERSHIP_RESPONSE",
            }
        ]
    }

    messages_status_request = MessagesStatusRequest(
        requestsIds=[uuid.UUID("a4963c1f-f2be-4e3c-9a3a-0d2627aaf9bc")]
    )

    response = client.post(
        "/internal/messagesStatus",
        data=messages_status_request.model_dump_json(),
        content_type="application/json",
        headers={
            "X-TEST-SSL-VERIFY": "True",
            "X-TEST-SSL-FINGERPRINT": "VALID",
        },
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "statuses": [
            {
                "type": "KEY_LINK_PROOF_OF_OWNERSHIP_RESPONSE",
                "status": "PENDING_SIGN",
                "requestId": "a4963c1f-f2be-4e3c-9a3a-0d2627aaf9bc",
                "response": {},
            }
        ]
    }

    response = client.get(
        f"/api/{mode}/v1alpha1/documents",
        headers={
            "X-TEST-SSL-VERIFY": "True",
            "X-TEST-SSL-FINGERPRINT": "VALID",
        },
    )

    assert response.status_code == 200
    assert V1_5.DocumentList.model_validate_json(response.data) == V1_5.DocumentList(
        documents=[unsigned_doc], count=1
    )


@pytest.mark.parametrize("mode", ["frontend"])
def test_frontend_oso2isv(mode, client):
    response = client.post(
        f"/api/{mode}/v1alpha1/documents",
        data=V1_5.DocumentList(documents=[signed_doc], count=1).model_dump_json(),
        content_type="application/json",
        headers={
            "X-TEST-SSL-VERIFY": "True",
            "X-TEST-SSL-FINGERPRINT": "VALID",
        },
    )

    assert response.status_code == 200
    assert response.data == b'["OK"]\n'

    response = client.post(
        "/internal/messagesStatus",
        data=MessagesStatusRequest(
            requestsIds=[uuid.UUID("a4963c1f-f2be-4e3c-9a3a-0d2627aaf9bc")]
        ).model_dump_json(),
        content_type="application/json",
        headers={
            "X-TEST-SSL-VERIFY": "True",
            "X-TEST-SSL-FINGERPRINT": "VALID",
        },
    )

    expected_messages_status_response = load_model(
        "tests/data/signed_messages_status_response.json", MessagesStatusResponse
    )

    assert response.status_code == 200
    assert (
        MessagesStatusResponse.model_validate_json(response.data)
        == expected_messages_status_response
    )


@pytest.mark.parametrize("mode", ["backend"])
def test_min_keys(mode, client):
    fb_plugin = current_oso_plugin_app()
    assert isinstance(fb_plugin, FBPlugin)

    secp256k1_keys = fb_plugin.signing_server.list_keys(key_type=KeyType.SECP256K1)
    assert len(secp256k1_keys) == 2

    ed25519_keys = fb_plugin.signing_server.list_keys(key_type=KeyType.ED25519)
    assert len(ed25519_keys) == 2


# @pytest.mark.parametrize("mode", ["backend"])
# def test_backend(
#     mode,
#     client,
# ):
#     fb_plugin = current_oso_plugin_app()
#     assert isinstance(fb_plugin, FBPlugin)

#     # keys = fb_plugin.signing_server.list_keys(key_type=KeyType.SECP256K1)

#     response = client.post(
#         f"/api/{mode}/v1alpha1/documents",
#         data=V1_3.DocumentList(documents=[unsigned_doc], count=1).model_dump_json(),
#         content_type="application/json",
#         headers={
#             "X-TEST-SSL-VERIFY": "True",
#             "X-TEST-SSL-FINGERPRINT": "VALID",
#         },
#     )

#     assert response.status_code == 200
#     assert response.data == b'["OK"]\n'

#     response = client.get(
#         f"/api/{mode}/v1alpha1/documents",
#         headers={
#             "X-TEST-SSL-VERIFY": "True",
#             "X-TEST-SSL-FINGERPRINT": "VALID",
#         },
#     )

#     assert response.status_code == 200
#     assert V1_3.DocumentList.model_validate_json(response.data) == V1_3.DocumentList(
#         documents=[signed_doc], count=1
#     )


@pytest.mark.parametrize("mode", ["frontend"])
def test_frontend_status(mode, client):
    response = client.get(
        f"/api/{mode}/v1alpha1/status",
        headers={
            "X-TEST-SSL-VERIFY": "True",
            "X-TEST-SSL-FINGERPRINT": "VALID",
        },
    )

    assert response.status_code == 200
    assert V1_3.ComponentStatus.model_validate_json(
        response.data
    ) == V1_3.ComponentStatus(status_code=200, status="OK")


@pytest.mark.parametrize("mode", ["backend"])
def test_backend_status(mode, client):
    with requests_mock.Mocker() as mock:
        mock.get(f"{get_signing_api_endpoint()}/status", text="OK")

        response = client.get(
            f"/api/{mode}/v1alpha1/status",
            headers={
                "X-TEST-SSL-VERIFY": "True",
                "X-TEST-SSL-FINGERPRINT": "VALID",
            },
        )

    assert response.status_code == 200
    assert V1_3.ComponentStatus.model_validate_json(
        response.data
    ) == V1_3.ComponentStatus(status_code=200, status="OK")


# ---------------------------------------------------------------------------
# Rewrap tests (V1_5 schema, framework-driven rewrap)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mode", ["backend"])
def test_rewrap_via_http_backend(mode, client):
    """POST /api/backend/v1alpha1/rewrap — framework drives rewrap, returns done."""
    # Trigger the signing_server cached_property so min_keys are generated.
    fb_plugin = current_oso_plugin_app()
    assert isinstance(fb_plugin, FBPlugin)
    _ = fb_plugin.signing_server  # triggers key generation (min_keys=2 each type)

    rotation_id = str(uuid.uuid4())

    response = client.post(
        f"/api/{mode}/v1alpha1/rewrap",
        data=json.dumps({"rotation_id": rotation_id}),
        content_type="application/json",
        headers={
            "X-TEST-SSL-VERIFY": "True",
            "X-TEST-SSL-FINGERPRINT": "VALID",
        },
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["doc_type"] == "mk_rotation_done"
    assert body["rotation_id"] == rotation_id
    # min_keys=2 per conftest → 2 SECP256K1 + 2 ED25519 keys generated
    assert len(body["rewrapped_key_ids"]) == 4


@pytest.mark.parametrize("mode", ["frontend"])
def test_rewrap_via_http_frontend_schedules(mode, client):
    """POST /api/frontend/v1alpha1/rewrap schedules mk_rotation (202 Accepted)."""
    rotation_id = str(uuid.uuid4())

    response = client.post(
        f"/api/{mode}/v1alpha1/rewrap",
        data=json.dumps({"rotation_id": rotation_id}),
        content_type="application/json",
        headers={
            "X-TEST-SSL-VERIFY": "True",
            "X-TEST-SSL-FINGERPRINT": "VALID",
        },
    )

    assert response.status_code == 202
    body = response.get_json()
    assert body["rotation_id"] == rotation_id
    assert body["status"] == "scheduled"

    # The next GET /documents must include the mk_rotation document.
    response = client.get(
        f"/api/{mode}/v1alpha1/documents",
        headers={
            "X-TEST-SSL-VERIFY": "True",
            "X-TEST-SSL-FINGERPRINT": "VALID",
        },
    )
    assert response.status_code == 200
    result = V1_5.DocumentList.model_validate_json(response.data)
    mk_docs = [d for d in result.documents if d.is_mk_rotation()]
    assert len(mk_docs) == 1
    meta = mk_docs[0].parse_mk_rotation_metadata()
    assert meta.rotation_id == rotation_id


@pytest.mark.parametrize("mode", ["backend"])
def test_rewrap_via_metadata_sentinel(mode, client):
    """Framework detects mk_rotation in metadata → rewrap → done doc on GET /docs."""
    # Trigger signing_server so min_keys are generated before rewrap.
    fb_plugin = current_oso_plugin_app()
    assert isinstance(fb_plugin, FBPlugin)
    _ = fb_plugin.signing_server

    rotation_id = str(uuid.uuid4())

    # Build a V1_5 DocumentList carrying the mk_rotation metadata sentinel.
    mk_rotation_doc = V1_5.Document.with_metadata(
        id=f"mk_rotation_{rotation_id}",
        content="",
        metadata=V1_5.MkRotationMetadata(rotation_id=rotation_id),
    )
    doc_list = V1_5.DocumentList(documents=[mk_rotation_doc], count=1)

    # POST to the backend documents endpoint — framework strips and rewraps.
    response = client.post(
        f"/api/{mode}/v1alpha1/documents",
        data=doc_list.model_dump_json(),
        content_type="application/json",
        headers={
            "X-TEST-SSL-VERIFY": "True",
            "X-TEST-SSL-FINGERPRINT": "VALID",
        },
    )
    assert response.status_code == 200

    # GET documents — the done doc must appear (injected by framework).
    response = client.get(
        f"/api/{mode}/v1alpha1/documents",
        headers={
            "X-TEST-SSL-VERIFY": "True",
            "X-TEST-SSL-FINGERPRINT": "VALID",
        },
    )
    assert response.status_code == 200

    result = V1_5.DocumentList.model_validate_json(response.data)
    done_docs = [d for d in result.documents if d.is_mk_rotation_done()]
    assert len(done_docs) == 1

    done = done_docs[0].parse_mk_rotation_done_metadata()
    assert done.rotation_id == rotation_id
    # min_keys=2 per conftest → 2+2 keys rewrapped
    assert len(done.rewrapped_key_ids) == 4
