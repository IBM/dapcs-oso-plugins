# Offline Signing Orchestrator - Ripple Custody Plugin

The plugin provided within this repository contains the code required to integrate Ripple Custody with the Offline Signing Orchestrator (OSO). Additional tooling is provided to generate the plugin image and to generate encrypted HPVS contracts used as workload configuration options within OSO. The Ripple Custody plugin image is expected to be built and uploaded to a private container image registry along with other images, accessible to all OSO LPARs.

## Prerequisites

- [Offline Signing Orchestrator](https://www.ibm.com/docs/en/hpdaoso)
- [Podman](https://podman.io/) (replaces Docker — required for GPG-based image trust enforcement via `policy.json`)
- `curl` and `gpg` — used by `setup-build-host.sh` to download and verify the Red Hat signing key

> **Why Podman?**
> The build enforces GPG signature verification on all UBI base images pulled from
> `registry.access.redhat.com` using [`/etc/containers/policy.json`](https://github.com/podman-container-tools/podman/blob/main/docs/tutorials/image_signing.md).
> Docker does not read `policy.json` — this enforcement only works with Podman.
> `--pull=always` is also set on every build so the local image cache is never used,
> defeating stale-cache substitution attacks.

## Build Host Setup

Every build host or CI runner must be configured once before the first build.
Run the provided script **as root**:

```bash
cd ripple-plugin
sudo ./setup-build-host.sh
```

The script performs three steps:

1. **Downloads the Red Hat GPG key** (`FD431D51`) from `https://www.redhat.com/security/fd431d51.txt`
   and verifies its fingerprint (`567E 347A D044 2268 1029 5A6F 53D5 E571 FD43 1D51`)
   against the value published at https://access.redhat.com/security/team/key before
   installing it to `/etc/pki/rpm-gpg/RPM-GPG-KEY-redhat-release`.

2. **Writes `/etc/containers/policy.json`** — enforces `signedBy` (Red Hat GPG) for all
   `registry.access.redhat.com` pulls; rejects everything else by default.

3. **Writes `/etc/containers/registries.d/redhat.yaml`** — tells Podman where to fetch
   Red Hat image signatures (their public sigstore).

The script is idempotent and safe to re-run. To verify the setup afterwards:

```bash
podman image trust show
```

## Building

The OSO ripple-plugin image must be built on an s390x system with Podman.

### Build environment variables

| Environment Variable | Description                                            |
| -------------------- | ------------------------------------------------------ |
| `REGISTRY_URL`       | URL of your container registry (e.g., `us.icr.io`)    |
| `REGISTRY_NAMESPACE` | Container registry namespace                           |

### Building the Ripple Plugin

```bash
git clone git@github.com:IBM/dapcs-oso-plugins.git
cd dapcs-oso-plugins/ripple-plugin

export REGISTRY_URL=us.icr.io
export REGISTRY_NAMESPACE=<REGISTRY_NAMESPACE>
make build
```

`make build` calls `podman build --pull=always` which:
- Always re-fetches base images from the registry (no stale cache)
- Triggers `policy.json` signature verification on every `registry.access.redhat.com` pull
- Aborts the build if any base image fails the GPG signature check

> **Note:** After the images are successfully built, push the images into the private
> container image registry used for OSO.

### Contract Generation and Usage

Refer to the contracts [readme](../contracts/ripple/README.md) for installation of the plugin.

### Run Unit Tests

```bash
make test
```