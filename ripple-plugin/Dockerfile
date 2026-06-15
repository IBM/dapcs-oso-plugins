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


FROM registry.access.redhat.com/ubi9/ubi-minimal:latest AS live

ENV HOME=/app-root
RUN microdnf --assumeyes module enable nginx:1.24 \
    && microdnf --assumeyes \
        --setopt=install_weak_deps=0 \
        --disablerepo='*' \
        --enablerepo=ubi-9-baseos-rpms \
        --enablerepo=ubi-9-appstream-rpms \
        install \
            python3.12 \
            gettext nginx findutils \
    && microdnf clean all

RUN install --directory --mode 0700 --owner 1001 --group 0 \
        "${HOME}" \
        "${HOME}/.ssh" \
    && chown -R 1001:0 /var/run \
    && chmod -R ug+rwX /var/run \
    && chown -R 1001:0 /var/lib/nginx \
    && chmod -R ug+rwX /var/lib/nginx \
    && chown -R 1001:0 /var/log/nginx \
    && chmod -R ug+rwX /var/log/nginx \
    && chown -R 1001:0 /usr/local/etc \
    && chmod -R ug+rwX /usr/local/etc \
    ;

FROM registry.access.redhat.com/ubi9/ubi-minimal:latest AS compile

ENV HOME=/app-root
RUN microdnf --assumeyes \
        --setopt=install_weak_deps=0 \
        --setopt=keepcache=0 \
        --disablerepo='*' \
        --enablerepo=ubi-9-baseos-rpms \
        --enablerepo=ubi-9-appstream-rpms \
        install \
            openssl-devel \
            gcc cargo rustc \
            python3.12-pip python3.12-devel \
    && mkdir -p "${HOME}"
ARG PIP_INDEX_URL=https://pypi.org/simple 

COPY /requirements*.txt /tmp
RUN --mount=type=secret,id=netrc,target=${HOME}/.netrc,mode=0600 \
    pip3.12 install --upgrade --require-hashes \
        --requirement <(gawk 'BEGIN { RS = "[^\\\\]\n" } /pip==/ { print }' /tmp/requirements.constraints.txt) \
    && pip3.12 install --requirement /tmp/requirements.build.txt \
    && python3.12 -m venv --without-pip /opt/venv \
    && pip3.12 --python /opt/venv install --requirement /tmp/requirements.txt

COPY /src/oso_ripple_plugins /src/oso_ripple_plugins
COPY /src/setup.py /src
RUN pip3.12 wheel --wheel-dir /build --no-index --no-build-isolation /src \
    && pip3.12 --python /opt/venv install --no-index --find-links /build oso_ripple_plugins

FROM live AS release

COPY --from=compile --chown=1001:0 /opt/venv /opt/venv
COPY --from=compile --chown=1001:0 ${HOME} ${HOME}
COPY --chown=1001:0 /src/app-root /oso-root

USER 1001
ENV PATH="/opt/venv/bin:$PATH"
CMD [ "/oso-root/common/entrypoints/entrypoint.sh" ]


FROM compile AS test

ENV PATH="/opt/venv/bin:$PATH"
RUN microdnf --assumeyes \
        --setopt=install_weak_deps=0 \
        --disablerepo='*' \
        --enablerepo=ubi-9-baseos-rpms \
        --enablerepo=ubi-9-appstream-rpms \
        install \
            gcc \
            make \
            python3.12-devel \
            openssl-devel \
    && microdnf clean all
COPY --from=compile /opt/venv /opt/venv
COPY --chown=1001:0 /unit-tests /pyproject.toml /tests/
RUN pip3.12 --python /opt/venv install --requirement /tmp/requirements.constraints.txt
CMD ["pytest", "-svvv"]