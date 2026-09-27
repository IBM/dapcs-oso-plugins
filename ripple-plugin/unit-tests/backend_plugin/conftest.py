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
from common.certs import approver_fingerprints, component_fingerprints

from oso_ripple_plugins.backend_plugin.flask_util.app import create_app
from oso_ripple_plugins.backend_plugin.flask_util.config import BaseConfig

env = {
    "Vault__Ids__0": "test_vault_id",
    "COLD_BRIDGE_ENDPOINT__0": "https://backend",
    "APPROVER_FINGERPRINTS": approver_fingerprints,
    "COMPONENT_FINGERPRINTS": component_fingerprints,
}


filenames = [str(uuid.uuid4()) for _ in range(5)]


@pytest.fixture(scope="function")
def seed(request, app):
    # Patch the already-created manager directly — BackendPluginManager reads
    # OSOENCRYPTIONPASS once at __init__ time (before the seed fixture runs),
    # so setting the env var is not enough.
    app.bpm.seed = request.param
    yield request.param
    app.bpm.seed = ""


@pytest.fixture
def set_env():
    for k, v in env.items():
        os.environ[k] = v


@pytest.fixture
def app(set_env, tmpdir, mocker):
    config = BaseConfig()

    config.PREPARED_DIR = tmpdir + "/app-root/data/backend_plugin/prepared"
    config.SIGNED_DIR = tmpdir + "/app-root/data/backend_plugin/signed"

    app = create_app(config=config)
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()
