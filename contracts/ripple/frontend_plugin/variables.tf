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

variable "DEBUG" {
  type        = bool
  description = "Create debug contracts, plaintext"
  default     = false
}

variable "HPCR_CERT" {
  type        = string
  description = "Public HPCR certificate for contract encryption"
  nullable    = true
  default     = null
}

variable "FRONTEND_PLUGIN_IMAGE" {
  type        = string
  description = "Frontend plugin image name"
}

variable "SEED" {
  type        = string
  description = "Encrypt data through the iteration pipeline (should be same value as backend plugin)"
  default     = ""
}

# Ripple
variable "SK" {
  type        = string
  description = "Private (secret) key of a registered user used to login to Ripple"
}

variable "VAULT_ID" {
  type        = string
  description = "Ripple vault id"
}

variable "HMZ_AUTH_HOSTNAME" {
  type        = string
  description = "Ripple auth hostname containing no protocol or path"
}

variable "HMZ_API_HOSTNAME" {
  type        = string
  description = "Ripple api hostname containing no protocol or path"
}

variable "ROOTCERT" {
  type        = string
  description = "Ripple SSL server certification as base64 encoded (optional)"
  default     = ""
}

variable "TOKEN_EXP" {
  type        = string
  description = "Ripple configured bearer token expiration (#h#m#s format)"
  default     = "4h0m0s"
}

variable "PORT" {
  type        = string
  description = "Frontend plugin port"
  default     = "8080"
}

variable "CONFIRMATION_FINGERPRINT" {
  type        = string
  description = "Confirmation fingerprint for frontend plugin"
}

variable "COMPONENT_CA_CERT" {
  type        = string
  description = "Component CA certificate for frontend plugin"
}

variable "FRONTEND_PLUGIN_KEY" {
  type        = string
  description = "Frontend plugin private key"
  sensitive   = true
}

variable "FRONTEND_PLUGIN_CERT" {
  type        = string
  description = "Frontend plugin certificate"
  sensitive   = true
}
