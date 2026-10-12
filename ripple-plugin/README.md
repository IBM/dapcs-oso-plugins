# Offline Signing Orchestrator - Ripple Custody Plugin

The plugin provided within this repository contains the code required to integrate Ripple Custody with the Offline Signing Orchestrator (OSO). Additional tooling is provided to generate the plugin image and to generate encrypted HPVS contracts used as workload configuration options within OSO. The Ripple Custody plugin image is expected to be built and uploaded to a private container image registry along with other images, accessible to all OSO LPARs.

## Prerequisites

- [Offline Signing Orchestrator](https://www.ibm.com/docs/en/hpdaoso)
- [Podman](https://podman.io/)
- `curl` and `gpg`

## Build Host Setup

Run once on each build host or CI runner before building:

```bash
cd ripple-plugin
sudo ./setup-build-host.sh
```

To verify the setup afterwards:

```bash
podman image trust show
```

## Building

The OSO ripple-plugin image must be built on an s390x system with Podman.

### Build environment variables

| Environment Variable | Description                                         |
| -------------------- | --------------------------------------------------- |
| `REGISTRY_URL`       | URL of your container registry (e.g., `us.icr.io`) |
| `REGISTRY_NAMESPACE` | Container registry namespace                        |

### Building the Ripple Plugin

```bash
git clone git@github.com:IBM/dapcs-oso-plugins.git
cd dapcs-oso-plugins/ripple-plugin

export REGISTRY_URL=us.icr.io
export REGISTRY_NAMESPACE=<REGISTRY_NAMESPACE>
make build
```

> **Note:** After the images are successfully built, push the images into the private
> container image registry used for OSO.

### Contract Generation and Usage

Refer to the contracts [readme](../contracts/ripple/README.md) for installation of the plugin.

### Run Unit Tests

```bash
make test
```
