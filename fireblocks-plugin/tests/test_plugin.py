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

from oso.framework.data.types import V1_3
from oso.framework.plugin import current_oso_plugin_app
from oso.framework.plugin.document.mk_rotation import MkRotationMetadata
from oso.framework.plugin.addons.signing_server._key import KeyType


T = TypeVar("T", bound=pydantic.BaseModel)


def load_model(file_path: str, model: type[T]) -> T:
    with open(file_path, "r") as file:
        json_data = json.load(file)

    model_instance = model.model_validate(json_data)
    return model_instance


unsigned_doc = load_model("tests/data/unsigned_doc.json", V1_3.Document)

signed_doc = load_model("tests/data/signed_doc.json", V1_3.Document)

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
    assert V1_3.DocumentList.model_validate_json(response.data) == V1_3.DocumentList(
        documents=[unsigned_doc], count=1
    )


@pytest.mark.parametrize("mode", ["frontend"])
def test_frontend_oso2isv(mode, client):
    response = client.post(
        f"/api/{mode}/v1alpha1/documents",
        data=V1_3.DocumentList(documents=[signed_doc], count=1).model_dump_json(),
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


@pytest.mark.parametrize("mode", ["backend"])
def test_rewrap(mode, client):
    fb_plugin = current_oso_plugin_app()
    all_keys = fb_plugin.signing_server.list_keys(
        KeyType.SECP256K1
    ) + fb_plugin.signing_server.list_keys(KeyType.ED25519)

    assert sorted(fb_plugin.rewrap(mk_rotation_request_id="rot-1")) == sorted(all_keys)


@pytest.mark.parametrize("mode", ["backend"])
def test_mk_rotation_document_flow(mode, client):
    """mk_rotation arriving via OSO drives FBPlugin.rewrap() and returns the result."""
    headers = {"X-TEST-SSL-VERIFY": "True", "X-TEST-SSL-FINGERPRINT": "VALID"}
    fb_plugin = current_oso_plugin_app()
    all_keys = fb_plugin.signing_server.list_keys(
        KeyType.SECP256K1
    ) + fb_plugin.signing_server.list_keys(KeyType.ED25519)

    rotation = V1_3.Document(
        id="rot-2",
        content="",
        metadata=MkRotationMetadata().model_dump(mode="json"),
    )
    response = client.post(
        f"/api/{mode}/v1alpha1/documents",
        data=V1_3.DocumentList(documents=[rotation], count=1).model_dump_json(),
        content_type="application/json",
        headers=headers,
    )
    assert response.status_code == 200
    assert fb_plugin.signed_statuses == []  # rotation doc never reached to_isv

    response = client.get(f"/api/{mode}/v1alpha1/documents", headers=headers)
    docs = V1_3.DocumentList.model_validate_json(response.data)
    assert docs.documents[0].id == "rot-2"
    done = MkRotationMetadata.model_validate_json(docs.documents[0].metadata)
    assert done.status == "success"
    assert sorted(done.rewrapped_key_ids) == sorted(all_keys)


@pytest.mark.parametrize("mode", ["backend"])
def test_rewrap_skips_key_top_up_and_clears_signing_error(mode, client):
    fb_plugin = current_oso_plugin_app()
    fb_plugin.signing_error = True

    # no min_keys generated mid-rotation
    assert fb_plugin.rewrap(mk_rotation_request_id="rot-3") == []
    assert fb_plugin.signing_error is None


@pytest.mark.parametrize("mode", ["backend"])
def test_rewrap_removes_backups_when_done(mode, client):
    fb_plugin = current_oso_plugin_app()
    ss = fb_plugin.signing_server
    keystore = FBPlugin._keystore_path()
    key_id = ss.list_keys(KeyType.SECP256K1)[0]
    key_file = keystore / "SECP256K1" / f"{key_id}.key"
    before = key_file.read_bytes()

    fb_plugin.rewrap(mk_rotation_request_id="r1")
    assert key_file.read_bytes() == before + b"\xff"
    assert not (keystore / ".mk_rotation").exists()  # backups removed when done

    with pytest.raises(ValueError, match="Invalid mk_rotation_request_id"):
        fb_plugin.rewrap(mk_rotation_request_id="../escape")


@pytest.mark.parametrize("mode", ["backend"])
def test_rewrap_retry_after_partial_failure(mode, client):
    from unittest.mock import patch

    fb_plugin = current_oso_plugin_app()
    ss = fb_plugin.signing_server
    ids = ss.list_keys(KeyType.SECP256K1) + ss.list_keys(KeyType.ED25519)
    files = [next(FBPlugin._keystore_path().glob(f"*/{i}.key")) for i in ids]
    before = [f.read_bytes() for f in files]

    real = ss.rewrap_key
    calls = iter([real, RuntimeError("hsm down")])

    def flaky(blob: bytes) -> bytes:
        step = next(calls, real)
        if isinstance(step, Exception):
            raise step
        return step(blob)

    with patch.object(ss, "rewrap_key", flaky):
        with pytest.raises(RuntimeError):
            fb_plugin.rewrap(mk_rotation_request_id="r")
    assert (FBPlugin._keystore_path() / ".mk_rotation" / "r").exists()

    fb_plugin.rewrap(mk_rotation_request_id="r")
    assert [f.read_bytes() for f in files] == [b + b"\xff" for b in before]
    assert not list(FBPlugin._keystore_path().rglob("*.tmp"))
    assert not (FBPlugin._keystore_path() / ".mk_rotation").exists()


@pytest.mark.parametrize("mode", ["backend"])
def test_sign_failure_marks_message_failed(mode, client):
    from unittest.mock import patch

    from fb.types import MessageEnvelope, MessageState

    fb_plugin = current_oso_plugin_app()
    envelope = MessageEnvelope.model_validate_json(unsigned_doc.content)
    with patch.object(
        type(fb_plugin.signing_server), "sign", side_effect=RuntimeError("old MK")
    ):
        status = fb_plugin.sign(envelope)

    assert status.status == MessageState.FAILED
    assert status.response.signedMessages == []
    assert fb_plugin.signing_error is True


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
# MK rotation tests (framework-driven rewrap)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("mode", ["frontend"])
def test_mk_rotation_generate_frontend(mode, client):
    """POST /generate on the frontend queues mk_rotation for the backend."""
    headers = {"X-TEST-SSL-VERIFY": "True", "X-TEST-SSL-FINGERPRINT": "VALID"}
    response = client.post(
        f"/api/{mode}/v1alpha1/generate",
        json={"doc_type": "mk_rotation"},
        headers=headers,
    )
    assert response.status_code == 200
    doc_id = response.get_json()["id"]

    response = client.get(f"/api/{mode}/v1alpha1/documents", headers=headers)
    docs = V1_3.DocumentList.model_validate_json(response.data)
    assert [d.id for d in docs.documents] == [doc_id]


@pytest.mark.parametrize("mode", ["frontend"])
def test_mk_rotation_end_to_end(mode, app, monkeypatch, _setup_app):
    """Admin -> frontend -> OSO -> backend rewrap -> OSO -> frontend done."""
    from oso.framework.plugin import create_app

    headers = {"X-TEST-SSL-VERIFY": "True", "X-TEST-SSL-FINGERPRINT": "VALID"}
    fe = app.test_client()
    monkeypatch.setenv("PLUGIN__MODE", "backend")
    _setup_app()  # reload config for the backend app
    be_app = create_app()
    be_app.config.update({"TESTING": True})
    be = be_app.test_client()

    def ferry(src, src_mode, dst, dst_mode):
        """What OSO does: GET from one side, POST to the other."""
        got = src.get(f"/api/{src_mode}/v1alpha1/documents", headers=headers)
        assert got.status_code == 200, got.data
        posted = dst.post(
            f"/api/{dst_mode}/v1alpha1/documents",
            data=got.data,
            content_type="application/json",
            headers=headers,
        )
        assert posted.status_code == 200, posted.data
        return V1_3.DocumentList.model_validate_json(got.data)

    gen = fe.post(
        "/api/frontend/v1alpha1/generate",
        json={"doc_type": "mk_rotation"},
        headers=headers,
    )
    assert gen.status_code == 200, gen.data
    rid = gen.json["id"]

    # Backend keys exist before the rotation (min_keys top-up).
    with be_app.app_context():
        all_keys = sum(
            (current_oso_plugin_app().signing_server.list_keys(t) for t in KeyType),
            [],
        )

    sent = ferry(fe, "frontend", be, "backend")
    assert [d.id for d in sent.documents] == [rid]

    back = ferry(be, "backend", fe, "frontend")
    assert [d.id for d in back.documents] == [rid]
    done = MkRotationMetadata.model_validate_json(back.documents[0].metadata)
    assert done.status == "success"
    assert sorted(done.rewrapped_key_ids) == sorted(all_keys)

    # Frontend saw the reply: rotation no longer re-sent, a new one is allowed.
    assert ferry(fe, "frontend", be, "backend").count == 0
    again = fe.post(
        "/api/frontend/v1alpha1/generate",
        json={"doc_type": "mk_rotation"},
        headers=headers,
    )
    assert again.status_code == 200, again.data
