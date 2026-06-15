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



resource "local_file" "backend_podman_play" {
  content = templatefile(
    "${path.module}/backend.yml.tftpl",
    { tpl = {
      plugin_image       = var.BACKEND_PLUGIN_IMAGE,
      ekmf_addon_image   = var.BACKEND_EKMF_ADDON_IMAGE,
      ekmf_addon_port    = var.EKMF_ADDON_PORT,
      enable_ep11server  = var.INTERNAL_GREP11,
      crypto_pass_enable = var.CRYPTO_PASSTHROUGH_ENABLEMENT,
      grep11_image       = var.GREP11_IMAGE,
    } },
  )
  filename        = "backend/podman-play.yml"
  file_permission = "0664"

  depends_on = [
    local_file.grep11_cfg,
    null_resource.crypto_deps
  ]
}

resource "null_resource" "crypto_deps" {
  count = var.CRYPTO_PASSTHROUGH_ENABLEMENT ? 0 : 1

  depends_on = [
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
  count           = var.DEBUG ? 1 : 0
  content         = yamlencode(local.backend_workload)
  filename        = "${path.module}/backend_plain.yml"
  file_permission = "0664"
}

resource "local_file" "backend_contract_encrypted" {
  content         = hpcr_text_encrypted.backend_contract.rendered
  filename        = "${path.module}/backend.yml"
  file_permission = "0664"
}

resource "local_file" "grep11_cfg" {
  count           = var.INTERNAL_GREP11 ? 1 : 0
  content         = local.grep11_cfg
  filename        = "${path.module}/backend/srv1/grep11server.yaml"
  file_permission = "0664"
}

resource "local_file" "c16_client_cfg" {
  count           = (var.INTERNAL_GREP11 && !var.CRYPTO_PASSTHROUGH_ENABLEMENT) ? 1 : 0
  content         = local.c16_cfg
  filename        = "${path.module}/backend/cfg/c16client.yaml"
  file_permission = "0664"
}

resource "local_file" "c16_ca_cert" {
  count           = (var.INTERNAL_GREP11 && !var.CRYPTO_PASSTHROUGH_ENABLEMENT) ? 1 : 0
  content         = var.C16_CA_CERT
  filename        = "${path.module}/backend/cfg/ca.pem"
  file_permission = "0664"
}

resource "local_file" "c16_client_cert" {
  count           = (var.INTERNAL_GREP11 && !var.CRYPTO_PASSTHROUGH_ENABLEMENT) ? 1 : 0
  content         = var.C16_CLIENT_CERT
  filename        = "${path.module}/backend/cfg/c16client.pem"
  file_permission = "0664"
}

resource "local_file" "c16_client_key" {
  count           = (var.INTERNAL_GREP11 && !var.CRYPTO_PASSTHROUGH_ENABLEMENT) ? 1 : 0
  content         = var.C16_CLIENT_KEY
  filename        = "${path.module}/backend/cfg/c16client-key.pem"
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
  # TLS is disabled because GREP11 is only reachable over localhost within
  # the backend pod (plugin and EKMF addon connect over plain gRPC).
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
          enabled: false
        keepalive:
          serverKeepaliveTime: 30
          serverKeepaliveTimeout: 5
      domain: "${var.DOMAIN}"
  EOT
}
