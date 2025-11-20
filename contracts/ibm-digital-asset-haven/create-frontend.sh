#!/bin/bash
#
# (c) Copyright IBM Corp. 2025
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

. ./common.sh
exportTF || builtin exit $?
exportCP || builtin exit $?

contract_root=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

pushd "$contract_root" || exit 1

pushd frontend || exit 1
# shellcheck disable=SC2154
${tf} init && ${tf} destroy -auto-approve && ${tf} apply -auto-approve
${CP} -rf frontend.yml ../output/frontend
popd || exit 1

popd || exit 1

FRONTEND_PLUGIN_FILE="./frontend/frontend.yml"
if [ ! -f $FRONTEND_PLUGIN_FILE ]; then
  echo "frontend encrypted workload contract file does not exist: $FRONTEND_PLUGIN_FILE"
  exit 1
fi
FRONTEND_PLUGIN=$(cat "$FRONTEND_PLUGIN_FILE")

cat <<-EOT
FRONTEND_WORKLOADS=[
  {
    persistent_vol: null,
    name: "frontend-plugin",
    workload: "$FRONTEND_PLUGIN"
  }
]
EOT
