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

build-signing-server:
	podman build \
		https://github.com/IBM/signingserver.git -t signing-server:latest -t us.icr.io/dap-osc-dev/signing-server:latest
		
run-signing-server: build-signing-server 
	podman run \
		$(REGISTRY)/$(NAMESPACE)/signing-server:$(TAG)

.PHONY: build-signing-server run-signing-server

PROJECTS := fireblocks-agent fireblocks-plugin gateway-mock

all: $(PROJECTS)

$(PROJECTS):
	$(MAKE) -C $@ build

.PHONY: all $(PROJECTS)
