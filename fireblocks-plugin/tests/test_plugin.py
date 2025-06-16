#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2025
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

import json
from typing import TypeVar
import uuid
import pydantic
import pytest
import requests_mock

from fb.plugin import get_signing_api_endpoint
from fb.types import MessagesRequest, MessagesStatusRequest, MessagesStatusResponse

from oso.framework.data.types import V1_3


T = TypeVar("T", bound=pydantic.BaseModel)


def load_model(file_path: str, model: type[T]) -> T:
    with open(file_path, "r") as file:
        json_data = json.load(file)

    model_instance = model.model_validate(json_data)
    return model_instance


unsigned_doc = load_model("tests/data/unsigned_doc.json", V1_3.Document)

signed_doc = load_model("tests/data/signed_doc.json", V1_3.Document)

messages_request = load_model("tests/data/messages_request.json", MessagesRequest)


@pytest.mark.parametrize("mode", ["frontend"])
def test_frontend_isv2oso(mode, client):
    response = client.post(
        "/internal/messagesToSign",
        data=messages_request.model_dump_json(),
        content_type="application/json",
        headers={
            "X-TEST-SSL-VERIFY": "True",
            "X-TEST-SSL-FINGERPRINT": "VALID",
        },
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "statuses": [
            {
                "requestId": "a4963c1f-f2be-4e3c-9a3a-0d2627aaf9bc",
                "response": {},
                "status": "PENDING_SIGN",
                "type": "KEY_LINK_PROOF_OF_OWNERSHIP_RESPONSE",
            }
        ]
    }

    messages_status_request = MessagesStatusRequest(
        requestsIds=[uuid.UUID("a4963c1f-f2be-4e3c-9a3a-0d2627aaf9bc")]
    )

    response = client.post(
        "/internal/messagesStatus",
        data=messages_status_request.model_dump_json(),
        content_type="application/json",
        headers={
            "X-TEST-SSL-VERIFY": "True",
            "X-TEST-SSL-FINGERPRINT": "VALID",
        },
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "statuses": [
            {
                "type": "KEY_LINK_PROOF_OF_OWNERSHIP_RESPONSE",
                "status": "PENDING_SIGN",
                "requestId": "a4963c1f-f2be-4e3c-9a3a-0d2627aaf9bc",
                "response": {},
            }
        ]
    }

    response = client.get(
        f"/api/{mode}/v1alpha1/documents",
        headers={
            "X-TEST-SSL-VERIFY": "True",
            "X-TEST-SSL-FINGERPRINT": "VALID",
        },
    )

    assert response.status_code == 200
    assert V1_3.DocumentList.model_validate_json(response.data) == V1_3.DocumentList(
        documents=[unsigned_doc], count=1
    )


@pytest.mark.parametrize("mode", ["frontend"])
def test_frontend_oso2isv(mode, client):
    response = client.post(
        f"/api/{mode}/v1alpha1/documents",
        data=V1_3.DocumentList(documents=[signed_doc], count=1).model_dump_json(),
        content_type="application/json",
        headers={
            "X-TEST-SSL-VERIFY": "True",
            "X-TEST-SSL-FINGERPRINT": "VALID",
        },
    )

    assert response.status_code == 200
    assert response.data == b'["OK"]\n'

    response = client.post(
        "/internal/messagesStatus",
        data=MessagesStatusRequest(
            requestsIds=[uuid.UUID("a4963c1f-f2be-4e3c-9a3a-0d2627aaf9bc")]
        ).model_dump_json(),
        content_type="application/json",
        headers={
            "X-TEST-SSL-VERIFY": "True",
            "X-TEST-SSL-FINGERPRINT": "VALID",
        },
    )

    expected_messages_status_response = load_model(
        "tests/data/signed_messages_status_response.json", MessagesStatusResponse
    )

    assert response.status_code == 200
    assert (
        MessagesStatusResponse.model_validate_json(response.data)
        == expected_messages_status_response
    )


# @pytest.mark.parametrize("mode", ["backend"])
# def test_backend(
#     mode,
#     client,
# ):
#     fb_plugin = current_oso_plugin_app()
#     assert isinstance(fb_plugin, FBPlugin)

#     # keys = fb_plugin.signing_server.list_keys(key_type=KeyType.SECP256K1)

#     response = client.post(
#         f"/api/{mode}/v1alpha1/documents",
#         data=V1_3.DocumentList(documents=[unsigned_doc], count=1).model_dump_json(),
#         content_type="application/json",
#         headers={
#             "X-TEST-SSL-VERIFY": "True",
#             "X-TEST-SSL-FINGERPRINT": "VALID",
#         },
#     )

#     assert response.status_code == 200
#     assert response.data == b'["OK"]\n'

#     response = client.get(
#         f"/api/{mode}/v1alpha1/documents",
#         headers={
#             "X-TEST-SSL-VERIFY": "True",
#             "X-TEST-SSL-FINGERPRINT": "VALID",
#         },
#     )

#     assert response.status_code == 200
#     assert V1_3.DocumentList.model_validate_json(response.data) == V1_3.DocumentList(
#         documents=[signed_doc], count=1
#     )


@pytest.mark.parametrize("mode", ["frontend"])
def test_frontend_status(mode, client):
    response = client.get(
        f"/api/{mode}/v1alpha1/status",
        headers={
            "X-TEST-SSL-VERIFY": "True",
            "X-TEST-SSL-FINGERPRINT": "VALID",
        },
    )

    assert response.status_code == 200
    assert V1_3.ComponentStatus.model_validate_json(
        response.data
    ) == V1_3.ComponentStatus(status_code=200, status="OK")


@pytest.mark.parametrize("mode", ["backend"])
def test_backend_status(mode, client):
    with requests_mock.Mocker() as mock:
        mock.get(f"{get_signing_api_endpoint()}/status", text="OK")

        response = client.get(
            f"/api/{mode}/v1alpha1/status",
            headers={
                "X-TEST-SSL-VERIFY": "True",
                "X-TEST-SSL-FINGERPRINT": "VALID",
            },
        )

    assert response.status_code == 200
    assert V1_3.ComponentStatus.model_validate_json(
        response.data
    ) == V1_3.ComponentStatus(status_code=200, status="OK")
