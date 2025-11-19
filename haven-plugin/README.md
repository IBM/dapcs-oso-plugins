# dapcs-idah-oso-plugins

# Build the Plugin container image

Perform the following steps on a IBM LinuxONE system.

Clone repository https://github.com/IBM/dapcs-oso-framework and run command
```
make containerize
```
This builds the OSO framework container images locally.

Clone this repository and run command
```
make build
```

This builds the plugin container image locally. Work with the system administrator to push the image to the container registries as described in the OSO documentation and note the image tag and sha256 digest.

Further refer [contracts/README.md](contracts/README.md) to Configure Frontend and Backend Plugins.

