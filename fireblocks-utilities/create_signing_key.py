from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
)
from cryptography.x509.oid import NameOID
from datetime import datetime, timedelta, timezone
from fireblocks.models.create_signing_key_dto import CreateSigningKeyDto
from fireblocks.client import Fireblocks
from fireblocks.client_configuration import ClientConfiguration
from fireblocks.base_path import BasePath
import os

# load the secret key content from a file
with open(os.environ["SECRET_KEY_PATH"], "r") as file:
    secret_key_value = file.read()

# build the configuration
configuration = ClientConfiguration(
    api_key=os.environ["FB_API_KEY"],
    secret_key=secret_key_value,
    base_path=BasePath.US,
)

with open(os.environ["VALIDATION_PRIVATEKEY_PATH"], "r") as file:
    validation_privkey_value = file.read()

with open(os.environ["SIGNING_PUBLICKEY_PATH"], "r") as file:
    signing_publickey_value = file.read()
    print(signing_publickey_value)

key_id = os.environ["KEYID"]
user_id = os.environ["USERID"]


def issue_certificate(
    root_ca_private_key, certificate_pubkey, common_name, issuer_name
) -> x509.Certificate:
    # For Ed25519, only the Ed25519 signature algorithm is used
    sign_algo = (
        None
        if isinstance(root_ca_private_key, ed25519.Ed25519PrivateKey)
        else hashes.SHA256()
    )

    now = datetime.now(timezone.utc)
    time_delta = timedelta(minutes=5)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(
            x509.Name(
                [
                    x509.NameAttribute(NameOID.COMMON_NAME, common_name),
                ]
            )
        )
        .issuer_name(
            x509.Name(
                [
                    x509.NameAttribute(NameOID.COMMON_NAME, issuer_name),
                ]
            )
        )
        .public_key(certificate_pubkey)
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + time_delta)
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(
                root_ca_private_key.public_key()
            ),
            critical=False,
        )
        .sign(root_ca_private_key, sign_algo)
    )

    return certificate


def wrap_external_key(validator_privkey, external_public):
    COMMON_NAME = "ExampleName"
    ISSUER_NAME = "ExampleIssuerName"
    cert = issue_certificate(
        validator_privkey, external_public, COMMON_NAME, ISSUER_NAME
    )
    return cert.public_bytes(encoding=serialization.Encoding.PEM).decode()


# Enter a context with an instance of the API client
with Fireblocks(configuration) as fireblocks:
    # Wrap singing key with validation key
    encoded_sign_pub_key = load_pem_public_key(signing_publickey_value.encode())
    signed_key_cert_pem = wrap_external_key(
        load_pem_private_key(validation_privkey_value.encode(), password=None),
        encoded_sign_pub_key,
    )
    print(signed_key_cert_pem)

    # Add a new validation key
    create_signing_key_dto = CreateSigningKeyDto(
        signed_cert_pem=signed_key_cert_pem,
        signing_device_key_id=key_id,
        agent_user_id=user_id,
    )
    idempotency_key = "idempotency_key_0"  # str | A unique identifier for the request. If the request is sent multiple times with the same idempotency key, the server will return the same response as the first request. The idempotency key is valid for 24 hours. (optional)
    try:
        api_response = fireblocks.key_link_beta.create_signing_key(
            create_signing_key_dto, idempotency_key=idempotency_key
        ).result()
        print("The response of KeyLinkBetaApi->create_signing_key:\n")
        print(api_response)
    except Exception as e:
        print("Exception when calling KeyLinkBetaApi->create_signing_key: %s\n" % e)
