# Offline Signing Orchestrator - Fireblocks Plugin

The plugin provided within this repository contains the code required to integrate Fireblocks with the Offline Signing Orchestrator (OSO). Additional tooling is provided to generate the plugin image and to generate encrypted HPVS contracts used as workload configuration options within OSO. An additional image will be required to be supplied via [fireblocks-agent](https://github.com/fireblocks/fireblocks-agent) which is used to communicate with the Fireblocks API Gateway. This plugin and fireblocks-agent images are expected to be built and uploaded to a private docker container image registry, accessible to all OSO LPARs (ex. registry23.control.dap.local).

## Prerequisites

- [Offline Signing Orchestrator v1.3.2 or above](https://www.ibm.com/docs/en/hpdaoso/1.3.0)
- [Offline Signing Orchestrator Plugin Framework v1.0.0](https://github.com/ibm/dapcs-oso-framework)
- [Fireblocks Agent](https://github.com/fireblocks/fireblocks-agent)
- [Docker](https://www.docker.com/)

## Building
The fireblocks-agent and OSO fireblocks-plugin images are required to be built on an s390x system with Docker. See instructions below.

### Building Fireblocks Plugin
```
git clone git@github.com:IBM/dapcs-oso-framework.git
cd dapcs-oso-framework
make containerize
cd ..

git clone git@github.com:IBM/dapcs-oso-plugins.git
cd dapcs-oso-plugins/fireblocks-plugin
make build
```

### Building Fireblocks Agent
```
docker build -t fireblocks-agent:latest https://github.com/fireblocks/fireblocks-agent.git
```

**Note: After the images are successfully built, push the images into the private docker container image registry used for OSO**

## Contract Generation and Usage
Refer to the contracts [readme](./contracts/fireblocks/README.md) for installation of the plugin.

## Development

### Global
Please run the following commands to setup uv and pre-commit hooks

```
# 1. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install pre-commit into the uv-managed global environment
uv tool install pre-commit

# 3. Install git hooks
pre-commit install
```

### fireblocks-plugin
To work on the `fireblocks-plugin`, cd into the `fireblocks-plugin` dir and run
```
uv sync --all-extras
```

And to run tests
```
uv run pytest
```

To run linting and formatting
```
uv run ruff check
uv run ruff format
```
