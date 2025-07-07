#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#
""""""

import random
import string
import importlib
import sys
import pytest
import json
import flask
import base64
import datetime
import pkcs11

from asn1crypto import core as asn1_core

from uuid import uuid4

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec, ed25519

from oso.framework.data.types import V1_3
from oso.framework.plugin import create_app
from oso.framework.plugin.addons.signing_server._key import SECP256K1_Key, ED25519_Key
from oso.framework.plugin.addons.signing_server.generated import server_pb2


@pytest.fixture(scope="session")
def document_set():
    """DocumentList for testing in the above format.

    Returns:
        object:

            Contains OSO and ISV formatted data of the same set.

    """
    oso: list[V1_3.Document] = list()
    isv: list[str] = list()
    for doc in [
        V1_3.Document(
            id=str(uuid4()),
            content="".join(
                random.choices(
                    population=string.ascii_letters + string.digits,
                    k=random.randint(1, 99),
                ),
            ),
            metadata="",
        )
        for _ in range(random.randint(1, 99))
    ]:
        print(doc)
        oso.append(doc)
        isv.append(f"{doc.id}:{doc.content}")

    return {
        "isv": isv,
        "oso": V1_3.DocumentList(documents=oso, count=len(oso)),
    }


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
            "oso.framework.plugin.addons.signing_server.generated.server_pb2_grpc.CryptoStub",
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
            return dict(
                authorized=bool(x.headers.get("X-TEST-SSL-VERIFY", "False")),
                errors=[],
                fingerprint=x.headers.get("X-TEST-SSL-FINGERPRINT", "NOT_VALID"),
                _user=x.headers.get("X-TEST-SSL-FINGERPRINT", "NOT_VALID"),
            )

        monkeypatch.setattr(
            oso.framework.auth.mtls,
            "parse",
            _parse,
        )

    return _fn


@pytest.fixture
def set_grep11_certs(monkeypatch):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ]
    )

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now())
        .not_valid_after(datetime.datetime.now() + datetime.timedelta(days=3650))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost")]),
            critical=False,
        )
        .sign(private_key, hashes.SHA256())
    )

    cert_pem = cert.public_bytes(encoding=serialization.Encoding.PEM)

    key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    monkeypatch.setenv(
        "PLUGIN__ADDONS__0__CA_CERT",
        base64.b64encode(cert_pem).decode(),
    )
    monkeypatch.setenv(
        "PLUGIN__ADDONS__0__CLIENT_KEY",
        base64.b64encode(key_pem).decode(),
    )
    monkeypatch.setenv(
        "PLUGIN__ADDONS__0__CLIENT_CERT",
        base64.b64encode(cert_pem).decode(),
    )


@pytest.fixture
def secp256k1_key_pair():
    private_key = ec.generate_private_key(ec.SECP256K1())
    public_key = private_key.public_key()

    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    ec_point_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    return {
        "private_key": private_key,
        "public_key": public_key,
        "private_bytes": private_bytes,
        "ec_point_bytes": ec_point_bytes,
        "public_bytes": public_pem,
    }


@pytest.fixture
def ed25519_key_pair():
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    ec_point_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    return {
        "private_key": private_key,
        "public_key": public_key,
        "private_bytes": private_bytes,
        "ec_point_bytes": ec_point_bytes,  # actually just raw Ed25519 key bytes
        "public_bytes": public_pem,
    }


@pytest.fixture
def grpc_stub_mock(secp256k1_key_pair, ed25519_key_pair):
    # Create a class to mock the stub
    class MockCryptoStub:
        def __init__(self, _=None):
            pass

        def GenerateKeyPair(self, request: server_pb2.GenerateKeyPairRequest):
            priv_key = server_pb2.KeyBlob()

            ec_point_bytes = None

            match request.PubKeyTemplate[pkcs11.Attribute.EC_PARAMS].AttributeB.hex():
                case SECP256K1_Key.Oid:
                    ec_point_bytes = secp256k1_key_pair["ec_point_bytes"]
                case ED25519_Key.Oid:
                    ec_point_bytes = ed25519_key_pair["ec_point_bytes"]
                case _:
                    raise Exception("Unsupported Key OID")

            octet_string = asn1_core.OctetString(ec_point_bytes)

            der_encoded_ec_point = octet_string.dump()

            ec_point_attribute_value = server_pb2.AttributeValue(
                AttributeB=der_encoded_ec_point
            )

            pub_key = server_pb2.KeyBlob(
                Attributes={pkcs11.Attribute.EC_POINT: ec_point_attribute_value}
            )

            response = server_pb2.GenerateKeyPairResponse(
                PrivKey=priv_key, PubKey=pub_key
            )

            return response

        def GetMechanismList(self, _):
            return server_pb2.GetMechanismListResponse(
                Mechs=[
                    pkcs11.Mechanism.ECDSA,
                    pkcs11.Mechanism._VENDOR_DEFINED + 0x1001C,
                ]
            )

    return MockCryptoStub


@pytest.fixture()
def app(
    mode,
    monkeypatch,
    _setup_app,
    _enable_mtls,
    tmp_path,
    set_grep11_certs,
    grpc_stub_mock,
):
    monkeypatch.setenv("PLUGIN__MODE", mode)
    monkeypatch.setenv(
        "PLUGIN__APPLICATION",
        "fb.plugin:FBPlugin",
    )
    monkeypatch.setenv(
        "PLUGIN__ADDONS__0__TYPE",
        "oso.framework.plugin.addons.signing_server",
    )
    monkeypatch.setenv(
        "PLUGIN__ADDONS__0__GREP11_ENDPOINT",
        "localhost",
    )
    monkeypatch.setenv(
        "PLUGIN__ADDONS__0__GREP11_PORT",
        "9876",
    )
    monkeypatch.setenv(
        "PLUGIN__ADDONS__0__KEYSTORE_PATH",
        str(tmp_path),
    )
    monkeypatch.setenv(
        "PLUGIN__ADDONS__0__EXTRA",
        "test",
    )
    monkeypatch.setenv(
        "FB__min_keys",
        "2",
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
