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

variable "WORKLOAD_VOL_SEED" {
  type        = string
  description = "Workload volume encryption seed"
}

variable "INTERNAL_GREP11" {
  type = bool
  default = true
  description = "Deploy GREP11 in the backend"
}

variable "MIN_KEYS" {
  type = number
  default = 1
  description = "Number of key generated per key type"
}

### INTERNAL GREP11 ###

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

### EXTERNAL GREP11 ###

variable "GREP11_ENDPOINT" {
  type = string
  description = "Standalone GREP11 endpoint"
  default = null
  nullable = true
}

variable "GREP11_CA" {
  type = string
  description = "GREP11 CA certificate (PEM)"
  default = ""
}

variable "GREP11_CLIENT_KEY" {
  type = string
  description = "GREP11 client key PKCS8 (PEM)"
  default = ""
}

variable "GREP11_CLIENT_CERT" {
  type = string
  description = "GREP11 client certificate (PEM)"
  default = ""
}

variable "CRYPTO_PASSTHROUGH_ENABLEMENT" {
  type = bool
  default = false
  description = "Crypto passthrough enablement configuration"
}

