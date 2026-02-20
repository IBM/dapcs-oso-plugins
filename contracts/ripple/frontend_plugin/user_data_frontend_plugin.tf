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

# Generate Pod YAML for Podman
resource "local_file" "frontend_plugin_pod" {
  content = templatefile(
    "${path.module}/frontend_plugin.yml.tftpl",
    { tpl = {
      image             = var.FRONTEND_PLUGIN_IMAGE,
      PORT              = var.PORT,
      SK                = var.SK,
      VAULTID           = var.VAULT_ID,
      HMZ_AUTH_HOSTNAME = var.HMZ_AUTH_HOSTNAME,
      HMZ_API_HOSTNAME  = var.HMZ_API_HOSTNAME,
      ROOTCERT          = var.ROOTCERT,
      SEED              = var.SEED,
      TOKEN_EXP         = var.TOKEN_EXP
    } },
  )
  filename        = "frontend_plugin/pod.yml"
  file_permission = "0664"
}

# Generate ConfigMap YAML
resource "local_file" "frontend_plugin_configmap" {
  content = templatefile(
    "${path.module}/frontend_plugin/configmap.yml.tftpl",
    {
      port                     = var.PORT,
      confirmation_fingerprint = var.CONFIRMATION_FINGERPRINT,
      component_ca_cert        = var.COMPONENT_CA_CERT
    }
  )
  filename        = "frontend_plugin/configmap.yml"
  file_permission = "0664"
}

# Generate Secret YAML
resource "local_file" "frontend_plugin_secret" {
  content = templatefile(
    "${path.module}/frontend_plugin/secret.yml.tftpl",
    {
      frontend_key  = base64encode(var.FRONTEND_PLUGIN_KEY),
      frontend_cert = base64encode(var.FRONTEND_PLUGIN_CERT)
    }
  )
  filename        = "frontend_plugin/secret.yml"
  file_permission = "0664"
}

# archive of the folder containing Podman Kube YAML files. This folder contains pod.yml, configmap.yml, and secret.yml
# All of these files get bundled in a tgz file (base64 encoded)
resource "hpcr_tgz" "frontend_plugin_workload" {
  depends_on = [
    local_file.frontend_plugin_pod,
    local_file.frontend_plugin_configmap,
    local_file.frontend_plugin_secret
  ]
  folder = "frontend_plugin"
}

locals {
  frontend_plugin_kube = {
    "kube" : {
      "archive" : hpcr_tgz.frontend_plugin_workload.rendered
    }
  }
  frontend_plugin_workload = merge(local.workload_template, local.frontend_plugin_kube)
}

# In this step we encrypt the fields of the contract and sign the env and workload field. The certificate to execute the
# encryption it built into the provider and matches the latest HPCR image. If required it can be overridden.
# We use a temporary, random keypair to execute the signature. This could also be overriden.
resource "hpcr_text_encrypted" "frontend_plugin_contract" {
  text = yamlencode(local.frontend_plugin_workload)
  cert = var.HPCR_CERT == "" ? null : var.HPCR_CERT
}

resource "local_file" "frontend_plugin_contract" {
  count           = var.DEBUG ? 1 : 0
  content         = yamlencode(local.frontend_plugin_workload)
  filename        = "frontend_plugin_contract.yml"
  file_permission = "0664"
}

resource "local_file" "frontend_plugin_contract_encrypted" {
  content         = hpcr_text_encrypted.frontend_plugin_contract.rendered
  filename        = "frontend_plugin.yml"
  file_permission = "0664"
}
