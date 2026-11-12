# Offline Signing Orchestrator - Ripple Custody Plugin

The plugin provided within this repository contains the code required to integrate Ripple Custody with the Offline Signing Orchestrator (OSO). Additional tooling is provided to generate the plugin image and to generate encrypted IBM Confidential Computing Container Runtime (CCRT) contracts used as workload configuration options within OSO. The Ripple Custody plugin image is expected to be built and uploaded to a private container registry along with other images, accessible to all OSO LPARs.

## Compatibility

The plugin has been tested with the following versions:

| Component                    | Version                          |
| ---------------------------- | -------------------------------- |
| Offline Signing Orchestrator | 1.4.1.4+, 1.5.1+                 |
| Ripple Custody (Harmonize)   | 1.34                             |

Ripple images used:

| Image             | Version |
| ----------------- | ------- |
| vault-releases    | 1.32.13 |
| vault-cold-bridge | 1.32.13 |
| kms-ibm           | 1.13.17 |

## Prerequisites

- [Offline Signing Orchestrator](https://www.ibm.com/docs/en/hpdaoso)
- [Docker](https://www.docker.com/)

## Building
The OSO ripple-plugin image is required to be built on an s390x system with Docker. A sample `Dockerfile` is provided to build the plugin container image.

### Build variables
| Variable    | Default       | Description                    |
| ----------- | ------------- | ------------------------------ |
| `REGISTRY`  | `us.icr.io`   | URL of your container registry |
| `NAMESPACE` | `dap-osc-dev` | Container registry namespace   |
| `TAG`       | `latest`      | Image tag                      |

### Building Ripple Plugin
```
git clone https://github.com/IBM/dapcs-oso-plugins.git
cd dapcs-oso-plugins/ripple-plugin
export REGISTRY_URL=us.icr.io
export REGISTRY_NAMESPACE=<REGISTRY_NAMESPACE>
make build
```
The image is built as `oso-ripple-plugins` and tagged `<REGISTRY>/<NAMESPACE>/oso-ripple-plugins:<TAG>`.

**Note: After the image is successfully built, push it to the private container registry used for OSO.**

## Contract Generation and Usage
Refer to the contracts [readme](../contracts/ripple/README.md) for installation of the plugin.

## Development

### Run unit tests
```
make test
```
