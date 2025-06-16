#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2025
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
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
