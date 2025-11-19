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

variable "FIREBLOCKS_AGENT_IMAGE" {
  type        = string
  description = "Fireblocks agent image name"
}

# Fireblocks
variable "MOBILE_GATEWAY_URL" {
  type        = string
  description = "Fireblocks mobile gateway url"
  default     = "https://mobile-api.fireblocks.io"
}

variable "REFRESH_TOKEN" {
  type        = string
  description = "Fireblocks refresh token (in base64)"
}
