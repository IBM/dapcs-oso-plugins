#
# (c) Copyright IBM Corp. 2024, 2026
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
""""""

import base64
import hashlib
import importlib
import json
import sys

import flask
import pytest

from oso.framework.plugin import create_app

from fb.ekmf import CKM
from fb.ekmf.generated import server_pb2

# Matches the signature in tests/data/signed_doc.json
MOCK_SIGNATURE = bytes.fromhex(
    "9702268725126e1831a50ba8b47bbe168866ffdc6b2ff91048f92baff5c80065"
    "e410c206246470793a24c743f816b7bd260b9d509d4f7a67db6deb6341b501d6"
)

# The signingDeviceKeyId in tests/data/unsigned_doc.json
SIGNING_DEVICE_KEY_ID = "46c3933b-7d9a-41a4-9d69-696527902c5e"

EKMF_ADDON_PORT = "8081"

# OpenSSH-format fingerprint allowed to call the EKMF import endpoints; the
# fake mtls parser below decodes SHA256: headers the same way the real one
# fingerprints certificates.
APPROVER_FINGERPRINT = (
    "SHA256:" + base64.b64encode(hashlib.sha256(b"test-approver").digest()).decode()
)


@pytest.fixture(scope="function")
def _cleanup():
    to_removes = [
        k
        for k in sys.modules.keys()
        if k.startswith("oso") or k.startswith("tests.oso")
    ]
    for to_remove in to_removes:
        del sys.modules[to_remove]


@pytest.fixture(scope="function")
def ConfigManager(_cleanup):
    # Clear cached config
    import oso.framework.config

    importlib.reload(oso.framework.config)
    return oso.framework.config.ConfigManager


@pytest.fixture(scope="function")
def LoggingFactory(_cleanup, ConfigManager):
    assert ConfigManager
    # Register logging config type
    # Clear logging singleton
    import oso.framework.core.logging
    from oso.framework.config.models import logging  # noqa: F401

    importlib.reload(oso.framework.core.logging)
    return oso.framework.core.logging.LoggingFactory


@pytest.fixture(scope="function")
def _setup_app(ConfigManager, LoggingFactory, monkeypatch, grpc_stub_mock):
    def _fn():
        monkeypatch.setattr(
            "fb.ekmf.generated.server_pb2_grpc.CryptoStub",
            grpc_stub_mock,
        )

        from oso.framework.auth.common import AuthConfig  # noqa: F401
        from oso.framework.config.models.logging import LoggingConfig  # noqa: F401
        from oso.framework.plugin.extension import PluginConfig  # noqa: F401

        config = ConfigManager.reload()
        LoggingFactory(**config.logging.model_dump())

    return _fn


@pytest.fixture(scope="function")
def _enable_mtls(monkeypatch, _setup_app):
    """
    Override the mTLS parser to use the headers ``X-TEST-SSL-VERIFY`` and
    ``X-TEST-SSL-FINGERPRINT`` to authenticate the user. A fingerprint value of
    ``VALID`` will allow the request to go through.
    """
    monkeypatch.setenv(
        "AUTH__PARSERS__0__TYPE",
        "oso.framework.auth.mtls",
    )
    monkeypatch.setenv(
        "AUTH__PARSERS__0__ALLOWLIST",
        json.dumps({"component": ["VALID", "ALSO_VALID"]}),
    )

    def _fn():
        import oso.framework.auth.mtls

        def _parse_allowlist(x):
            return x

        monkeypatch.setattr(
            oso.framework.auth.mtls,
            "parse_allowlist",
            _parse_allowlist,
        )

        def _parse(x):
            fp_header = x.headers.get("X-TEST-SSL-FINGERPRINT", "NOT_VALID")

            # The real parser returns the SHA256 digest bytes of the
            # certificate's public key.
            fingerprint = (
                base64.b64decode(fp_header.removeprefix("SHA256:"))
                if fp_header.startswith("SHA256:")
                else fp_header
            )

            return dict(
                authorized=bool(x.headers.get("X-TEST-SSL-VERIFY", "False")),
                errors=[],
                fingerprint=fingerprint,
                _user=fingerprint,
            )

        monkeypatch.setattr(
            oso.framework.auth.mtls,
            "parse",
            _parse,
        )

    return _fn


@pytest.fixture
def grpc_stub_mock():
    class MockCryptoStub:
        sign_calls: list[server_pb2.SignSingleRequest] = []

        def __init__(self, _=None):
            pass

        def SignSingle(self, request: server_pb2.SignSingleRequest):
            MockCryptoStub.sign_calls.append(request)

            return server_pb2.SignSingleResponse(Signature=MOCK_SIGNATURE)

        def GetMechanismList(self, _):
            return server_pb2.GetMechanismListResponse(
                Mechs=[
                    CKM.ECDSA,
                    CKM.IBM_ED25519_SHA512,
                ]
            )

    MockCryptoStub.sign_calls.clear()

    return MockCryptoStub


@pytest.fixture
def keystore_path(tmp_path):
    return tmp_path / "ekmf"


@pytest.fixture
def seeded_keystore(keystore_path):
    """Write imported key blobs for the key ids referenced by the test data."""
    keystore_path.mkdir(parents=True, exist_ok=True)

    keys = {
        SIGNING_DEVICE_KEY_ID: {
            "key_type": "secp256k1",
            "encrypted_key": base64.b64encode(b"fake-secp256k1-blob").decode(),
        },
        "test-ed25519-0": {
            "key_type": "ed25519",
            "encrypted_key": base64.b64encode(b"fake-ed25519-blob").decode(),
        },
    }

    (keystore_path / "signing_keys.json").write_text(json.dumps(keys))

    return keys


@pytest.fixture()
def app(
    mode,
    monkeypatch,
    _setup_app,
    _enable_mtls,
    keystore_path,
    grpc_stub_mock,
):
    monkeypatch.setenv("PLUGIN__MODE", mode)
    monkeypatch.setenv(
        "PLUGIN__APPLICATION",
        "fb.plugin:FBPlugin",
    )
    monkeypatch.setenv(
        "FB__EKMF_ADDON_PORT",
        EKMF_ADDON_PORT,
    )
    monkeypatch.setenv(
        "FB__GREP11_ENDPOINT",
        "localhost",
    )
    monkeypatch.setenv(
        "FB__GREP11_PORT",
        "9876",
    )
    monkeypatch.setenv(
        "FB__KEYSTORE_PATH",
        str(keystore_path),
    )
    monkeypatch.setenv(
        "FB__EKMF_APPROVER_FINGERPRINTS",
        APPROVER_FINGERPRINT,
    )

    _enable_mtls()
    _setup_app()

    app = create_app()
    app.config.update(
        {
            "TESTING": True,
        }
    )
    with app.app_context():
        yield app


@pytest.fixture()
def client(app: flask.Flask):
    return app.test_client()
