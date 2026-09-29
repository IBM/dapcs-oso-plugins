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

ARG RELEASEVER=9
ARG NGINX_VERSION=1.30.4
ARG NGINX_PKG_RELEASE=1~trixie

# ---- nginx RPM build ----
FROM registry.access.redhat.com/ubi${RELEASEVER}/ubi-minimal:latest AS nginx-build

ARG RELEASEVER
ARG NGINX_VERSION
ARG NGINX_PKG_RELEASE

WORKDIR /build
RUN microdnf --assumeyes \
        --setopt=install_weak_deps=0 \
        --setopt=keepcache=0 \
        --disablerepo='*' \
        --enablerepo=ubi-${RELEASEVER}-baseos-rpms \
        --enablerepo=ubi-${RELEASEVER}-appstream-rpms \
        --enablerepo=ubi-${RELEASEVER}-codeready-builder-rpms \
        install \
            tar gzip make gcc patch findutils diffutils \
            libxslt openssl-devel pcre2-devel zlib-devel \
            rpm-build rpmlint rpmdevtools \
    ; microdnf --assumeyes clean all

ADD --checksum=sha256:a5a3c5c29504d411f3d82738322dcc9a24202db652512878051a9767eb4ce714 \
    https://github.com/nginx/pkg-oss/archive/refs/tags/${NGINX_VERSION}-${NGINX_PKG_RELEASE%~*}.tar.gz \
    /archive
COPY /patches/nginx.spec.in.patch /project/
RUN tar xzf /archive -C /project --strip-components=1 \
    && cd /project/rpm/SPECS \
    && patch < /project/nginx.spec.in.patch \
    && make base


FROM registry.access.redhat.com/ubi${RELEASEVER}/ubi-minimal:latest AS compile

ENV HOME=/app-root
RUN --mount=type=bind,from=quay.io/centos/centos:stream9,source=/etc/yum.repos.d/centos.repo,target=/etc/yum.repos.d/centos.repo \
    --mount=type=bind,from=quay.io/centos/centos:stream9,source=/etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial,target=/etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial \
    --mount=type=bind,from=quay.io/centos/centos:stream9,source=/etc/yum/vars/stream,target=/etc/yum/vars/stream \
    rpm --install https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm \
    && microdnf --assumeyes \
        --setopt=install_weak_deps=0 \
        --setopt=keepcache=0 \
        --disablerepo='*' \
        --enablerepo=ubi-9-baseos-rpms \
        --enablerepo=ubi-9-appstream-rpms \
        --enablerepo=ubi-9-codeready-builder-rpms \
        --enablerepo=epel \
        install \
            openssl-devel \
            gcc cargo rustc \
            python3.13 python3.13-pip python3.13-devel \
    && mkdir -p "${HOME}"
ARG PIP_INDEX_URL=https://pypi.org/simple

COPY /requirements*.txt /tmp
RUN --mount=type=secret,id=netrc,target=${HOME}/.netrc,mode=0600 \
    pip3.13 install --upgrade --require-hashes \
        --requirement <(gawk 'BEGIN { RS = "[^\\\\]\n" } /pip==/ { print }' /tmp/requirements.constraints.txt) \
    && pip3.13 install --requirement /tmp/requirements.build.txt \
    && python3.13 -m venv --without-pip /opt/venv \
    && pip3.13 --python /opt/venv install --requirement /tmp/requirements.txt

COPY /src/oso_ripple_plugins /src/oso_ripple_plugins
COPY /src/setup.py /src
RUN pip3.13 wheel --wheel-dir /build --no-index --no-build-isolation /src \
    && pip3.13 --python /opt/venv install --no-index --find-links /build oso_ripple_plugins


# ---- Runtime packages installed into an empty root ----
FROM registry.access.redhat.com/ubi${RELEASEVER}/ubi:latest AS runtime-install

ARG RELEASEVER
ARG NGINX_VERSION
ARG NGINX_PKG_RELEASE

RUN --mount=type=bind,from=quay.io/centos/centos:stream9,source=/etc/yum.repos.d/centos.repo,target=/etc/yum.repos.d/centos.repo \
    --mount=type=bind,from=quay.io/centos/centos:stream9,source=/etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial,target=/etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial \
    --mount=type=bind,from=quay.io/centos/centos:stream9,source=/etc/yum/vars/stream,target=/etc/yum/vars/stream \
    rpm --install https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm \
    && mkdir /installroot \
    && dnf --assumeyes \
        --setopt=install_weak_deps=0 \
        --setopt=keepcache=0 \
        --setopt=tsflags=nodocs \
        --disablerepo='*' \
        --enablerepo=ubi-${RELEASEVER}-baseos-rpms \
        --enablerepo=ubi-${RELEASEVER}-appstream-rpms \
        --enablerepo=epel \
        --installroot=/installroot \
        --releasever=${RELEASEVER} \
        install \
            python3.13 gettext findutils \
            libstdc++ openssl pcre2 zlib \
            procps-ng shadow-utils tzdata \
    && dnf --assumeyes clean all --installroot=/installroot \
    && test -x /installroot/usr/bin/python3.13

COPY --from=nginx-build /project/rpm/RPMS/*/*.rpm /RPMS/
RUN rpm --install \
        --root=/installroot \
        --nodeps \
        --noscripts \
        --excludedocs \
        /RPMS/nginx-${NGINX_VERSION}-${NGINX_PKG_RELEASE%~*}.el${RELEASEVER}.ngx.*.rpm


# ---- Micro runtime base ----
FROM registry.access.redhat.com/ubi${RELEASEVER}/ubi-micro:latest AS live

COPY --from=runtime-install /installroot /

ENV HOME=/app-root
RUN install --directory --mode 0700 --owner 1001 --group 0 \
        "${HOME}" \
        "${HOME}/.ssh" \
    ; chown -R 1001:0 /var/run \
    ; chmod -R ug+rwX /var/run \
    ; chown -R 1001:0 /var/lib/nginx \
    ; chmod -R ug+rwX /var/lib/nginx \
    ; chown -R 1001:0 /var/log/nginx \
    ; chmod -R ug+rwX /var/log/nginx \
    ; chown -R 1001:0 /var/cache/nginx \
    ; chmod -R ug+rwX /var/cache/nginx \
    ; chown -R 1001:0 /usr/local/etc \
    ; chmod -R ug+rwX /usr/local/etc \
    ;


FROM live AS release

COPY --from=compile --chown=1001:0 /opt/venv /opt/venv
COPY --from=compile --chown=1001:0 ${HOME} ${HOME}
COPY --chown=1001:0 /src/app-root /oso-root

USER 1001
ENV PATH="/opt/venv/bin:$PATH"
CMD [ "/oso-root/common/entrypoints/entrypoint.sh" ]


# ---- Test stage ----
FROM compile AS test

ENV PATH="/opt/venv/bin:$PATH"
RUN --mount=type=bind,from=quay.io/centos/centos:stream9,source=/etc/yum.repos.d/centos.repo,target=/etc/yum.repos.d/centos.repo \
    --mount=type=bind,from=quay.io/centos/centos:stream9,source=/etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial,target=/etc/pki/rpm-gpg/RPM-GPG-KEY-centosofficial \
    --mount=type=bind,from=quay.io/centos/centos:stream9,source=/etc/yum/vars/stream,target=/etc/yum/vars/stream \
    microdnf --assumeyes \
        --setopt=install_weak_deps=0 \
        --disablerepo='*' \
        --enablerepo=ubi-9-baseos-rpms \
        --enablerepo=ubi-9-appstream-rpms \
        --enablerepo=ubi-9-codeready-builder-rpms \
        --enablerepo=epel \
        install \
            gcc \
            make \
            python3.13-devel \
            openssl-devel \
    && microdnf clean all
COPY --from=compile /opt/venv /opt/venv
COPY --chown=1001:0 /unit-tests /pyproject.toml /tests/
RUN pip3.13 --python /opt/venv install --requirement /tmp/requirements.constraints.txt
CMD ["pytest", "-svvv"]
