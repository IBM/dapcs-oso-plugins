#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#


REGISTRY ?= us.icr.io
NAMESPACE ?= dap-osc-dev
TAG ?= latest

build: 
	podman build \
		. -t gateway-mock:latest -t $(REGISTRY)/$(NAMESPACE)/gateway-mock:$(TAG) -f Containerfile

run: build
	podman run \
		-d -p 3000:3000 \
		$(REGISTRY)/$(NAMESPACE)/gateway-mock:$(TAG)

.PHONY: build run
