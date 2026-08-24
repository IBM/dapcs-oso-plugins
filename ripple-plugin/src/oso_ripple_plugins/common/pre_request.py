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
import logging
import re
import sys
from os import environ
from typing import List
from urllib.parse import unquote

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from flask import Flask, abort, request, request_started

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


sha256_regex = re.compile(r"^SHA256:[A-Za-z0-9+/]{43}=?$")


def is_sha256_hash(s):
    """Check if a string is a valid OpenSSH SHA256 hash."""
    if re.match(sha256_regex, s):
        return True
    else:
        return False


def load_fingerprints() -> List[str]:
    try:
        fingerprints = [f for f in environ["COMPONENT_FINGERPRINTS"].split()]
    except KeyError as e:
        logger.info("Could not find COMPONENT_FINGERPRINTS in environment variables")
        raise e

    for fingerprint in fingerprints:
        if not is_sha256_hash(fingerprint):
            logger.error(
                f"{fingerprint}, located in COMPONENT_FINGERPRINTS, is not a OpenSSH"
                " SHA256 hash"
            )
            raise Exception(
                f"{fingerprint}, located in COMPONENT_FINGERPRINTS, is not a OpenSSH"
                " SHA256 hash"
            )

    return fingerprints


def set_cert():
    cert_bytes = unquote(request.headers["X-SSL-CERT"]).encode("utf-8")
    request.x_oso = dict(
        x509_cert=x509.load_pem_x509_certificate(cert_bytes, default_backend())
    )


def bind_flask_before_request(sender: Flask, **extras) -> None:
    logger.info(f"HTTP Method: {request.method} URL Path: {request.path}")

    client_verify = request.headers.get("X-SSL-CLIENT-VERIFY", "FAILED")
    if client_verify != "SUCCESS":
        logger.info(f"Could not verify certificate, client verify: {client_verify}")
        abort(401, {"error": {"code": "401", "message": "Unauthorized"}})

    if "X-SSL-CERT" not in request.headers:
        sender.logger.info("[X-SSL-CERT] not in request header")
        abort(401, {"error": {"code": "401", "message": "Unauthorized"}})
    set_cert()

    pub_key = (
        request.x_oso["x509_cert"]
        .public_key()
        .public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH,
        )
    )
    parts = pub_key.split(b" ")
    key_bytes = base64.b64decode(parts[1])

    digest = hashes.Hash(hashes.SHA256())
    digest.update(key_bytes)
    fingerprint = base64.b64encode(digest.finalize()).rstrip(b"=").decode("utf-8")

    logger.info(f"Fingerprint: SHA256:{fingerprint}")

    user = request.x_oso["x509_cert"].subject.rfc4514_string()
    logger.info(f"User: {user}")
    logger.info("AUTHENTICATED")

    if not fingerprint:
        logger.info("Fingerprint for client cert was not generated")
        abort(403, {"error": {"code": "403", "message": "Forbidden"}})

    if f"SHA256:{fingerprint}" not in authorized_fingerprints:
        logger.info(
            f"Could not find fingerprint SHA256:{fingerprint} in COMPONENT_FINGERPRINTS"
        )
        abort(403, {"error": {"code": "403", "message": "Forbidden"}})


def configure_flask_common(app: Flask) -> None:
    global authorized_fingerprints
    authorized_fingerprints = load_fingerprints()
    request_started.connect(bind_flask_before_request, app)
