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
      min_keys = var.MIN_KEYS
      enable_ep11server = var.INTERNAL_GREP11,
      grep11_image = var.GREP11_IMAGE,
      grep11_endpoint = var.INTERNAL_GREP11 ? "localhost:9876" : local.grep11_endpoint,
      grep11_client_cert = base64encode(var.INTERNAL_GREP11 ? tls_locally_signed_cert.client_cert.cert_pem : var.GREP11_CLIENT_CERT),
      grep11_client_key = base64encode(var.INTERNAL_GREP11 ? tls_private_key.client_key.private_key_pem_pkcs8 : var.GREP11_CLIENT_KEY),
      grep11_ca = base64encode(var.INTERNAL_GREP11 ? tls_self_signed_cert.grep11_ca_cert.cert_pem : var.GREP11_CA),
    } },
  )
  filename        = "backend/podman-play.yml"
  file_permission = "0664"

  depends_on = [
    local_file.grep11_cfg,
    local_file.grep11_ca_cert,
    local_file.grep11_server_key,
    local_file.grep11_server_cert,
    local_file.c16_client_cfg,
    local_file.c16_ca_cert,
    local_file.c16_client_cert,
    local_file.c16_client_key
  ]
}

# archive of the folder containing podman play file. This folder could create additional resources such as files
# to be mounted into containers, environment files etc. This is why all of these files get bundled in a tgz file (base64 encoded)
resource "hpcr_tgz" "backend_workload" {
  depends_on = [local_file.backend_podman_play]
  folder     = "${path.module}/backend"
}

locals {
  grep11_endpoint = var.GREP11_ENDPOINT != null ? var.GREP11_ENDPOINT : format("%s-cs-backend-grep11.control23.dap.local:9876", var.PREFIX)
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

resource "local_file" "grep11_cfg" {
  count = var.INTERNAL_GREP11 ? 1 : 0
  content = local.grep11_cfg
  filename = "${path.module}/backend/srv1/grep11server.yaml"
  file_permission = "0664"
}

resource "local_file" "grep11_ca_cert" {
  count = var.INTERNAL_GREP11 ? 1 : 0
  content = tls_self_signed_cert.grep11_ca_cert.cert_pem
  filename = "${path.module}/backend/srv1/grep11ca.pem"
  file_permission = "0664"
}

resource "local_file" "grep11_server_key" {
  count = var.INTERNAL_GREP11 ? 1 : 0
  content = tls_private_key.server_key.private_key_pem
  filename = "${path.module}/backend/srv1/grep11server-key.pem"
  file_permission = "0664"
}

resource "local_file" "grep11_server_cert" {
  count = var.INTERNAL_GREP11 ? 1 : 0
  content = tls_locally_signed_cert.server_cert.cert_pem
  filename = "${path.module}/backend/srv1/grep11server.pem"
  file_permission = "0664"
}

resource "local_file" "c16_client_cfg" {
  count = var.INTERNAL_GREP11 ? 1 : 0
  content = local.c16_cfg
  filename = "${path.module}/backend/cfg/c16client.yaml"
  file_permission = "0664"
}

resource "local_file" "c16_ca_cert" {
  count = var.INTERNAL_GREP11 ? 1 : 0
  content = var.C16_CA_CERT
  filename = "${path.module}/backend/cfg/ca.pem"
  file_permission = "0664"
}

resource "local_file" "c16_client_cert" {
  count = var.INTERNAL_GREP11 ? 1 : 0
  content = var.C16_CLIENT_CERT
  filename = "${path.module}/backend/cfg/c16client.pem"
  file_permission = "0664"
}

resource "local_file" "c16_client_key" {
  count = var.INTERNAL_GREP11 ? 1 : 0
  content = var.C16_CLIENT_KEY
  filename = "${path.module}/backend/cfg/c16client-key.pem"
  file_permission = "0664"
}

locals {
  c16_cfg = <<-EOT
    loglevel: ${var.C16_CLIENT_LOGLEVEL}
    servers:
      - hostname: ${var.C16_CLIENT_HOST}
        port: ${var.C16_CLIENT_PORT}
        mTLS: true
        server_cert_file: "/etc/c16/ca.pem"
        client_key_file: "/etc/c16/c16client-key.pem"
        client_cert_file: "/etc/c16/c16client.pem"
  EOT
  grep11_cfg = <<-EOT
    logging:
      levels:
        entry: debug
    ep11crypto:
      enabled: true
      connection:
        address: 0.0.0.0
        port: 9876
        tls:
          enabled: true
          certfile: /cfg/grep11server.pem
          keyfile: /cfg/grep11server-key.pem
          mutual: true
          cacert: /cfg/grep11ca.pem
          cacertbytes:
          certfilebytes:
          keyfilebytes:
        keepalive:
          serverKeepaliveTime: 30
          serverKeepaliveTimeout: 5
      domain: "${var.DOMAIN}"
  EOT
}
