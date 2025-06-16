from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.asymmetric.utils import (
    encode_dss_signature,
    Prehashed,
)
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization

with open(
    "c:\\temp\\c9de5ed51087c6962e5d91a864f94d08d8f00f2c351f0016279ce95bc00fc9d3-pubkey.pem",
    "r",
) as file:
    secret_key_value = file.read().encode()

public_key = serialization.load_pem_public_key(secret_key_value)

# Input data
data = bytes.fromhex("1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef")
sig = bytes.fromhex(
    "9702268725126e1831a50ba8b47bbe168866ffdc6b2ff91048f92baff5c80065e410c206246470793a24c743f816b7bd260b9d509d4f7a67db6deb6341b501d6"
)

# data = bytes.fromhex("4cf719103b608294f1103e424372dc89e0656c595858b600818cf623f2bdfdad")
# sig = bytes.fromhex("31017d21cd19eb29b19647cc0a729e552c31b8992023c27aa65d86a67c90df38f39aa929c7520ba6891a65d0506b602e2df95717e7eacb276f76569938de9e87")
# public_key_hex = "02df7a8e5e0466577e87b1b079c51e0901d766cda29cd0be9fefa0059b0cdd2e92"

# Extract r and s from signature
r = int.from_bytes(sig[: len(sig) // 2], "big")
s = int.from_bytes(sig[len(sig) // 2 :], "big")

# Convert r and s to DER - encoded signature
der_encoded_sig = encode_dss_signature(r, s)

# Decode public key
# public_key = ec.EllipticCurvePublicKey.from_encoded_point(
#    ec.SECP256K1(), bytes.fromhex(public_key_hex)
# )

# List of hash algorithms to test

try:
    public_key.verify(der_encoded_sig, data, ec.ECDSA(Prehashed(SHA256())))
    print("Signature is valid")
except InvalidSignature:
    print("Signature verification failed")
