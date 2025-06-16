#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
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
		. -t dapcs-fireblocks-oso-plugins:latest -t $(REGISTRY)/$(NAMESPACE)/dapcs-fireblocks-oso-plugins:$(TAG) -f Containerfile

.PHONY: unit-test cov-test
unit-test:
	uv run pytest

cov-test:
	@if [ -z "$(TEST_RESULTS)" ]; then \
		echo "TEST_RESULTS not set"; \
		exit 1; \
	fi

	uv run pytest \
		--verbose \
		--import-mode=importlib \
		--cov=fb \
		--cov-report=xml:$(TEST_RESULTS)/coverage.xml \
		--junit-xml=$(TEST_RESULTS)/junit.xml
