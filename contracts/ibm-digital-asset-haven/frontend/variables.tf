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
  default     = ""
}

variable "FRONTEND_PLUGIN_IMAGE" {
  type        = string
  description = "Frontend plugin image name"
}

variable "HSMDRIVER_IMAGE" {
  type        = string
  description = "HSM Driver image name"
}

variable "PROXY_ADDRESS" {
  type        = string
  description = "address of the hsm-proxy endpoint"
  default     = "hsm-proxy.digitalassets.ibm.com:8443"
}
