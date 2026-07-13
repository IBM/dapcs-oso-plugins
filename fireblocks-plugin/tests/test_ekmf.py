#
# (c) Copyright IBM Corp. 2026
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

import base64
import json
import uuid

import pytest
import requests_mock

from conftest import APPROVER_FINGERPRINT, EKMF_ADDON_PORT

from fb.ekmf import SigningKeyStore, parse_ekmf_document_type

from oso.framework.data.types import V1_3

EKMF_ADDON_URL = f"http://localhost:{EKMF_ADDON_PORT}"

HEADERS = {
    "X-TEST-SSL-VERIFY": "True",
    "X-TEST-SSL-FINGERPRINT": "VALID",
}

APPROVER_HEADERS = {
    "X-TEST-SSL-VERIFY": "True",
    "X-TEST-SSL-FINGERPRINT": APPROVER_FINGERPRINT,
}

_TRANSPORT_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<SimpleExchangeModels>
  <KeyList>
    <AesKey>
      <KeyData>
        <Format>CKM_RSA_PKCS_OAEP</Format>
        <KeyValue>deadbeef</KeyValue>
        <KeyCheck><KeyCheckValue>0000</KeyCheckValue></KeyCheck>
        <KeyLabel>test-kek</KeyLabel>
      </KeyData>
    </AesKey>
  </KeyList>
</SimpleExchangeModels>
"""

_PAYLOAD_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<SimpleExchangeModels>
  <KeyList>
    <EccKey>
      <KekData>
        <KekLabel>test-kek</KekLabel>
      </KekData>
      <KeyData>
        <Format>CKM_AES_CBC_PAD</Format>
        <KeyValue>deadbeef</KeyValue>
        <KeyCheck><KeyCheckValue>0000</KeyCheckValue></KeyCheck>
        <KeyLabel>test-ed25519-0</KeyLabel>
        <Curve>EDWARDS_CURVE_25519</Curve>
      </KeyData>
    </EccKey>
    <EccKey>
      <KekData>
        <KekLabel>test-kek</KekLabel>
      </KekData>
      <KeyData>
        <Format>CKM_AES_CBC_PAD</Format>
        <KeyValue>deadbeef</KeyValue>
        <KeyCheck><KeyCheckValue>0000</KeyCheckValue></KeyCheck>
        <KeyLabel>test-secp256k1-0</KeyLabel>
        <Curve>SECP256K1_CURVE</Curve>
      </KeyData>
    </EccKey>
  </KeyList>
</SimpleExchangeModels>
"""

# Fireblocks cannot sign with AES keys, so imports containing them are
# rejected up front.
_AES_PAYLOAD_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<SimpleExchangeModels>
  <KeyList>
    <AesKey>
      <KekData>
        <KekLabel>test-kek</KekLabel>
      </KekData>
      <KeyData>
        <Format>CKM_AES_CBC</Format>
        <KeyValue>deadbeef</KeyValue>
        <KeyCheck><KeyCheckValue>0000</KeyCheckValue></KeyCheck>
        <KeyLabel>test-aes-0</KeyLabel>
      </KeyData>
    </AesKey>
  </KeyList>
</SimpleExchangeModels>
"""

KEY_LABELS = ["test-ed25519-0", "test-secp256k1-0"]
KEY_IDS = [str(uuid.uuid4()), str(uuid.uuid4())]
KEY_LABEL_TO_ID = dict(zip(KEY_LABELS, KEY_IDS))


def _init_doc_wire():
    return {
        "id": str(uuid.uuid4()),
        "content": "",
        "metadata": json.dumps({"ekmf_addon": {"document_type": "init"}}),
    }


def _wrapping_key_doc_wire(key_id):
    content = {
        "key_id": key_id,
        "public_key": base64.b64encode(b"fake-public-key").decode(),
        "key_hash": "ab" * 32,
    }
    return {
        "id": str(uuid.uuid4()),
        "content": json.dumps(content),
        "metadata": json.dumps({"ekmf_addon": {"document_type": "wrapping_key"}}),
    }


def _keygen_result_wire(key_id):
    return {
        "result": _wrapping_key_doc_wire(key_id),
        "wrapping_key": {
            "key_id": key_id,
            "private_key": base64.b64encode(b"fake-ep11-private-blob").decode(),
        },
    }


def _payload_doc_wire(key_id, payload_xml=_PAYLOAD_XML):
    content = {
        "wrapping_key_id": key_id,
        "transport_key": base64.b64encode(_TRANSPORT_XML).decode(),
        "payload": base64.b64encode(payload_xml).decode(),
    }
    return {
        "id": str(uuid.uuid4()),
        "content": json.dumps(content),
        "metadata": json.dumps({"ekmf_addon": {"document_type": "ekmf_payload"}}),
    }


def _import_result_doc_wire(with_key_ids=False):
    """Build an import-result OSO document wire representation.

    Set ``with_key_ids=True`` to include the UUID that the backend injects
    before forwarding the document through OSO (simulating the enriched doc
    the frontend receives).  The raw addon /wrap response has no key_id.
    """
    content = {
        "keys": [
            {
                **({"key_id": KEY_LABEL_TO_ID[key_label]} if with_key_ids else {}),
                "key_label": key_label,
                "hash": "ab" * 32,
                "checksum": "cdcdcd",
            }
            for key_label in KEY_LABELS
        ]
    }
    return {
        "id": str(uuid.uuid4()),
        "content": json.dumps(content),
        "metadata": json.dumps({"ekmf_addon": {"document_type": "import_result"}}),
    }


def _import_result_wire():
    # The addon /wrap response does NOT include key_id; the backend assigns UUIDs.
    return {
        "result": _import_result_doc_wire(with_key_ids=False),
        "key_blobs": [
            {
                "key_label": key_label,
                "encrypted_key": base64.b64encode(
                    f"fake-ep11-{key_label}".encode()
                ).decode(),
            }
            for key_label in KEY_LABELS
        ],
    }


def _upload(client, mode, documents):
    return client.post(
        f"/api/{mode}/v1alpha1/documents",
        data=json.dumps({"documents": documents, "count": len(documents)}),
        content_type="application/json",
        headers=HEADERS,
    )


def _download(client, mode):
    response = client.get(
        f"/api/{mode}/v1alpha1/documents",
        headers=HEADERS,
    )

    assert response.status_code == 200

    return V1_3.DocumentList.model_validate_json(response.data)


@pytest.mark.parametrize("mode", ["backend"])
def test_backend_keygen_persists_bundle_and_enqueues_document(
    mode, client, keystore_path
):
    key_id = str(uuid.uuid4())

    with requests_mock.Mocker() as mock:
        keygen_mock = mock.post(
            f"{EKMF_ADDON_URL}/addon/ekmf/import/keygen",
            json=_keygen_result_wire(key_id),
        )

        response = _upload(client, mode, [_init_doc_wire()])

        assert response.status_code == 200
        assert keygen_mock.call_count == 1

    bundle = json.loads((keystore_path / "wrapping_key.json").read_text())
    assert bundle["key_id"] == key_id
    assert base64.b64decode(bundle["private_key"]) == b"fake-ep11-private-blob"

    # Only the WrappingKeyDocument (no private key) flows back through OSO
    document_list = _download(client, mode)

    assert document_list.count == 1
    doc = document_list.documents[0]
    assert "private_key" not in doc.content

    metadata = json.loads(doc.metadata)
    assert metadata["ekmf_addon"]["document_type"] == "wrapping_key"


@pytest.mark.parametrize("mode", ["backend"])
def test_backend_wrap_sends_bundle_and_persists_key_blobs(mode, client, keystore_path):
    key_id = str(uuid.uuid4())

    bundle = {
        "key_id": key_id,
        "private_key": base64.b64encode(b"fake-ep11-private-blob").decode(),
    }
    keystore_path.mkdir(parents=True, exist_ok=True)
    (keystore_path / "wrapping_key.json").write_text(json.dumps(bundle))

    with requests_mock.Mocker() as mock:
        wrap_mock = mock.post(
            f"{EKMF_ADDON_URL}/addon/ekmf/import/wrap",
            json=_import_result_wire(),
        )

        response = _upload(client, mode, [_payload_doc_wire(key_id)])

        assert response.status_code == 200
        assert wrap_mock.call_count == 1

        body = wrap_mock.request_history[0].json()
        assert set(body) == {"document", "wrapping_key"}
        assert body["wrapping_key"] == bundle

        document_content = json.loads(body["document"]["content"])
        assert document_content["wrapping_key_id"] == key_id

    keys = json.loads((keystore_path / "signing_keys.json").read_text())
    # Keys are now indexed by UUID; verify labels and blobs are stored correctly
    assert len(keys) == len(KEY_LABELS)
    by_label = {v["key_label"]: (k, v) for k, v in keys.items()}
    assert set(by_label) == set(KEY_LABELS)
    assert by_label["test-ed25519-0"][1]["key_type"] == "ed25519"
    assert by_label["test-secp256k1-0"][1]["key_type"] == "secp256k1"
    assert (
        base64.b64decode(by_label["test-ed25519-0"][1]["encrypted_key"])
        == b"fake-ep11-test-ed25519-0"
    )
    # The UUIDs stored as keys must be valid UUIDs
    for key_uuid in keys:
        uuid.UUID(key_uuid)

    # Only the ImportResultDocument (no key blobs) flows back through OSO,
    # and each key in the content must carry the UUID assigned by the backend.
    document_list = _download(client, mode)

    assert document_list.count == 1
    doc = document_list.documents[0]
    assert "key_blobs" not in doc.content

    metadata = json.loads(doc.metadata)
    assert metadata["ekmf_addon"]["document_type"] == "import_result"

    content = json.loads(doc.content)
    by_label = {k["key_label"]: k for k in content["keys"]}
    assert set(by_label) == set(KEY_LABELS)
    for lbl, entry in by_label.items():
        uuid.UUID(entry["key_id"])  # must be a valid UUID


@pytest.mark.parametrize("mode", ["backend"])
def test_backend_wrap_without_bundle_does_not_call_addon(mode, client):
    key_id = str(uuid.uuid4())

    with requests_mock.Mocker() as mock:
        wrap_mock = mock.post(f"{EKMF_ADDON_URL}/addon/ekmf/import/wrap", json={})

        response = _upload(client, mode, [_payload_doc_wire(key_id)])

        assert response.status_code == 200
        assert wrap_mock.call_count == 0

    # Nothing is enqueued for OSO transport
    document_list = _download(client, mode)
    assert document_list.count == 0


@pytest.mark.parametrize("mode", ["backend"])
def test_backend_wrap_rejects_unsupported_key_types(mode, client, keystore_path):
    key_id = str(uuid.uuid4())

    bundle = {
        "key_id": key_id,
        "private_key": base64.b64encode(b"fake-ep11-private-blob").decode(),
    }
    keystore_path.mkdir(parents=True, exist_ok=True)
    (keystore_path / "wrapping_key.json").write_text(json.dumps(bundle))

    with requests_mock.Mocker() as mock:
        wrap_mock = mock.post(f"{EKMF_ADDON_URL}/addon/ekmf/import/wrap", json={})

        response = _upload(
            client, mode, [_payload_doc_wire(key_id, payload_xml=_AES_PAYLOAD_XML)]
        )

        assert response.status_code == 200
        assert wrap_mock.call_count == 0

    # Nothing is persisted or enqueued for OSO transport
    assert not (keystore_path / "signing_keys.json").exists()
    document_list = _download(client, mode)
    assert document_list.count == 0


@pytest.mark.parametrize("mode", ["frontend"])
def test_frontend_key_without_import_sequence(mode, client):
    response = client.get("/api/ekmf/import/key", headers=APPROVER_HEADERS)

    assert response.status_code == 409
    assert response.get_json()["error"] == "conflict"


@pytest.mark.parametrize("mode", ["frontend"])
def test_frontend_rejects_unauthorized_fingerprint(mode, client):
    response = client.get("/api/ekmf/import/key", headers=HEADERS)

    assert response.status_code == 403
    assert response.get_json()["error"] == "forbidden"


@pytest.mark.parametrize("mode", ["frontend"])
def test_frontend_import_state_machine(mode, client):
    key_id = str(uuid.uuid4())

    # 1. Initialize the import sequence
    with requests_mock.Mocker() as mock:
        mock.post(
            f"{EKMF_ADDON_URL}/addon/ekmf/import/init",
            json=_init_doc_wire(),
        )

        response = client.post("/api/ekmf/import/init", headers=APPROVER_HEADERS)

    assert response.status_code == 202
    assert response.get_json()["status"] == "keygen_pending"

    # The wrapping key has not arrived yet
    response = client.get("/api/ekmf/import/key", headers=APPROVER_HEADERS)
    assert response.status_code == 404

    # The InitDocument is queued for OSO transport
    document_list = _download(client, mode)
    assert document_list.count == 1
    metadata = json.loads(document_list.documents[0].metadata)
    assert metadata["ekmf_addon"]["document_type"] == "init"

    # 2. The backend wrapping key document arrives through OSO
    response = _upload(client, mode, [_wrapping_key_doc_wire(key_id)])
    assert response.status_code == 200

    with requests_mock.Mocker() as mock:
        mock.post(
            f"{EKMF_ADDON_URL}/addon/ekmf/import/key",
            json={
                "key_id": key_id,
                "public_key": base64.b64encode(b"fake-public-key").decode(),
                "key_hash": "ab" * 32,
            },
        )

        response = client.get("/api/ekmf/import/key", headers=APPROVER_HEADERS)

    assert response.status_code == 200
    assert response.get_json()["key_id"] == key_id

    # 3. Submit the externally wrapped key material
    with requests_mock.Mocker() as mock:
        mock.post(
            f"{EKMF_ADDON_URL}/addon/ekmf/import/payload",
            json=_payload_doc_wire(key_id),
        )

        response = client.post(
            "/api/ekmf/import/payload",
            data=json.dumps(
                {
                    "transport_key": base64.b64encode(_TRANSPORT_XML).decode(),
                    "payload": base64.b64encode(_PAYLOAD_XML).decode(),
                }
            ),
            content_type="application/json",
            headers=APPROVER_HEADERS,
        )

    assert response.status_code == 200

    # The EkmfPayloadDocument is queued for OSO transport
    document_list = _download(client, mode)
    assert document_list.count == 1
    metadata = json.loads(document_list.documents[0].metadata)
    assert metadata["ekmf_addon"]["document_type"] == "ekmf_payload"

    # The import result has not arrived yet
    response = client.get("/api/ekmf/import/result", headers=APPROVER_HEADERS)
    assert response.status_code == 202
    assert response.get_json()["status"] == "payload_submitted"

    # 4. The backend import result document arrives through OSO; it is the
    #    enriched version (key_id injected by the backend before transport).
    response = _upload(client, mode, [_import_result_doc_wire(with_key_ids=True)])
    assert response.status_code == 200

    with requests_mock.Mocker() as mock:
        # The addon /result response does NOT carry key_id — the frontend
        # merges UUIDs from the cached (enriched) document.
        mock.post(
            f"{EKMF_ADDON_URL}/addon/ekmf/import/result",
            json={
                "keys": [
                    {
                        "key_label": key_label,
                        "hash": "ab" * 32,
                        "checksum": "cdcdcd",
                    }
                    for key_label in KEY_LABELS
                ]
            },
        )

        response = client.get("/api/ekmf/import/result", headers=APPROVER_HEADERS)

    assert response.status_code == 200
    result_keys = response.get_json()["keys"]
    assert [k["key_label"] for k in result_keys] == KEY_LABELS
    # Each key in the result must carry its assigned uuid (merged from cache)
    assert [k["key_id"] for k in result_keys] == [
        KEY_LABEL_TO_ID[lbl] for lbl in KEY_LABELS
    ]


@pytest.mark.parametrize("mode", ["backend"])
def test_ekmf_endpoints_not_available_in_backend_mode(mode, client):
    response = client.post("/api/ekmf/import/init", headers=APPROVER_HEADERS)

    assert response.status_code == 404


def test_keystore_round_trip(tmp_path):
    keystore = SigningKeyStore(tmp_path / "ekmf")

    test_key_id = str(uuid.uuid4())
    keystore.save_keys(
        [
            {
                "key_id": test_key_id,
                "key_label": "test-secp256k1-0",
                "key_type": "secp256k1",
                "encrypted_key": b"fake-blob",
            }
        ]
    )

    keystore.save_wrapping_key({"key_id": "abc", "private_key": "ZmFrZQ=="})

    reloaded = SigningKeyStore(tmp_path / "ekmf")

    assert reloaded.get_all_keys() == [
        (test_key_id, "test-secp256k1-0", "secp256k1", b"fake-blob")
    ]
    assert reloaded.load_wrapping_key() == {"key_id": "abc", "private_key": "ZmFrZQ=="}


def test_parse_ekmf_document_type():
    from fb.ekmf.schemas import DocumentType

    assert parse_ekmf_document_type(_init_doc_wire()) == DocumentType.INIT
    assert (
        parse_ekmf_document_type(_payload_doc_wire("abc")) == DocumentType.EKMF_PAYLOAD
    )
    assert parse_ekmf_document_type({"id": "1", "content": "", "metadata": ""}) is None
    assert (
        parse_ekmf_document_type(
            {"id": "1", "content": "", "metadata": json.dumps({"other": {}})}
        )
        is None
    )
    assert (
        parse_ekmf_document_type(
            {
                "id": "1",
                "content": "",
                "metadata": json.dumps({"ekmf_addon": {"document_type": "bogus"}}),
            }
        )
        is None
    )
