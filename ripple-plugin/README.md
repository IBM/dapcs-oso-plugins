# Offline Signing Orchestrator - Ripple Custody Plugin

The plugin provided within this repository contains the code required to integrate Ripple Custody with the Offline Signing Orchestrator (OSO). Additional tooling is provided to generate the plugin image and to generate encrypted HPVS contracts used as workload configuration options within OSO. The Ripple Custody plugin image is expected to be built and uploaded to a private docker container image registry along with other images, accessible to all OSO LPARs.

## Prerequisites

- [Offline Signing Orchestrator](https://www.ibm.com/docs/en/hpdaoso)
- [Docker](https://www.docker.com/)


## Building
OSO ripple-plugin image is required to be built on an s390x system with Docker. See instructions below.

### Build environment variables
| Environment Variable  | Description                                                                 |
| --------------------- | --------------------------------------------------------------------------- |
| REGISTRY_URL          | URL of your container registry (e.g., us.icr.io). |
| REGISTRY_NAMESPACE    | Container registry namespace |

### Building Ripple Plugin


```
git clone git@github.com:IBM/dapcs-oso-plugins.git
cd dapcs-oso-plugins/ripple-plugin

export REGISTRY_URL=us.icr.io
export REGISTRY_NAMESPACE=<REGISTRY_NAMESPACE>
make build
```
**Note: After the images are successfully built, push the images into the private docker container image registry used for OSO**

### Contract Generation and Usage
Refer to the contracts [readme](../contracts/ripple/README.md) for installation of the plugin.

### Run unit tests
make test
