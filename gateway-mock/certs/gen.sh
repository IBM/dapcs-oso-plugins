#!/bin/bash
#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

ci_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)

pushd "$ci_root" || exit

# CA
openssl genrsa -out gatewayca-key.pem 4096
openssl req -config ca.cnf -key gatewayca-key.pem -new -out gatewayca-req.csr
openssl x509 -signkey gatewayca-key.pem -in gatewayca-req.csr -req -days 365 -out gatewayca.pem

# Server
openssl genrsa -out gatewayserver-key.pem 4096
openssl req -config server.cnf -key gatewayserver-key.pem -new -out gatewayserver-req.csr
openssl x509 -in gatewayserver-req.csr -req -days 365 -CA gatewayca.pem -CAkey gatewayca-key.pem -CAcreateserial -extfile server.cnf -extensions gatewayserver -out gatewayserver.pem

# Client
openssl req -config client.cnf -newkey rsa:4096 -nodes -keyout gatewayclient-key.pem -new -out gatewayclient.csr
openssl x509 -req -in gatewayclient.csr -days 7300 -CA gatewayca.pem -CAkey gatewayca-key.pem -CAcreateserial -out gatewayclient.pem

popd || exit
