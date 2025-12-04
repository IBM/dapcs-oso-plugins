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

variable "IMAGE" {
  type        = string
  description = "GREP11 image name with registry"
}

variable "PORT" {
  type        = string
  description = "GREP11 port number"
  default     = "9876"
}

variable "HPCR_CERT" {
  type        = string
  description = "Public HPCR certificate for contract encryption"
  nullable    = true
  default     = null
}

variable "DEBUG" {
  type        = bool
  description = "Create debug contracts, plaintext"
  default     = false
}

variable "DOMAIN" {
  type        =  string
  description = "Crypto appliance domain"
}

variable "C16_CLIENT_HOST" {
  type        = string
  default     = "192.168.128.4"
  description = "Crypto appliance host endpoint"
}

variable "C16_CLIENT_PORT" {
  type       = string
  default    = "9001"
}

variable "C16_CLIENT_LOGLEVEL" {
  type        = string
  default     = "debug"
  validation {
    condition     = contains(["trace", "debug", "info", "warn", "err", "error", "critical", "off"], var.C16_CLIENT_LOGLEVEL)
    error_message = "Valid values for var: C16_CLIENT_LOGLEVEL are (trace, debug, info, warn, err, error, critical, off)."
  }
}

variable "C16_CLIENT_KEY" {
  type        = string
  description = "Crypto appliance client key"
}

variable "C16_CLIENT_CERT" {
  type        = string
  description = "Crypto appliance client certificate"
}

variable "C16_CA_CERT" {
  type        = string
  description = "Crypto appliance CA certificate"
}

variable "CERT_VALIDITY_PERIOD" {
  type = string
  default = "720"
}

variable "STATIC_IP" {
  type        = bool
  description = "Deploying via OSO release that supports static IP"
  default     = true
}

variable "STATIC_IP_ADDRS" {
  type        = list(string)
  description = "Static IP addresses assigned to grep11 VM"
  default     = ["192.168.64.21", "192.168.96.21", "192.168.128.21"]
}
