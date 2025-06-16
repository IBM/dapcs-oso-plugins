# EdDSA Signature Verification
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

message_binary = bytes.fromhex(
    "message payload in hex"
)  # Replace with your message in hex
signature = bytes.fromhex("signature in hex")  # Replace with your signature in hex
public_key_hex = "public key in hex"  # Replace with your public key in hex

# Convert the public key from hex to bytes
public_key_bytes = bytes.fromhex(public_key_hex)

# Load the public key
public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)

# Verify the signature
try:
    public_key.verify(signature, message_binary)
    print("Signature is valid.")
except InvalidSignature:
    print("Signature verification failed.")
