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
#

cp -r /oso-root/"${COMPONENT}"/*    /app-root

if [ "${DEBUG}" == "true" ]; then
	echo "${SSH_PUBKEY}" >"${HOME}/.ssh/authorized_keys"
        sed -ie 's/#Port 22/Port '"$SSH_PORT"'/g' /etc/ssh/sshd_config
else
	export DEBUG="false"
fi

umask 0007
/app-root/entrypoints/entrypoint.sh
