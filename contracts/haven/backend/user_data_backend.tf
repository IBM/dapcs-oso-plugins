#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2025
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

resource "local_file" "backend_podman_play" {
  content = templatefile(
    "${path.module}/backend.yml.tftpl",
    { tpl = {
      plugin_image = var.BACKEND_PLUGIN_IMAGE,
      hsmdriver_image = var.HSMDRIVER_IMAGE,
      user_pin = var.USER_PIN,
      so_pin = var.SO_PIN,
    } },
  )
  filename = "backend/podman-play.yml"
  file_permission = "0664"
}

# archive of the folder containing podman play file. This folder could create additional resources such as files
# to be mounted into containers, environment files etc. This is why all of these files get bundled in a tgz file (base64 encoded)
resource "hpcr_tgz" "backend_workload" {
  depends_on = [local_file.backend_podman_play]
  folder = "${path.module}/backend"
}

locals {
  backend_play = {
    "play" : {
      "archive" : hpcr_tgz.backend_workload.rendered
    }
  }
  backend_workload = merge(local.workload_template, local.backend_play)
}

# In this step we encrypt the fields of the contract and sign the env and workload field. The certificate to execute the
# encryption it built into the provider and matches the latest HPCR image. If required it can be overridden.
# We use a temporary, random keypair to execute the signature. This could also be overriden.
resource "hpcr_text_encrypted" "backend_contract" {
  text = yamlencode(local.backend_workload)
  cert = var.HPCR_CERT == "" ? null : var.HPCR_CERT
}

resource "local_file" "backend_contract" {
  count    = var.DEBUG ? 1 : 0
  content  = yamlencode(local.backend_workload)
  filename = "${path.module}/backend_plain.yml"
  file_permission = "0664"
}

resource "local_file" "backend_contract_encrypted" {
  content  = hpcr_text_encrypted.backend_contract.rendered
  filename = "${path.module}/backend.yml"
  file_permission = "0664"
}

