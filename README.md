# Offline Signing Orchestrator - Fireblocks Plugin

The plugin provided within this repository contains the code required to integrate Fireblocks with the Offline Signing Orchestrator (OSO). Additional tooling is provided to generate the plugin image and to generate encrypted HPVS contracts used as workload configuration options within OSO. An additional image will be required to be supplied via [fireblocks-agent](https://github.com/fireblocks/fireblocks-agent) which is used to communicate with the Fireblocks API Gateway. This plugin and fireblocks-agent images are expected to be built and uploaded to a private docker container image registry, accessible to all OSO LPARs (ex. registry23.control.dap.local).

## Prerequisites

- [Offline Signing Orchestrator v1.4.0 or above](https://www.ibm.com/docs/en/hpdaoso/1.4.x)
- [Offline Signing Orchestrator Plugin Framework v1.0.0](https://github.com/ibm/dapcs-oso-framework)
- [Fireblocks Agent](https://github.com/fireblocks/fireblocks-agent)
- [Podman](https://podman.io/)

## Building
The fireblocks-agent and dapcs-fireblocks-oso-plugins images are required to be built on an s390x system with Podman. See instructions below.

### Building Fireblocks Plugin
```
git clone git@github.com:ibm/dapcs-oso-framework.git -b v1.0.0
cd dapcs-oso-framework
make containerize
cd ..

git clone git@github.com:ibm/dapcs-fireblocks-oso-plugins.git -b v1.0.0
cd dapcs-fireblocks-oso-plugins/fireblocks-plugin
make build
```

### Building Fireblocks Agent
```
git clone https://github.com/fireblocks/fireblocks-agent.git
cd fireblocks-agent
podman build . -t fireblocks-agent:latest 
```

**Note: After the images are successfully built, push the images into the private docker container image registry used for OSO**

## Contract Generation and Usage
Refer to the contracts [readme](./contracts/README.md) for installation of the plugin.

## License
[Apache-2.0](./LICENSE)
