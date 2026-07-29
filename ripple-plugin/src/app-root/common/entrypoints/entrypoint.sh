#!/bin/bash
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
#

cp -r /oso-root/"${COMPONENT}"/*    /app-root

if [ "${DEBUG}" == "true" ]; then
	if [ -z "${SSH_PORT}" ]; then
		echo "ERROR: DEBUG=true but SSH_PORT is not set" >&2
		exit 1
	fi
	# Support both OSO_SSH_PUBKEY (new) and SSH_PUBKEY (legacy)
	_SSH_PUBKEY="${OSO_SSH_PUBKEY:-${SSH_PUBKEY}}"
	# Support both OSO_SSH_PASSWORD (new) and SSH_PASSWORD (legacy)
	_SSH_PASSWORD="${OSO_SSH_PASSWORD:-${SSH_PASSWORD}}"

	if [ -z "${_SSH_PUBKEY}" ] && [ -z "${_SSH_PASSWORD}" ]; then
		echo "ERROR: DEBUG=true but neither OSO_SSH_PUBKEY nor OSO_SSH_PASSWORD is set" >&2
		exit 1
	fi

	# ── authorized_keys ────────────────────────────────────────────────────────
	if [ -n "${_SSH_PUBKEY}" ]; then
		echo "[DEBUG] Writing OSO_SSH_PUBKEY to ${HOME}/.ssh/authorized_keys"
		echo "${_SSH_PUBKEY}" > "${HOME}/.ssh/authorized_keys"
		chmod 0600 "${HOME}/.ssh/authorized_keys"
	else
		echo "[DEBUG] OSO_SSH_PUBKEY not set — publickey auth will not work"
		> "${HOME}/.ssh/authorized_keys"
	fi

	# ── optional password auth ──────────────────────────────────────────────────
	# Password is set at image build time (Dockerfile ARG SSH_PASSWORD) since
	# the container runs as UID 1001 which cannot write /etc/passwd at runtime.
	if [ -n "${_SSH_PASSWORD}" ]; then
		PASSWORD_AUTH="yes"
	else
		PASSWORD_AUTH="no"
	fi

	# ── container-local sshd config — never touch host /etc/ssh/sshd_config ───
	# Write a minimal self-contained config from scratch.
	# Avoids inheriting the base config's "Include" drop-ins or conflicting
	# directives (e.g. PasswordAuthentication no from sshd_config.d/).
	SSHD_CONFIG="${HOME}/.ssh/sshd_config"
	SSHD_LOG="${HOME}/.ssh/sshd.log"
	cat > "${SSHD_CONFIG}" <<-EOF
		Port ${SSH_PORT}
		ListenAddress 0.0.0.0
		HostKey /etc/ssh/ssh_host_rsa_key
		HostKey /etc/ssh/ssh_host_ecdsa_key
		HostKey /etc/ssh/ssh_host_ed25519_key
		AuthorizedKeysFile ${HOME}/.ssh/authorized_keys
		PasswordAuthentication ${PASSWORD_AUTH}
		PubkeyAuthentication yes
		StrictModes no
		ChallengeResponseAuthentication no
		KbdInteractiveAuthentication no
		UsePAM yes
		LogLevel DEBUG3
		SyslogFacility AUTH
		Subsystem sftp /usr/libexec/openssh/sftp-server
	EOF
	chmod 0644 "${SSHD_CONFIG}"
	touch "${SSHD_LOG}"
	chmod 0644 "${SSHD_LOG}"
	export SSHD_CONFIG
	export SSHD_LOG

	# ── diagnostics printed at container startup ────────────────────────────────
	echo "[DEBUG] ======== SSH debug info ========"
	echo "[DEBUG] SSH_PORT              = ${SSH_PORT}"
	echo "[DEBUG] SSHD_CONFIG           = ${SSHD_CONFIG}"
	echo "[DEBUG] SSHD_LOG              = ${SSHD_LOG}"
	echo "[DEBUG] authorized_keys       = $(cat "${HOME}/.ssh/authorized_keys")"
	echo "[DEBUG] authorized_keys perms = $(stat -c '%a %U:%G' "${HOME}/.ssh/authorized_keys")"
	echo "[DEBUG] .ssh dir perms        = $(stat -c '%a %U:%G' "${HOME}/.ssh")"
	echo "[DEBUG] HOME                  = ${HOME}"
	echo "[DEBUG] whoami                = $(whoami)"
	echo "[DEBUG] id                    = $(id)"
	echo "[DEBUG] sshd_config contents:"
	cat "${SSHD_CONFIG}"
	echo "[DEBUG] Validating sshd config:"
	/usr/sbin/sshd -t -f "${SSHD_CONFIG}" && echo "[DEBUG] sshd config OK" || echo "[DEBUG] sshd config INVALID"
	echo "[DEBUG] ================================"
else
	export DEBUG="false"
fi

umask 0007
/app-root/entrypoints/entrypoint.sh

