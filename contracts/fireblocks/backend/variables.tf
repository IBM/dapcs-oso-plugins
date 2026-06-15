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

variable "PREFIX" {
  type = string
}

variable "DEBUG" {
  type        = bool
  description = "Create debug contracts, plaintext"
  default     = false
}

variable "BACKEND_PLUGIN_IMAGE" {
  type        = string
  description = "Backend plugin image containing registry"
}

variable "HPCR_CERT" {
  type        = string
  description = "Public HPCR certificate for contract encryption"
  nullable    = true
  default     = null
}

variable "VOLUME_NAME" {
  type        = string
  description = "Volume name"
  default     = "vault_vol"
}

variable "WORKLOAD_VOL_SEED" {
  type        = string
  description = "Workload volume encryption seed"
}

variable "WORKLOAD_VOLUME_PREV_SEED" {
  type        = string
  description = "Previous Workload Seed phrase for conductor disk volume."
  default     = ""
}

variable "INTERNAL_GREP11" {
  type        = bool
  default     = true
  description = "Deploy GREP11 in the backend"
}

variable "BACKEND_EKMF_ADDON_IMAGE" {
  type        = string
  description = "EKMF addon image containing registry"
}

variable "EKMF_ADDON_PORT" {
  type        = number
  default     = 8081
  description = "Port the EKMF addon listens on (must not collide with the plugin app on 8080)"
}

### INTERNAL GREP11 ###

variable "GREP11_IMAGE" {
  type        = string
  description = "GREP11 image name with registry"
  nullable    = true
  default     = null
}

variable "DOMAIN" {
  type        = string
  description = "Crypto appliance domain"
  nullable    = true
  default     = null
}

variable "C16_CLIENT_HOST" {
  type        = string
  default     = "192.168.7.4"
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
  default     = ""
}

variable "C16_CLIENT_CERT" {
  type        = string
  description = "Crypto appliance client certificate"
  default     = ""
}

variable "C16_CA_CERT" {
  type        = string
  description = "Crypto appliance CA certificate"
  default     = ""
}

variable "CRYPTO_PASSTHROUGH_ENABLEMENT" {
  type        = bool
  default     = false
  description = "Crypto passthrough enablement configuration"
}
