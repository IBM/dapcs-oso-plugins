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

import base64
from datetime import UTC, datetime, timedelta
from urllib.parse import quote

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa
from cryptography.x509.oid import NameOID


def random_hash():
    digest = hashes.Hash(hashes.SHA256())
    fingerprint = base64.b64encode(digest.finalize()).rstrip(b"=").decode("utf-8")
    return f"SHA256:{fingerprint}"


def create_ec_private_key(curve: ec.EllipticCurve = ec.SECP256K1()):
    private_key = ec.generate_private_key(curve, backend=default_backend())
    private_key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    base64_private_key = base64.b64encode(private_key_bytes)
    return base64_private_key


def create_secp256k1_private_key():
    return create_ec_private_key(curve=ec.SECP256K1())


def create_secp256r1_private_key():
    return create_ec_private_key(curve=ec.SECP256R1())


def create_ED25519_private_key():
    private_key = ed25519.Ed25519PrivateKey.generate()
    private_key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    base64_private_key = base64.b64encode(private_key_bytes)
    return base64_private_key


def create_key(subject):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    public_key = private_key.public_key()

    cert = (
        x509.CertificateBuilder()
        .subject_name(
            x509.Name(
                [
                    x509.NameAttribute(NameOID.COMMON_NAME, subject),
                ]
            )
        )
        .issuer_name(
            x509.Name(
                [
                    x509.NameAttribute(NameOID.COMMON_NAME, "ISSUER"),
                ]
            )
        )
        .not_valid_before(datetime.now(UTC))
        .not_valid_after(datetime.now(UTC) + timedelta(days=365))
        .serial_number(x509.random_serial_number())
        .public_key(public_key)
        .sign(private_key, hashes.SHA256())
    )

    pub_cert = cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")

    pub_key = cert.public_key().public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    )

    parts = pub_key.split(b" ")
    key_bytes = base64.b64decode(parts[1])

    digest = hashes.Hash(hashes.SHA256())
    digest.update(key_bytes)
    fingerprint = base64.b64encode(digest.finalize()).rstrip(b"=").decode("utf-8")

    openssh_fingerprint = f"SHA256:{fingerprint}"

    return quote(pub_cert), openssh_fingerprint


pem_public_key_no_subj, _ = create_key("?")
pem_public_key_subj_is_USER1, _ = create_key("USER1")

approver_cert, approver_fingerprint = create_key(subject="APPROVER")
approver_cert2, approver_fingerprint2 = create_key(subject="APPROVER2")
approver_cert3, approver_fingerprint3 = create_key(subject="APPROVER3")
approver_fingerprints = "\n".join(
    [
        approver_fingerprint,
        approver_fingerprint2,
        approver_fingerprint3,
    ]
)

component_cert, component_fingerprint = create_key(subject="COMPONENT")
component_fingerprints = "\n".join(
    [
        component_fingerprint,
        random_hash(),
        random_hash(),
    ]
)

admin_cert, admin_fingerprint = create_key(subject="ADMIN")
admin_fingerprints = "\n".join(
    [
        admin_fingerprint,
        random_hash(),
        random_hash(),
    ]
)
