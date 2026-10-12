#!/usr/bin/env bash
# Copyright (c) 2025 IBM Corp.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# setup-build-host.sh
#
# Configures a build host (or CI runner) for signed-image enforcement.
#
# What this script does:
#   1. Downloads the Red Hat container-signing GPG key from the official
#      Red Hat security page and verifies its fingerprint before trusting it.
#   2. Writes /etc/containers/policy.json to enforce GPG signature checks
#      on all images pulled from registry.access.redhat.com (i.e. UBI base
#      images used in the Dockerfile FROM lines).
#   3. Writes /etc/containers/registries.d/redhat.yaml so podman knows
#      where to fetch Red Hat image signatures (their public sigstore).
#
# Must be run as root (or with sudo) because it writes to /etc/containers/.
# Safe to re-run — all writes are idempotent.
#
# Usage:
#   sudo ./setup-build-host.sh
#
# To verify the setup afterwards:
#   podman image trust show

set -euo pipefail

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Red Hat container image signing key (FD431D51).
# Source: https://access.redhat.com/security/team/key
RH_GPG_KEY_URL="https://www.redhat.com/security/fd431d51.txt"

# Expected fingerprint — verify this against https://access.redhat.com/security/team/key
# before running this script in a new environment.
RH_GPG_EXPECTED_FINGERPRINT="567E 347A D004 4ADE 55BA 8A5F 199E 2F91 FD43 1D51"

RH_GPG_KEY_DEST="/etc/pki/rpm-gpg/RPM-GPG-KEY-redhat-release"
POLICY_JSON="/etc/containers/policy.json"
REGISTRIES_D_DIR="/etc/containers/registries.d"
REGISTRIES_D_FILE="${REGISTRIES_D_DIR}/redhat.yaml"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

info()  { echo "[INFO]  $*"; }
warn()  { echo "[WARN]  $*" >&2; }
die()   { echo "[ERROR] $*" >&2; exit 1; }

require_root() {
    [[ "$(id -u)" -eq 0 ]] || die "This script must be run as root (use sudo)."
}

require_cmd() {
    command -v "$1" &>/dev/null || die "Required command not found: $1 — please install it first."
}

# ---------------------------------------------------------------------------
# Step 1 — Download and verify the Red Hat GPG key
# ---------------------------------------------------------------------------

download_and_verify_gpg_key() {
    info "Downloading Red Hat GPG key from ${RH_GPG_KEY_URL} ..."
    local tmp_key
    tmp_key=$(mktemp /tmp/rh-gpg-key.XXXXXX)
    curl --silent --fail --location "${RH_GPG_KEY_URL}" --output "${tmp_key}" \
        || die "Failed to download Red Hat GPG key from ${RH_GPG_KEY_URL}"

    info "Verifying GPG key fingerprint ..."
    local actual_fingerprint
    actual_fingerprint=$(gpg --with-fingerprint --with-colons "${tmp_key}" 2>/dev/null \
        | awk -F: '/^fpr:/ { print $10; exit }' \
        | sed 's/.\{4\}/& /g' | sed 's/  / /g' | xargs)

    # Normalise both sides to uppercase, no spaces, for comparison
    local expected_norm actual_norm
    expected_norm=$(echo "${RH_GPG_EXPECTED_FINGERPRINT}" | tr -d ' ' | tr '[:lower:]' '[:upper:]')
    actual_norm=$(echo "${actual_fingerprint}"            | tr -d ' ' | tr '[:lower:]' '[:upper:]')

    if [[ "${actual_norm}" != "${expected_norm}" ]]; then
        rm -f "${tmp_key}"
        die "GPG fingerprint mismatch!
  Expected : ${RH_GPG_EXPECTED_FINGERPRINT}
  Got      : ${actual_fingerprint}
Aborting — do NOT trust this key. Verify https://access.redhat.com/security/team/key manually."
    fi

    info "Fingerprint verified: ${actual_fingerprint}"
    mkdir -p "$(dirname "${RH_GPG_KEY_DEST}")"
    cp "${tmp_key}" "${RH_GPG_KEY_DEST}"
    chmod 0644 "${RH_GPG_KEY_DEST}"
    rm -f "${tmp_key}"
    info "Key installed at ${RH_GPG_KEY_DEST}"
}

# ---------------------------------------------------------------------------
# Step 2 — Write /etc/containers/policy.json
# ---------------------------------------------------------------------------

write_policy_json() {
    info "Writing ${POLICY_JSON} ..."
    mkdir -p "$(dirname "${POLICY_JSON}")"
    cat > "${POLICY_JSON}" <<'EOF'
{
  "default": [{ "type": "reject" }],
  "transports": {
    "containers-storage": {
      "": [{ "type": "insecureAcceptAnything" }]
    },
    "docker": {
      "registry.access.redhat.com": [
        {
          "type": "signedBy",
          "keyType": "GPGKeys",
          "keyPath": "/etc/pki/rpm-gpg/RPM-GPG-KEY-redhat-release"
        }
      ],
      "registry.control23.dap.local": [
        { "type": "insecureAcceptAnything" }
      ],
      "quay.io/centos/centos": [
        { "type": "insecureAcceptAnything" }
      ]
    }
  }
}
EOF
    chmod 0644 "${POLICY_JSON}"
    info "${POLICY_JSON} written."
}

# ---------------------------------------------------------------------------
# Step 3 — Write /etc/containers/registries.d/redhat.yaml (sigstore location)
#           Skipped if any existing file in registries.d already defines
#           registry.access.redhat.com (e.g. the distro-shipped
#           registry.access.redhat.com.yaml on RHEL hosts).
# ---------------------------------------------------------------------------

write_registries_d() {
    mkdir -p "${REGISTRIES_D_DIR}"

    # Check whether registry.access.redhat.com is already defined in any
    # existing registries.d file — if so, skip to avoid a duplicate-namespace error.
    local existing_files existing_file
    mapfile -t existing_files < <(grep -rl "registry.access.redhat.com" "${REGISTRIES_D_DIR}" 2>/dev/null || true)
    if [[ ${#existing_files[@]} -gt 0 ]]; then
        info "Skipping ${REGISTRIES_D_FILE} — registry.access.redhat.com already defined in:"
        for existing_file in "${existing_files[@]}"; do
            info "  ${existing_file}"
            grep -q "access.redhat.com/webassets/docker/content/sigstore" "${existing_file}" \
                || warn "  ${existing_file} does NOT point to the expected Red Hat sigstore URL."
        done
        return
    fi

    info "Writing ${REGISTRIES_D_FILE} ..."
    cat > "${REGISTRIES_D_FILE}" <<'EOF'
docker:
  registry.access.redhat.com:
    sigstore: https://access.redhat.com/webassets/docker/content/sigstore
EOF
    chmod 0644 "${REGISTRIES_D_FILE}"
    info "${REGISTRIES_D_FILE} written."
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

require_root
require_cmd curl
require_cmd gpg

download_and_verify_gpg_key
write_policy_json
write_registries_d

info ""
info "Build host setup complete."
info "Verify with: podman image trust show"
