#!/bin/bash
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


mkdir -p /app-root/all-certs

# Write certs to file
echo "${COMPONENT_CA_CERT}" >/app-root/all-certs/component-ca-cert.pem
echo "${FRONTEND_CERT}" >/app-root/all-certs/frontend-certificate.pem
echo "${FRONTEND_KEY}" >/app-root/all-certs/frontend-key.pem

export COMPONENT_FINGERPRINTS="${CONFIRMATION_FINGERPRINT}"

unset CONF_FILE
CONF_FILE=/app-root/entrypoints/supervisord-frontend_plugin.conf

cd /app-root/entrypoints || exit

SUPERVISORD_CONF=/usr/local/etc/supervisord.conf
cp ${CONF_FILE} ${SUPERVISORD_CONF}
supervisord -c ${SUPERVISORD_CONF}
