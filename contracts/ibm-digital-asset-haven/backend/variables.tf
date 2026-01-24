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

variable "HPCR_CERT" {
  type        = string
  description = "Public HPCR certificate for contract encryption"
  nullable    = true
  default     = ""
}

variable "WORKLOAD_VOL_SEED" {
  type        = string
  description = "Workload volume encryption seed"
}

variable "BACKEND_PLUGIN_IMAGE" {
  type        = string
  description = "Backend plugin image containing registry"
}

variable "HSMDRIVER_IMAGE" {
  type        = string
  description = "HSM Driver image name"
}

variable "USER_PIN" {
  type        = string
  description = "PKCS11 normal user PIN"
}

variable "SO_PIN" {
  type        = string
  description = "PKCS11 SO PIN"
  default     = "87654321"
}

variable "WORKLOAD_VOLUME_PREV_SEED" {
  type        = string
  description = "Previous Workload Seed phrase for conductor disk volume."
  default     = ""
}

variable "PREGEN_KEYS" {
  type        = number
  description = "No of Key-Pair to be generated at time of DB Provisioning"
  default     = 1000
}

variable "LOG_LEVEL" {
  type        = string
  description = "Log Level for HSM Signer"
  default     = "info"
}
