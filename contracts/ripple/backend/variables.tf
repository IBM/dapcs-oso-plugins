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

variable "PREFIX" {
  type        = string
}

variable "DEBUG" {
  type        = bool
  description = "Create debug contracts, plaintext"
  default     = false
}

variable "SEED" {
  type        = string
  description = "Encrypt data through the iteration pipeline (should be the same value as frontend plugin)"
  default     = ""
}

variable "BACKEND_PLUGIN_IMAGE" {
  type = string
  description = "Backend plugin image containing registry"
}

variable "COLD_BRIDGE_IMAGE" {
  type = string
  description = "Cold bridge image containing registry"
}

variable "COLD_VAULT_IMAGE" {
  type = string
  description = "Cold vault image containing registry"
}

variable "KMSCONNECT_IMAGE" {
  type = string
  description = "KMS connect image containing registry"
}

variable "VAULT_ID" {
  type = string
  description = "Vault ID"
}

variable "PASSPHRASE" {
  type = string
  default = "{{EMPTY}}"
  description = "Required to enable plugin to view content within a JSON format"
}

variable "NOTARY_MESSAGING_PUBLIC_KEY" {
  type = string
  description = "Notary messaging public key after performing genesis"
}

variable "HPCR_CERT" {
  type        = string
  description = "Public HPCR certificate for contract encryption"
  nullable    = true
  default     = null
}

variable "INTERNAL_GREP11" {
  type = bool
  default = true
  description = "Deploy GREP11 in the backend"
}

variable "GREP11_ENDPOINT" {
  type = string
  description = "GREP11 backend endpoint"
  default = "192.168.96.21"
}

variable "GREP11_CA" {
  type = string
  description = "GREP11 CA certificate"
  default = ""
}

variable "GREP11_CLIENT_KEY" {
  type = string
  description = "GREP11 client key"
  default = ""
}

variable "GREP11_CLIENT_CERT" {
  type = string
  description = "GREP11 client certificate"
  default = ""
}

variable "WORKLOAD_VOL_SEED" {
  type = string
  description = "Workload volume encryption seed"
}

variable "PORT" {
  type        = string
  description = "External port number for api"
  default     = "4000"
}

variable "STATIC_IP" {
  type        = bool
  description = "Deploying via OSO release that supports static IP"
  default     = true
}

variable "GREP11_IMAGE" {
  type        = string
  description = "GREP11 image name with registry"
  nullable = true
  default = null
}

variable "DOMAIN" {
  type        = string
  description = "Crypto appliance domain"
  nullable = true
  default = null
}

variable "C16_CLIENT_HOST" {
  type        = string
  default     = "192.168.128.4"
  description = "Crypto appliance host endpoint"
}

variable "C16_CLIENT_PORT" {
  type    = string
  default = "9001"
}

variable "C16_CLIENT_LOGLEVEL" {
  type    = string
  default = "debug"
  validation {
    condition     = contains(["trace", "debug", "info", "warn", "err", "error", "critical", "off"], var.C16_CLIENT_LOGLEVEL)
    error_message = "Valid values for var: C16_CLIENT_LOGLEVEL are (trace, debug, info, warn, err, error, critical, off)."
  }
}

variable "C16_CLIENT_KEY" {
  type        = string
  description = "Crypto appliance client key"
  default = ""
}

variable "C16_CLIENT_CERT" {
  type        = string
  description = "Crypto appliance client certificate"
  default = ""
}

variable "C16_CA_CERT" {
  type        = string
  description = "Crypto appliance CA certificate"
  default = ""
}

variable "CERT_VALIDITY_PERIOD" {
  type    = string
  default = "720"
}

variable "CRYPTO_PASSTHROUGH_ENABLEMENT" {
  type = bool
  default = true
  description = "Crypto passthrough enablement configuration"
}
