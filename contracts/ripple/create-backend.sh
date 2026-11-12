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

umask 077

. ./common.sh
exportTF || builtin exit $?
exportCP || builtin exit $?

contract_root=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

pushd "$contract_root" || exit 1

pushd backend || exit 1
# Always remove secret-bearing intermediate files and Terraform state, even if apply fails or the script is interrupted.
b="${contract_root}/backend"
trap 'rm -f "${b}/podman-play/cert/client-key.pem" \
            "${b}/podman-play/srv1/grep11server-key.pem" \
            "${b}/podman-play/cfg/c16client-key.pem" \
            "${b}/podman-play/play.yml" \
            "${b}/backend_plain.yml" \
            "${b}/terraform.tfstate" "${b}/terraform.tfstate.backup"' EXIT
# shellcheck disable=SC2154
${tf} init && ${tf} destroy -auto-approve && ${tf} apply -auto-approve
${CP} -rf backend.yml ../output/backend/user-data
chmod 600 ../output/backend/user-data
popd || exit 1

popd || exit 1
