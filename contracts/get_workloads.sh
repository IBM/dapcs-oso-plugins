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

HIPERSOCKET34="${HIPERSOCKET34:-true}"

FRONTEND_PLUGIN_FILE="./output/frontend/frontend.yml"
if [ ! -f $FRONTEND_PLUGIN_FILE ]; then
  echo "frontend plugin file does not exist: $FRONTEND_PLUGIN_FILE"
  exit 1
fi
FRONTEND_PLUGIN=$(cat "$FRONTEND_PLUGIN_FILE")

BACKEND_FILE="./output/backend/user-data"
if [ ! -f $BACKEND_FILE ]; then
  echo "backend file does not exist: $BACKEND_FILE"
  exit 1
fi
BACKEND=$(cat "$BACKEND_FILE")

cat <<-EOT
# Hyper Protect Encrypted Workloads
FRONTEND_WORKLOADS=[
  {
    persistent_vol: null,
    name: "frontend-plugin",
    workload: "$FRONTEND_PLUGIN"
  }
]

BACKEND_WORKLOADS=[
  {
    name: "backend-plugin",
    hipersocket34: $HIPERSOCKET34,
    workload: "$BACKEND",
    persistent_vol: {
      volume_name = "vault_vol",
      env_seed = "vaultseed2",
      prev_seed = "",
      volume_path = "/var/lib/libvirt/images/oso/fb-vault-data.qcow2"
    }
  }
]
EOT
