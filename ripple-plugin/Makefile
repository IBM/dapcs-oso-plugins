# Copyright (c) 2025 IBM Corp.
# All rights reserved.
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


.PHONY : build debug test

REGISTRY ?= us.icr.io
NAMESPACE ?= dap-osc-dev
TAG ?= latest

ifdef PIP_UPGRADE
PIP_COMPILE_UPGRADE := --upgrade
endif

PIP_COMPILE = CUSTOM_COMPILE_COMMAND='make pip-compile' pip-compile --quiet --strip-extras --allow-unsafe --generate-hashes $(PIP_COMPILE_UPGRADE)
requirements.constraints.txt: pyproject.toml
	$(PIP_COMPILE) \
		--build-deps-for wheel \
		--extra dependencies \
		--extra test \
		--output-file $@ $<

requirements.txt: requirements.constraints.txt pyproject.toml
	$(PIP_COMPILE) \
		--extra dependencies \
		--output-file $@ \
		--constraint $^

requirements.build.txt: requirements.constraints.txt pyproject.toml
	$(PIP_COMPILE) \
		--only-build-deps \
		--build-deps-for wheel \
		--output-file $@ \
		--constraint $^

hack/requirements.dev.txt: pyproject.toml
	$(PIP_COMPILE) \
		--extra dev \
		--output-file $@ $<

.PHONY: pip-compile
pip-compile: requirements.constraints.txt requirements.txt requirements.build.txt

.PHONY: generate
generate: pip-compile

build :
	docker build \
		. --target release -t oso-ripple-plugins:latest -t $(REGISTRY)/$(NAMESPACE)/oso-ripple-plugins:$(TAG) -f Dockerfile --platform linux/s390x --provenance=false

ifdef RIPPLE_PLUGINS_TEST_RESULTS
VOL_OPTS ::= -v $(RIPPLE_PLUGINS_TEST_RESULTS):/tests/results:rw,z
endif

test-build:
	docker build \
		--target test \
		-t $(REGISTRY)/$(NAMESPACE)/oso-ripple-plugins-test:$(TAG) \
		--platform linux/s390x .

test: test-build
	docker run --rm \
		--workdir /tests \
		--platform linux/s390x \
		--entrypoint pytest \
		$(REGISTRY)/$(NAMESPACE)/oso-ripple-plugins-test:$(TAG)
