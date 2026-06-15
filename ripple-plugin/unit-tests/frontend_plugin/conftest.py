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


import os
import uuid

import pytest
from common.certs import (
    approver_fingerprints,
    component_fingerprints,
    create_ED25519_private_key,
    create_secp256k1_private_key,
    create_secp256r1_private_key,
)

from oso_ripple_plugins.frontend_plugin.flask_util.app import create_app
from oso_ripple_plugins.frontend_plugin.flask_util.config import BaseConfig

base_env = {
    "APPROVER_FINGERPRINTS": approver_fingerprints,
    "COMPONENT_FINGERPRINTS": component_fingerprints,
    "FRONTEND_ENDPOINT": "https://frontend",
    "HMZ_AUTH_HOSTNAME": "HMZ_AUTH_HOSTNAME",
    "HMZ_API_HOSTNAME": "HMZ_API_HOSTNAME",
    "VAULTID": "vault_id",
    "TOKEN_EXP": "4h0m0s",
}

secp256k1_env = base_env | {
    "SK": create_secp256k1_private_key().decode(),
}

secp256r1_env = base_env | {
    "SK": create_secp256r1_private_key().decode(),
}

ed25519_env = base_env | {
    "SK": create_ED25519_private_key().decode(),
}

filenames = [str(uuid.uuid4()) for _ in range(5)]


@pytest.fixture(scope="function")
def rootcert(request, monkeypatch):
    monkeypatch.setenv("ROOTCERT", request.param)
    yield request.param


@pytest.fixture(scope="function")
def seed(request, monkeypatch):
    monkeypatch.setenv("SEED", request.param)
    yield request.param


@pytest.fixture(
    params=[
        pytest.param(secp256k1_env, id="secp256k1"),
        pytest.param(secp256r1_env, id="secp256r1"),
        pytest.param(ed25519_env, id="ed25519"),
    ]
)
def set_env(request):
    for k, v in request.param.items():
        os.environ[k] = v


@pytest.fixture
def app(set_env, tmpdir, mocker):
    config = BaseConfig()

    config.PREPARED_DIR = tmpdir + "/app-root/data/frontend_plugin/prepared"
    config.SIGNED_DIR = tmpdir + "/app-root/data/frontend_plugin/signed"

    app = create_app(config=config)
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()
