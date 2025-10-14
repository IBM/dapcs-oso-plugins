#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2025
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

terraform {
  required_providers {
    hpcr = {
      source  = "ibm-hyper-protect/hpcr"
      version = ">= 0.11.0"
    }
    null = {
      source = "hashicorp/null"
      version = "3.2.3"
    }
  }
}
