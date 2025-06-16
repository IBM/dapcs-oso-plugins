#!/bin/bash
#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2025
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

exportTF() {
	declare -gx tf="/usr/local/bin/tofu"
	if ! [[ -e "${tf}" ]]; then
		tf="/usr/local/bin/terraform"
		if ! [[ -e "${tf}" ]]; then
			builtin echo "FATAL: Neither OpenTofu nor Terraform is installed!"
			builtin return 1
		fi
	fi
	builtin return
}

exportCP() {
	declare -gx CP="/usr/bin/cp"
	builtin return
}
