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
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ALGORITHM = "AES"
KEY_SIZE = 32  # 256 bits
ITERATION_COUNT = 100000
TAG_LENGTH = 16  # 128 bits


def encrypt(plaintext, password):
    salt = os.urandom(16)
    key = derive_key_from_password(password, salt)

    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)

    encoded_ciphertext = base64.b64encode(ciphertext).decode("utf-8")
    encoded_nonce = base64.b64encode(nonce).decode("utf-8")
    encoded_salt = base64.b64encode(salt).decode("utf-8")

    return f"{encoded_salt}:{encoded_nonce}:{encoded_ciphertext}"


def decrypt(ciphertext, password):
    parts = ciphertext.split(":")
    encoded_salt, encoded_nonce, encoded_ciphertext = parts

    ciphertext = base64.b64decode(encoded_ciphertext)
    nonce = base64.b64decode(encoded_nonce)
    salt = base64.b64decode(encoded_salt)

    key = derive_key_from_password(password, salt)

    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)

    return plaintext.decode("utf-8")


def derive_key_from_password(password, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=ITERATION_COUNT,
        backend=default_backend(),
    )
    return kdf.derive(password.encode())
