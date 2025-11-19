#!/bin/bash
#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2025
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

. ./common.sh
exportTF || builtin exit $?
exportCP || builtin exit $?

contract_root=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

pushd "$contract_root" || exit 1

pushd backend || exit 1
# shellcheck disable=SC2154
${tf} init && ${tf} destroy -auto-approve && ${tf} apply -auto-approve
${CP} -rf backend.yml ../output/backend/user-data
popd || exit 1

popd || exit 1

BACKEND_FILE="./backend/backend.yml"
if [ ! -f $BACKEND_FILE ]; then
  echo "backend file does not exist: $BACKEND_FILE"
  exit 1
fi
BACKEND=$(cat "$BACKEND_FILE")

HIPERSOCKET34="${HIPERSOCKET34:-false}"

cat <<-EOT
BACKEND_WORKLOADS=[
  {
    name: "backend-plugin",
    hipersocket34: $HIPERSOCKET34,
    workload: "$BACKEND",
    persistent_vol: {
      volume_name = "backend_vol",
      env_seed = "TODO-change-this_seed",
      prev_seed = "",
      volume_path = "/var/lib/libvirt/images/oso/hsm-signer-db.qcow2"
    }
  }
]
EOT
