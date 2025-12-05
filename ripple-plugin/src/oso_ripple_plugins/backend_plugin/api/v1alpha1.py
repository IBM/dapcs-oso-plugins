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


import logging
import sys

from flask import abort, current_app, request
from flask_restx import Namespace, Resource, fields

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

api = Namespace("v1alpha1", description="")

content_model = api.model(
    "Ripple_Document_Content",
    {
        "vaultId": fields.String(),
        "transactions": fields.List(fields.String()),
        "accounts": fields.List(fields.String()),
        "manifests": fields.List(fields.String()),
    },
)


document_model = api.model(
    "Document",
    {
        "id": fields.String(),
        "content": fields.Nested(content_model),
        "signature": fields.String(),
    },
)

documents_model = api.model(
    "Documents",
    {
        "documents": fields.List(fields.Nested(document_model)),
        "count": fields.Integer(),
    },
)


@api.route("/documents", methods=["POST"])
class Upload(Resource):
    @api.doc(
        summary="Upload a batch of confirmed documents",
        description=(
            "This endpoint enables the offline signing coductor's input bridge"
            " service to upload multiple signed documents to the backend"
        ),
        operationId="backendBatchUpload",
        body=documents_model,
    )
    @api.response(code=204, description="Success")
    @api.response(code=500, description="Internal Server Error")
    def post(self):
        try:
            json_data = request.get_json(force=True)
            documents = json_data.get("documents")
            if documents is None:
                raise Exception("Request json key 'documents' not found")
        except Exception as e:
            logger.exception(e)
            return abort(400)

        try:
            logger.info(f"Processing {len(documents)} documents for upload")
            if len(documents) > 0:
                current_app.bpm.bulk_upload(documents)
        except Exception as e:
            logger.exception(e)
            abort(500)

        return "OK", 204


@api.route("/documents", methods=["GET"])
class Download(Resource):
    @api.doc(
        summary="Download a batch of signed documents",
        description="GET",
        operationId="backendBatchDownload",
        model=documents_model,
    )
    @api.response(code=200, description="Success", model=documents_model)
    @api.response(code=500, description="Internal Server Error")
    def get(self):
        try:
            documents = current_app.bpm.bulk_download()
        except Exception as e:
            logger.exception(e)
            abort(500)

        return {"documents": documents, "count": len(documents)}


@api.route("/status", methods=["GET"])
class Status(Resource):
    component_status_model = api.model(
        "ComponentStatus", {"status": fields.String(), "error": fields.String()}
    )

    @api.response(code=200, description="Success", model=component_status_model)
    @api.response(code=503, description="Unavailable", model=component_status_model)
    def get(self):
        try:
            current_app.bpm.backend_status()
        except Exception as e:
            logger.exception(e)
            abort(503)

        return {"status": "OK"}, 200
