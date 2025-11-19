#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2025
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

resource "local_file" "frontend_podman_play" {
  content = templatefile(
    "${path.module}/frontend.yml.tftpl",
    { tpl = {
      plugin_image = var.FRONTEND_PLUGIN_IMAGE,
      hsmdriver_image = var.HSMDRIVER_IMAGE,
      proxy_address = var.PROXY_ADDRESS,
    } },
  )
  filename = "frontend/podman-play.yml"
  file_permission = "0664"
}

# archive of the folder containing podman play file. This folder could create additional resources such as files
# to be mounted into containers, environment files etc. This is why all of these files get bundled in a tgz file (base64 encoded)
resource "hpcr_tgz" "frontend_workload" {
  depends_on = [ local_file.frontend_podman_play ]
  folder = "${path.module}/frontend"
}

locals {
  frontend_play = {
    "play" : {
      "archive" : hpcr_tgz.frontend_workload.rendered
    }
  }
  frontend_workload = merge(local.workload_template, local.frontend_play)
}

# In this step we encrypt the fields of the contract and sign the env and workload field. The certificate to execute the
# encryption it built into the provider and matches the latest HPCR image. If required it can be overridden.
# We use a temporary, random keypair to execute the signature. This could also be overriden.
resource "hpcr_text_encrypted" "frontend_contract" {
  text      = yamlencode(local.frontend_workload)
  cert      = var.HPCR_CERT == "" ? null : var.HPCR_CERT
}

resource "local_file" "frontend_contract" {
  count    = var.DEBUG ? 1 : 0
  content  = yamlencode(local.frontend_workload)
  filename = "frontend_contract.yml"
  file_permission = "0664"
}

resource "local_file" "frontend_contract_encrypted" {
  content  = hpcr_text_encrypted.frontend_contract.rendered
  filename = "frontend.yml"
  file_permission = "0664"
}
