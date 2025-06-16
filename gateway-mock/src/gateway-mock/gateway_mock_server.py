from flask import Flask, request

from fbserverapimock import FBServerAPIMock

app = Flask(__name__)

gateway_mock = FBServerAPIMock()


@app.route("/pair_device")
def pair_device():
    return ""


@app.route("/access_token", methods=["POST"])
def access_token():
    return gateway_mock.getAccessToken()


@app.route("/msg", methods=["GET", "PUT"])
def msg():
    if request.method == "GET":
        use_batch = request.args.get("useBatch", default="false", type=str)

        if use_batch:
            return gateway_mock.getBatchMessages()
        else:
            return gateway_mock.getMessages()
    elif request.method == "PUT":
        return gateway_mock.ackMessage(request.json)


# KEY_LINK_PROOF_OF_OWNERSHIP_RESPONSE: 'keylink_proof_of_ownership_response',
# KEY_LINK_TX_SIGN_RESPONSE: 'keylink_tx_sign_response',
@app.route("/keylink_proof_of_ownership_response")
def proof_of_ownership():
    return None


@app.route("/keylink_tx_sign_response")
def sign_res():
    return None


@app.route("/get_service_certificates")
def get_service_certificates():
    return gateway_mock.getCertificates()


@app.route("/keylink_proof_of_ownership_response", methods=["POST"])
def broadcastResponse1():
    return gateway_mock.broadcastResponse(
        "/keylink_proof_of_ownership_response", request.json
    )


@app.route("/keylink_tx_sign_response", methods=["POST"])
def broadcastResponse2():
    return gateway_mock.broadcastResponse("keylink_tx_sign_response", request.json)
