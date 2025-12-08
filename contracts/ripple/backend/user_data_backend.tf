// Copyright (c) 2025 IBM Corp.
// All rights reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

resource "local_file" "ibm_cfg" {
  content = local.ibm_cfg
  filename = "docker-compose/ibm.cfg"
  file_permission = "0664"
}

resource "local_file" "grep_ca" {
  content = var.INTERNAL_GREP11 ? tls_self_signed_cert.grep11_ca_cert.cert_pem : var.GREP11_CA
  filename = "docker-compose/cert/ca.pem"
  file_permission = "0664"
}

resource "local_file" "grep_client_key" {
  content = var.INTERNAL_GREP11 ? tls_private_key.client_key.private_key_pem_pkcs8 : var.GREP11_CLIENT_KEY
  filename = "docker-compose/cert/client-key.pem"
  file_permission = "0664"
}

resource "local_file" "grep_client_cert" {
  content = var.INTERNAL_GREP11 ? tls_locally_signed_cert.client_cert.cert_pem : var.GREP11_CLIENT_CERT
  filename = "docker-compose/cert/client.pem"
  file_permission = "0664"
}


resource "local_file" "docker_compose" {
  content = templatefile(
    "${path.module}/backend.yml.tftpl",
    { tpl = {
      backend_plugin_image = var.BACKEND_PLUGIN_IMAGE,
      cold_bridge_image = var.COLD_BRIDGE_IMAGE,
      cold_vault_image = var.COLD_VAULT_IMAGE,
      kmsconnect_image = var.KMSCONNECT_IMAGE,
      vault_id = var.VAULT_ID,
      passphrase = var.PASSPHRASE,
      notary_messaging_public_key = var.NOTARY_MESSAGING_PUBLIC_KEY,
      seed = var.SEED,
      enable_ep11server = var.INTERNAL_GREP11,
      crypto_pass_enable = var.CRYPTO_PASSTHROUGH_ENABLEMENT,
      grep11_image = var.GREP11_IMAGE,
    } },
  )
  filename = "docker-compose/docker-compose.yml"
  file_permission = "0664"

  depends_on = [
    local_file.ibm_cfg,
    local_file.grep_ca,
    local_file.grep_client_key,
    local_file.grep_client_cert,
    local_file.grep11_server_key,
    local_file.grep11_server_cert,
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

# archive of the folder containing docker-compose file. This folder could create additional resources such as files
# to be mounted into containers, environment files etc. This is why all of these files get bundled in a tgz file (base64 encoded)
resource "hpcr_tgz" "workload" {
  depends_on = [ local_file.docker_compose ]
  folder = "docker-compose"
}

locals {
  grep11_endpoint = var.STATIC_IP ? var.GREP11_ENDPOINT: format("%s-cs-backend-grep11.control23.dap.local:9876", var.PREFIX)
  ibm_cfg = <<-EOT
    system = onprem
    endpoint = ${var.INTERNAL_GREP11 ? "ep11server:9876" : local.grep11_endpoint}
  EOT
  compose = {
    "compose" : {
      "archive" : hpcr_tgz.workload.rendered
    }
  }
  workload = merge(local.workload_template, local.compose)
}

# In this step we encrypt the fields of the contract and sign the env and workload field. The certificate to execute the
# encryption it built into the provider and matches the latest HPCR image. If required it can be overridden.
# We use a temporary, random keypair to execute the signature. This could also be overriden.
resource "hpcr_text_encrypted" "contract" {
  text      = yamlencode(local.workload)
  cert      = var.HPCR_CERT == "" ? null : var.HPCR_CERT
}

resource "local_file" "contract" {
  count    = var.DEBUG ? 1 : 0
  content  = yamlencode(local.workload)
  filename = "backend_plain.yml"
  file_permission = "0664"
}

resource "local_file" "contract_encrypted" {
  content  = hpcr_text_encrypted.contract.rendered
  filename = "backend.yml"
  file_permission = "0664"
}


resource "local_file" "grep11_cfg" {
  count = var.INTERNAL_GREP11 ? 1 : 0
  content = local.grep11_cfg
  filename = "${path.module}/docker-compose/srv1/grep11server.yaml"
  file_permission = "0664"
}

resource "local_file" "grep11_ca_cert" {
  count = var.INTERNAL_GREP11 ? 1 : 0
  content = tls_self_signed_cert.grep11_ca_cert.cert_pem
  filename = "${path.module}/docker-compose/srv1/grep11ca.pem"
  file_permission = "0664"
}

resource "local_file" "grep11_server_key" {
  count = var.INTERNAL_GREP11 ? 1 : 0
  content = tls_private_key.server_key.private_key_pem
  filename = "${path.module}/docker-compose/srv1/grep11server-key.pem"
  file_permission = "0664"
}

resource "local_file" "grep11_server_cert" {
  count = var.INTERNAL_GREP11 ? 1 : 0
  content = tls_locally_signed_cert.server_cert.cert_pem
  filename = "${path.module}/docker-compose/srv1/grep11server.pem"
  file_permission = "0664"
}

resource "local_file" "c16_client_cfg" {
  count = (var.INTERNAL_GREP11 && !var.CRYPTO_PASSTHROUGH_ENABLEMENT) ? 1 : 0
  content = local.c16_cfg
  filename = "${path.module}/docker-compose/cfg/c16client.yaml"
  file_permission = "0664"
}

resource "local_file" "c16_ca_cert" {
  count = (var.INTERNAL_GREP11 && !var.CRYPTO_PASSTHROUGH_ENABLEMENT) ? 1 : 0
  content = var.C16_CA_CERT
  filename = "${path.module}/docker-compose/cfg/ca.pem"
  file_permission = "0664"
}

resource "local_file" "c16_client_cert" {
  count = (var.INTERNAL_GREP11 && !var.CRYPTO_PASSTHROUGH_ENABLEMENT) ? 1 : 0
  content = var.C16_CLIENT_CERT
  filename = "${path.module}/docker-compose/cfg/c16client.pem"
  file_permission = "0664"
}

resource "local_file" "c16_client_key" {
  count = (var.INTERNAL_GREP11 && !var.CRYPTO_PASSTHROUGH_ENABLEMENT) ? 1 : 0
  content = var.C16_CLIENT_KEY
  filename = "${path.module}/docker-compose/cfg/c16client-key.pem"
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

