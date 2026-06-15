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
import requests_mock

from oso_ripple_plugins.common import utils
from oso_ripple_plugins.frontend_plugin.frontend_plugin_manager import (
    FrontendPluginManager,
)


@pytest.mark.parametrize("rootcert", ["bXlfY2VydA=="], indirect=True)
def test_create_cert(set_env, rootcert, mocker):
    mock_temp_file = mocker.patch(
        "oso_ripple_plugins.frontend_plugin.frontend_plugin_manager.tempfile.NamedTemporaryFile",
        autospec=True,
    )
    mock_file_handle = mock_temp_file.return_value.__enter__.return_value
    FrontendPluginManager()
    mock_file_handle.write.assert_called_once_with(bytes("my_cert", "utf-8"))


def test_create_no_cert(set_env, mocker):
    mock_temp_file = mocker.patch(
        "oso_ripple_plugins.frontend_plugin.frontend_plugin_manager.tempfile.NamedTemporaryFile",
        autospec=True,
    )
    mock_file_handle = mock_temp_file.return_value.__enter__.return_value
    FrontendPluginManager()
    assert not mock_file_handle.write.called


def test_token_cache(set_env, monkeypatch):
    monkeypatch.setenv("TOKEN_EXP", "5s")
    monkeypatch.setenv("TOKEN_EXP_BUFF", "0")

    token_url = "https://hmz_auth_hostname/token"
    with requests_mock.mock() as m:
        m.post(
            token_url,
            json=lambda tok, exp: {"access_token": str(uuid.uuid4())},
            status_code=200,
        )

        fpm = FrontendPluginManager()
        token = fpm.get_token()

        # token returned should be the same (from cache)
        assert token == fpm.get_token()

        # Default token expiration buffer to 10 sec - should expire token
        monkeypatch.delenv("TOKEN_EXP_BUFF", raising=False)

        # new token should be generated
        token_new = fpm.get_token()
        assert not token == token_new

        # new token returned should be the same (from cache)
        monkeypatch.setenv("TOKEN_EXP_BUFF", "0")
        assert token_new == fpm.get_token()


def test_parse_wait_time(set_env, monkeypatch):
    times = [
        ["4h", 14400],
        ["5m", 300],
        ["5s", 5],
        ["2h3m4s", 7384],
        ["0", 0],
        ["abcd", 0],
    ]

    for time_check in times:
        monkeypatch.setenv("TOKEN_EXP", time_check[0])
        assert time_check[1] == utils.parse_wait_time(os.environ.get("TOKEN_EXP"))
