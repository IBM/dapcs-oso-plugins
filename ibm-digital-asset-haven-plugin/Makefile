#
# (c) Copyright IBM Corp. 2025
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

TEMP_DIR := $(shell mktemp -d)
REGISTRY ?= us.icr.io
NAMESPACE ?= dap-osc-dev
TAG ?= latest

.PHONY: install build

build:
	docker build \
		. -t dapcs-haven-oso-plugins:latest -t $(REGISTRY)/$(NAMESPACE)/dapcs-haven-oso-plugins:$(TAG) -f Containerfile

save:
	docker save -o OSO-PLUGIN-IMAGE.tar $(REGISTRY)/$(NAMESPACE)/dapcs-haven-oso-plugins:$(TAG)
