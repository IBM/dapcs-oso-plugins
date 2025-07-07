# Offline Signing Orchestrator - Plugins
This repository contains plugins used to integrate third-party systems with the Offline Signing Orchestrator (OSO). Plugin directories located at the project root are used to build a Docker image that is included in an HPVS contract. This image must be pushed to a private Docker container registry accessible to all OSO LPARs. The Terraform scripts used to generate the HPVS contracts provided to OSO are located in the /contracts directory.

## Plugins

### Fireblocks
Plugin code: `/fireblocks-plugins`
Contract configuration: `/contracts/fireblocks`

## License
[Apache-2.0](./LICENSE)
