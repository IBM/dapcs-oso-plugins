#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2025
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
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
