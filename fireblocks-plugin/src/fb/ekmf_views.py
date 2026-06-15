#
# (c) Copyright IBM Corp. 2026
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
#
"""Frontend EKMF key import API served at /api/ekmf/import/*.

Authenticated by the approver client certificate: the proxy verifies it against
``CERTS__CLIENT_CA_EXTRA`` and the views check the fingerprint against
``FB__EKMF_APPROVER_FINGERPRINTS``.
"""

import base64
import logging
import sys
import uuid

from flask import g, jsonify, request
from flask.views import MethodView

from pydantic import BaseModel, ValidationError

from oso.framework.auth.common import EXT_NAME as AUTH_EXT_NAME
from oso.framework.auth.mtls import NAME as MTLS_NAME
from oso.framework.plugin import current_oso_plugin, current_oso_plugin_app

from .ekmf import EkmfAddonError, EkmfStateError
from .ekmf import state as ekmf_state
from .ekmf.schemas import (
    DocumentType,
    EkmfPayloadContent,
    ImportResultDocument,
    WrappingKeyDocument,
)

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger(__name__)


class InitResponse(BaseModel):
    status: str
    import_id: str
    message: str


class PayloadRequest(BaseModel):
    transport_key: str
    payload: str


class StatusResponse(BaseModel):
    status: str
    import_id: str | None
    message: str


def _error_response(error: str, status_code: int, message: str, details=None):
    body = {"error": error, "message": message}
    if details is not None:
        body["details"] = details
    return jsonify(body), status_code


def _load_fingerprint(fingerprint: str) -> bytes:
    """Decode an OpenSSH-format SHA256 fingerprint, with or without padding."""
    encoded = fingerprint.removeprefix("SHA256:")
    return base64.b64decode(encoded + "=" * (-len(encoded) % 4))


def _require_approver():
    allowlist = current_oso_plugin_app().config.ekmf_approver_fingerprints.split()

    if not allowlist:
        return _error_response(
            "forbidden",
            403,
            "no EKMF approver fingerprints are configured",
        )

    try:
        mtls_result = getattr(g, AUTH_EXT_NAME)[MTLS_NAME]
    except (AttributeError, KeyError):
        return _error_response("unauthorized", 401, "no authentication context")

    if mtls_result.get("authorized") is not True:
        return _error_response("unauthorized", 401, "client certificate not verified")

    if mtls_result.get("fingerprint") not in [
        _load_fingerprint(fingerprint) for fingerprint in allowlist
    ]:
        return _error_response(
            "forbidden",
            403,
            "client certificate not authorized for EKMF import",
        )

    return None


def _check_access():
    if current_oso_plugin().config.mode != "frontend":
        return _error_response(
            "not_found",
            404,
            "EKMF import endpoints are only available in frontend mode",
        )
    return _require_approver()


class EkmfImportInitApi(MethodView):
    def post(self):
        if (error := _check_access()) is not None:
            return error

        plugin = current_oso_plugin_app()

        import_id = f"ekmf-import-{uuid.uuid4().hex[:8]}"
        try:
            plugin.ekmf_state.start_import(import_id)
        except EkmfStateError as exc:
            return _error_response("conflict", 409, str(exc))

        try:
            init_doc = plugin.ekmf_client.init_import()
        except EkmfAddonError as exc:
            plugin.ekmf_state.reset()
            logger.error(
                f"ekmf addon /init failed status={exc.status_code} body={exc.body}"
            )
            return _error_response(
                "addon_unavailable",
                502,
                "EKMF Add-On did not accept the init request",
            )

        plugin.ekmf_state.enqueue_outbound(init_doc.model_dump(mode="json"))

        logger.info(f"ekmf import initiated import_id={import_id}")

        return (
            jsonify(
                InitResponse(
                    status=ekmf_state.STATUS_KEYGEN_PENDING,
                    import_id=import_id,
                    message=(
                        "EKMF import sequence initialized; awaiting backend keygen."
                    ),
                ).model_dump(mode="json")
            ),
            202,
        )


class EkmfImportKeyApi(MethodView):
    def get(self):
        if (error := _check_access()) is not None:
            return error

        plugin = current_oso_plugin_app()

        if plugin.ekmf_state.status == ekmf_state.STATUS_IDLE:
            return _error_response(
                "conflict",
                409,
                "no active EKMF import sequence",
            )

        cached = plugin.ekmf_state.get_cached(DocumentType.WRAPPING_KEY)
        if cached is None:
            return _error_response(
                "not_found",
                404,
                "transport wrapping key not yet available",
                details={"current_status": plugin.ekmf_state.status},
            )

        try:
            wk_doc = WrappingKeyDocument.model_validate(cached)
            content = plugin.ekmf_client.extract_key(wk_doc)
        except EkmfAddonError as exc:
            logger.error(
                f"ekmf addon /key failed status={exc.status_code} body={exc.body}"
            )
            return _error_response(
                "addon_unavailable",
                502,
                "EKMF Add-On failed to extract key",
            )

        return jsonify(content.model_dump(mode="json")), 200


class EkmfImportPayloadApi(MethodView):
    def post(self):
        if (error := _check_access()) is not None:
            return error

        plugin = current_oso_plugin_app()

        if plugin.ekmf_state.status != ekmf_state.STATUS_KEY_AVAILABLE:
            return _error_response(
                "conflict",
                409,
                f"payload submission not allowed in state "
                f"'{plugin.ekmf_state.status}'; retrieve transport key first",
            )

        body = request.get_json(silent=True)
        if body is None:
            return _error_response(
                "validation_failed",
                422,
                "JSON body required",
            )

        try:
            req = PayloadRequest.model_validate(body)
        except ValidationError as exc:
            return _error_response("validation_failed", 422, str(exc))

        cached_wk = plugin.ekmf_state.get_cached(DocumentType.WRAPPING_KEY)
        if cached_wk is None:
            return _error_response("conflict", 409, "wrapping key not available")

        wk_doc = WrappingKeyDocument.model_validate(cached_wk)
        try:
            payload_content = EkmfPayloadContent(
                wrapping_key_id=wk_doc.content.key_id,
                transport_key=req.transport_key,
                payload=req.payload,
            )
        except ValidationError as exc:
            return _error_response("validation_failed", 422, str(exc))

        try:
            payload_doc = plugin.ekmf_client.package_payload(payload_content)
        except EkmfAddonError as exc:
            logger.error(
                f"ekmf addon /payload failed status={exc.status_code} body={exc.body}"
            )
            return _error_response(
                "addon_unavailable",
                502,
                "EKMF Add-On did not accept the payload",
            )

        plugin.ekmf_state.enqueue_outbound(payload_doc.model_dump(mode="json"))
        plugin.ekmf_state.transition(ekmf_state.STATUS_PAYLOAD_SUBMITTED)

        logger.info(f"ekmf payload submitted import_id={plugin.ekmf_state.import_id}")

        return jsonify(payload_doc.model_dump(mode="json")), 200


class EkmfImportResultApi(MethodView):
    def get(self):
        if (error := _check_access()) is not None:
            return error

        plugin = current_oso_plugin_app()

        if plugin.ekmf_state.status == ekmf_state.STATUS_IDLE:
            return _error_response(
                "conflict",
                409,
                "no active EKMF import sequence",
            )

        cached = plugin.ekmf_state.get_cached(DocumentType.IMPORT_RESULT)
        if cached is None:
            return (
                jsonify(
                    StatusResponse(
                        status=plugin.ekmf_state.status,
                        import_id=plugin.ekmf_state.import_id,
                        message="backend import processing in progress",
                    ).model_dump(mode="json")
                ),
                202,
            )

        try:
            result_doc = ImportResultDocument.model_validate(cached)
            content = plugin.ekmf_client.extract_result(result_doc)
        except EkmfAddonError as exc:
            logger.error(
                f"ekmf addon /result failed status={exc.status_code} body={exc.body}"
            )
            return _error_response(
                "addon_unavailable",
                502,
                "EKMF Add-On failed to extract result",
            )

        return jsonify(content.model_dump(mode="json")), 200
