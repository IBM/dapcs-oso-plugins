#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2025
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

TEMP_DIR := $(shell mktemp -d)
REGISTRY ?= us.icr.io
NAMESPACE ?= dap-osc-dev
TAG ?= latest

.PHONY: install build

build:
	docker build \
		. -t dapcs-oso-idah-plugins:latest -t $(REGISTRY)/$(NAMESPACE)/dapcs-oso-idah-plugins:$(TAG) -f Containerfile

save:
	docker save -o OSO-PLUGIN-IMAGE.tar $(REGISTRY)/$(NAMESPACE)/dapcs-oso-idah-plugins:$(TAG)
