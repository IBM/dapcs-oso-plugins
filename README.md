# Offline Signing Orchestrator — Plugins

This repository contains plugins that integrate third-party custody systems with
the [IBM Digital Asset Offline Signing Orchestrator (OSO)](https://www.ibm.com/docs/en/hpdaoso).

Each plugin directory produces a container image that is included in an
[IBM Confidential Computing Container Runtime (CCRT)](https://www.ibm.com/docs/en/ccrt/2.2.x)
encrypted workload contract. Images must be pushed to a private container registry
accessible to all OSO LPARs. The Terraform scripts used to generate those CCRT
contracts live under [`/contracts`](./contracts).

## Repository structure

| Path | Purpose |
|------|---------|
| [`/fireblocks-plugin`](./fireblocks-plugin) | Plugin source code for the Fireblocks integration |
| [`/ripple-plugin`](./ripple-plugin) | Plugin source code for the Ripple Custody integration |
| [`/contracts/fireblocks`](./contracts/fireblocks) | Terraform scripts to generate CCRT contracts for Fireblocks |
| [`/contracts/ripple`](./contracts/ripple) | Terraform scripts to generate CCRT contracts for Ripple Custody |

## Plugins

### Fireblocks

Integrates OSO with Fireblocks.

- Plugin source: [`/fireblocks-plugin`](./fireblocks-plugin/README.md)
- Contract configuration: [`/contracts/fireblocks`](./contracts/fireblocks/README.md)

### Ripple Custody

Integrates OSO with Ripple Custody.

- Plugin source: [`/ripple-plugin`](./ripple-plugin/README.md)
- Contract configuration: [`/contracts/ripple`](./contracts/ripple/README.md)

## Prerequisites

Common to both plugins:

- [IBM Digital Asset Offline Signing Orchestrator](https://www.ibm.com/docs/en/hpdaoso)
- An `s390x` build host with [Docker](https://www.docker.com/) to build the container images
- A private container registry accessible to all OSO LPARs

## Development

Pre-commit hooks are configured for the whole repository via [`.pre-commit-config.yaml`](.pre-commit-config.yaml).
They enforce secret scanning, YAML linting, commit-message conventions (Commitizen), and Python
linting/formatting (Ruff).

Install the hooks once after cloning:

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install pre-commit globally via uv
uv tool install pre-commit

# Register the git hooks
pre-commit install
```

See the individual plugin READMEs for plugin-specific development setup and test commands.

## License

[Apache-2.0](./LICENSE)
