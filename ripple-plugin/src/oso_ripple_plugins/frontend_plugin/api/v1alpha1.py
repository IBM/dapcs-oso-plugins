#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

import logging
import sys

from flask import abort, current_app, request
from flask_restx import Namespace, Resource, fields

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

api = Namespace("v1alpha1", description="")

document_model = api.model(
    "Document",
    {"id": fields.String(), "content": fields.String(), "signature": fields.String()},
)

documents_model = api.model(
    "Documents",
    {
        "documents": fields.List(fields.Nested(document_model)),
        "count": fields.Integer(),
    },
)

component_status_model = api.model(
    "ComponentStatus", {"status": fields.String(), "error": fields.String()}
)


@api.route("/documents", methods=["GET"])
class Download(Resource):
    @api.doc(
        summary="Get prepared documents",
        description="This API downloads documents from frontend.",
        operationId="pluginGetPrepared",
    )
    @api.response(code=200, description="Success")
    @api.response(code=500, description="Internal Server Error")
    def get(self):
        try:
            documents = current_app.fpm.bulk_download()
        except Exception as e:
            logger.exception(e)
            abort(500)

        return {"documents": documents, "count": len(documents)}


@api.route("/documents", methods=["POST"])
class Upload(Resource):
    @api.doc(
        summary="Post signed documents",
        description="This API uploads documents to frontend.",
        operationId="pluginPostSigned",
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
                current_app.fpm.bulk_upload(documents)
        except Exception as e:
            logger.exception(e)
            abort(500)

        return "OK", 204


@api.route("/status", methods=["GET"])
class Status(Resource):
   # Define the error model
    error_model = api.model(
        "Error",
        {
            "code": fields.String(description="Error code"),
            "message": fields.String(description="Error message")
        }
    )

    # Define the component status model
    component_status_model = api.model(
        "ComponentStatus",
        {
            "status_code": fields.Integer(description="HTTP status code"),
            "status": fields.String(description="Human readable message"),
            "errors": fields.List(fields.Nested(error_model), default=[], description="List of errors")
        }
    )

    @api.response(code=200, description="Success", model=component_status_model)
    @api.response(code=503, description="Unavailable", model=component_status_model)
    def get(self):
        """Return the component status"""
        try:
            # Capture backend status if needed
            backend_result = current_app.fpm.backend_status()
        except Exception as e:
            logger.exception("Backend status check failed")
            return {
                "status_code": 503,
                "status": "Unavailable",
                "errors": [{"code": "BACKEND_ERROR", "message": str(e)}]
            }, 503

        # Return a successful status
        return {
            "status_code": 200,
            "status": "OK",
            "errors": []
        }, 200