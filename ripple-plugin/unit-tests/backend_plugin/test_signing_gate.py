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


import json
import logging
import time

import pytest
import requests_mock
from common.certs import component_cert

from oso_ripple_plugins.backend_plugin.backend_plugin_manager import (
    BackendPluginManager,
)
from oso_ripple_plugins.common import errors


def counters(**overrides):
    """Full cold-bridge /v1/feed/status counter payload, all zero by default."""
    payload = {}
    for prefix in ("transaction", "account", "manifest", "rewrap"):
        payload[f"{prefix}ToSign"] = 0
        payload[f"{prefix}Signed"] = 0
    payload.update(overrides)
    return payload


def make_document(vault_id, num_transactions=1):
    return {
        "id": f"{vault_id}-doc",
        "content": json.dumps(
            {
                "vaultId": vault_id,
                "transactions": [
                    {"transactionId": f"{vault_id}-tx-{i}"}
                    for i in range(num_transactions)
                ],
                "accounts": [],
                "manifests": [],
                "rewraps": [],
                "vaults": [],
            }
        ),
        "metadata": "",
    }


@pytest.fixture
def manager(monkeypatch):
    monkeypatch.setenv("Vault__Ids__0", "vault1")
    monkeypatch.setenv("COLD_BRIDGE_ENDPOINT__0", "https://bridge1")
    monkeypatch.setenv("Vault__Ids__1", "vault2")
    monkeypatch.setenv("COLD_BRIDGE_ENDPOINT__1", "https://bridge2")
    monkeypatch.delenv("Vault__Ids__2", raising=False)
    monkeypatch.delenv("OSOENCRYPTIONPASS", raising=False)
    return BackendPluginManager()


def upload_to(manager, m, vault_ids, num_transactions=2):
    """Run bulk_upload for the given vaults against mocked bridge endpoints."""
    for vault_id in vault_ids:
        endpoint = manager.vault_bridge_map[vault_id]
        m.post(f"{endpoint}/v1/feed/upload", json={}, status_code=200)
    manager.bulk_upload(
        [make_document(vault_id, num_transactions) for vault_id in vault_ids]
    )


def test_status_without_upload_is_ready(manager):
    with requests_mock.mock() as m:
        m.get("https://bridge1/v1/feed/status", json=counters(), status_code=200)
        m.get("https://bridge2/v1/feed/status", json=counters(), status_code=200)
        manager.backend_status()


def test_status_holds_while_to_sign_outstanding(manager):
    with requests_mock.mock() as m:
        upload_to(manager, m, ["vault1"])

        m.get(
            "https://bridge1/v1/feed/status",
            json=counters(transactionToSign=2),
            status_code=200,
        )
        m.get("https://bridge2/v1/feed/status", json=counters(), status_code=200)

        with pytest.raises(errors.SigningInProgress) as excinfo:
            manager.backend_status()
        assert "vault1" in str(excinfo.value)


def test_status_holds_before_vault_registers_feed(manager):
    # All-zero counters right after an upload mean "not started", not "done".
    with requests_mock.mock() as m:
        upload_to(manager, m, ["vault1"], num_transactions=3)

        m.get("https://bridge1/v1/feed/status", json=counters(), status_code=200)
        m.get("https://bridge2/v1/feed/status", json=counters(), status_code=200)

        with pytest.raises(errors.SigningInProgress) as excinfo:
            manager.backend_status()
        assert "shortfall" in str(excinfo.value)
        assert "transactions" in str(excinfo.value)


def test_status_ready_when_all_signed(manager):
    with requests_mock.mock() as m:
        upload_to(manager, m, ["vault1"], num_transactions=2)

        m.get(
            "https://bridge1/v1/feed/status",
            json=counters(transactionSigned=2),
            status_code=200,
        )
        m.get("https://bridge2/v1/feed/status", json=counters(), status_code=200)

        manager.backend_status()
        assert manager._signing_state == {}

        # State is cleared: pathological counters afterwards do not re-gate
        m.get(
            "https://bridge1/v1/feed/status",
            json=counters(transactionToSign=99),
            status_code=200,
        )
        manager.backend_status()


def test_status_degrades_to_ready_after_stall(manager, caplog):
    frozen = counters(transactionToSign=1, transactionSigned=1)
    with requests_mock.mock() as m:
        upload_to(manager, m, ["vault1"], num_transactions=2)

        m.get("https://bridge1/v1/feed/status", json=frozen, status_code=200)
        m.get("https://bridge2/v1/feed/status", json=counters(), status_code=200)

        # First poll records the counters and keeps gating
        with pytest.raises(errors.SigningInProgress):
            manager.backend_status()

        # Counters unchanged past the stall window: degrade to ready
        state = manager._signing_state["vault1"]
        state["last_progress_at"] -= manager.signing_stall_secs + 1
        with caplog.at_level(logging.ERROR):
            manager.backend_status()

        assert manager._signing_state == {}
        assert any("stalled" in record.message for record in caplog.records)


def test_stall_clock_resets_while_counters_move(manager):
    with requests_mock.mock() as m:
        upload_to(manager, m, ["vault1"], num_transactions=2)

        m.get(
            "https://bridge1/v1/feed/status",
            json=counters(transactionToSign=2),
            status_code=200,
        )
        m.get("https://bridge2/v1/feed/status", json=counters(), status_code=200)
        with pytest.raises(errors.SigningInProgress):
            manager.backend_status()

        # Progress: counters changed, so the rewound stall clock is reset
        manager._signing_state["vault1"]["last_progress_at"] -= (
            manager.signing_stall_secs + 1
        )
        m.get(
            "https://bridge1/v1/feed/status",
            json=counters(transactionToSign=1, transactionSigned=1),
            status_code=200,
        )
        with pytest.raises(errors.SigningInProgress):
            manager.backend_status()
        assert time.time() - manager._signing_state["vault1"]["last_progress_at"] < 5


def test_status_gates_per_vault(manager):
    with requests_mock.mock() as m:
        upload_to(manager, m, ["vault1", "vault2"], num_transactions=2)

        m.get(
            "https://bridge1/v1/feed/status",
            json=counters(transactionSigned=2),
            status_code=200,
        )
        m.get(
            "https://bridge2/v1/feed/status",
            json=counters(transactionToSign=2),
            status_code=200,
        )

        with pytest.raises(errors.SigningInProgress) as excinfo:
            manager.backend_status()
        assert "vault2" in str(excinfo.value)
        assert "vault1" not in str(excinfo.value)
        assert "vault1" not in manager._signing_state

        # vault2 finishes: gate releases
        m.get(
            "https://bridge2/v1/feed/status",
            json=counters(transactionSigned=2),
            status_code=200,
        )
        manager.backend_status()
        assert manager._signing_state == {}


def test_failed_upload_is_not_gated(manager):
    with requests_mock.mock() as m:
        m.post("https://bridge1/v1/feed/upload", json={}, status_code=200)
        m.post("https://bridge2/v1/feed/upload", status_code=500)

        manager.bulk_upload([make_document("vault1"), make_document("vault2")])

        assert "vault1" in manager._signing_state
        assert "vault2" not in manager._signing_state


def test_upload_raises_when_all_vaults_fail(manager):
    with requests_mock.mock() as m:
        m.post("https://bridge1/v1/feed/upload", status_code=500)
        m.post("https://bridge2/v1/feed/upload", status_code=500)

        with pytest.raises(Exception, match="all vaults"):
            manager.bulk_upload([make_document("vault1"), make_document("vault2")])
        assert manager._signing_state == {}


def test_bridge_error_does_not_touch_stall_clock(manager):
    with requests_mock.mock() as m:
        upload_to(manager, m, ["vault1"], num_transactions=2)

        m.get("https://bridge1/v1/feed/status", status_code=502)
        m.get("https://bridge2/v1/feed/status", json=counters(), status_code=200)

        with pytest.raises(Exception) as excinfo:
            manager.backend_status()
        assert not isinstance(excinfo.value, errors.SigningInProgress)
        assert "vault1" in manager._signing_state


def test_status_endpoint_reports_signing_in_progress(client):
    upload_payload = {"documents": [make_document("test_vault_id", num_transactions=2)]}

    with requests_mock.mock() as m:
        m.post("https://backend/v1/feed/upload", json={}, status_code=200)
        response = client.post(
            "api/backend/v1alpha1/documents",
            headers={
                "X-SSL-CERT": component_cert,
                "X-SSL-CLIENT-VERIFY": "SUCCESS",
            },
            data=json.dumps(upload_payload),
            content_type="application/json",
        )
        assert response.status_code == 204

        status_headers = {
            "X-SSL-CERT": component_cert,
            "X-SSL-CLIENT-VERIFY": "SUCCESS",
        }

        m.get(
            "https://backend/v1/feed/status",
            json=counters(transactionToSign=2),
            status_code=200,
        )
        response = client.get("api/backend/v1alpha1/status", headers=status_headers)
        assert response.status_code == 503
        assert response.json["status_code"] == 503
        assert response.json["errors"][0]["code"] == "SIGNING_IN_PROGRESS"

        m.get(
            "https://backend/v1/feed/status",
            json=counters(transactionSigned=2),
            status_code=200,
        )
        response = client.get("api/backend/v1alpha1/status", headers=status_headers)
        assert response.status_code == 200
        assert response.json == {"status_code": 200, "status": "OK", "errors": []}
