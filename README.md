# Offline Signing Orchestrator - Plugins
This repository contains plugins used to integrate third-party systems with the Offline Signing Orchestrator (OSO). Plugin directories located at the project root are used to build a Docker image that is included in an HPVS contract. This image must be pushed to a private Docker container registry accessible to all OSO LPARs. The Terraform scripts used to generate the HPVS contracts provided to OSO are located in the /contracts directory.

## Plugins

### Fireblocks
Plugin code: [/fireblocks-plugin/](./fireblocks-plugin)

Contract configuration: [/contracts/fireblocks/](./contracts/fireblocks)

### Ripple Custody
Plugin code: [/ripple-plugin/](./ripple-plugin)

Contract configuration: [/contracts/ripple/](./contracts/ripple)

### IBM Digital Asset Haven
Plugin code: [/ibm-digital-asset-haven-plugin/](./ibm-digital-asset-haven-plugin)

Contract configuration: [/contracts/ibm-digital-asset-haven/](./contracts/ibm-digital-asset-haven)

## License
[Apache-2.0](./LICENSE)
