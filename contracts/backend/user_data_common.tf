#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2025
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

locals {
  workload_template = {
    "type" : "workload",
    "images": {},
    "volumes": {
        "vault_vol": {
            "filesystem": "ext4",
            "mount": "/data",
            "seed": var.WORKLOAD_VOL_SEED,
        }
    }
  }
}
