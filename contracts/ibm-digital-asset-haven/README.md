# IBM Digital Asset Haven OSO Plugins

## Prerequisites

### Terraform providers
- Execute command `sudo tar -xvf terraform-provider.tar -C /` to install the terraform providers.

### Steps to Generate Certificate Signing Request
The following steps show how to generate a Certificate Signing Request (CSR) to send to IBM Support to enable the HSM Signer to communicate with the IBM Digital Asset Haven's HSM Proxy. A script is provided to demonstrate how to generate the necessary keys and certificate signing request.
- Export required environment variables (as shown by example):
```
    export COUNTRY_CODE=DE
    export STATE=BW
    export LOCALITY=city
    export ORGANIZATION=org
    export ORGANIZATION_UNIT=unit
    export EMAIL_ADDRESS=someone@email.com
```
- Run below command to generate the private key and CSR.
```
    ./csr/generate-csr.sh --client-id=<client-id> --hsm-id=<hsm-id> [--cluster-id=<cluster-id>] [--priv-key=<private-key-path>]
```

An HSM cluster refers to a group of Hardware Security Modules (HSMs) working together to provide cryptographic services in a secure and highly available way.
    - <client-id> - This refers to a unique identifier provided by IBM Support during onboarding.
    - <hsm-id> - The unique identifier for the HSM instance in the cluster.
    - <cluster-id> - The unique identifier for the Cluster instance. Wallets can be associated to a cluster (one or more) of HSM. This parameter is optional.
    - <private-key-path> - The path to the private key to use for signing the CSR. If not provided, a new key will be generated.
- Run below command to get LPAR IP.
```
    curl ifconfig.me
```
- Reach out to IBM Support for below. IBM Support link: https://www.ibm.com/mysupport/s/createrecord/NewCase
    - Request to onboard an HSM Signer to obtain the client ID
    - Provide generated CSR to IBM support for signing
    - Provide LPAR IP address to IBM support for whitelisting
    - IBM Support will provide Signed client and CA certificate
    - IBM Support will whitelist your LPAR IP address
- Copy Signed client certificate to `contracts\frontend\frontend\tls\client.cert.pem` and CA certificate to `contracts\frontend\frontend\tls\ca.cert.pem`
- Copy the generated private key to `contracts\frontend\frontend\tls\client.key.pem`

# Configure the Frontend Plugin
The Offline Signing Orchestrator frontend plugin performs import or export operations to or from the HSM Proxy which is accessible from LPAR1.

## Generate encrypted workload
OSO uses the encrypted workload to deploy the frontend (LPAR1) components during the init process. Change to the `frontend` directory, and complete the following steps:

1. Copy the terraform template.
```
cp terraform.tfvars.template terraform.tfvars
```

2. In `contracts\frontend\frontend.yml.tftpl` adapt the environment variable values according to your certificates and private key: 
```
       - "--ca-cert"
        - "/tls/ca.cert.pem"
        - "--client-cert"
        - "/tls/client.cert.pem"
        - "--client-key"
        - "/tls/client-key.pem"     
```

3. Edit the terraform.tfvars file and assign values to the following terraform variables:
- `FRONTEND_PLUGIN_IMAGE` -  Plugin image with sha256 digest
- `HSMDRIVER_IMAGE` - HSM Driver image with sha256 digest
- `HPCR_CERT` - Certificate value of HPVS Image (optional)

4. To generate the encrypted workload, change to the contracts directory and run:
```
./create-frontend.sh
```

5. The script prints the resulting `FRONTEND_WORKLOADS` section comprising the encrypted frontend workload contract section. This can be passed to the system administrator persona to be used to continue with the OSO setup.

# Configure the Backend Plugin

## Generate encrypted workload
The encrypted workload will be used within OSO when deploying the backend during a signing iteration process on LPAR3. Change to the `backend` directory and perform the following steps:

1. Copy the terraform template
    `cp terraform.tfvars.template terraform.tfvars`
2. Edit the `terraform.tfvars` file and assign values to the following terraform variables:
    - `PREFIX` - Prefix used for OSO deployment
    - `BACKEND_PLUGIN_IMAGE` - Plugin image with sha256 (see above)
    - `HSMDRIVER_IMAGE` - HSM Driver image with sha256 digest
    - `WORKLOAD_VOL_SEED` - The Workload volume encryption seed (important: see Note below)
    - `WORKLOAD_VOLUME_PREV_SEED` - Change the Workload volume prev encryption seed.
    - `USER_PIN` - The PKCS11 normal user PIN
    - `SO_PIN` - The PKCS11 SO PIN
    - `HPCR_CERT` - Certificate value of HPVS Image (optional)

3. To generate the encrypted workload, change to the `contracts` directory and run:

    `./create-backend.sh`
4. The script prints the resulting `BACKEND_WORKLOADS` section comprising the encrypted backend workload contract section. This can be passed to the system administrator persona to be used to continue with the OSO setup.

Note: You must keep safe and securely backup the workload seed and must ensure to not loose nor forget nor leak the workload seed.


# Note: Using the frontend and backend encrypted workload contract sections to set up the OSO environment
The system administrator follows the [instructions in the OSO documentation](https://www.ibm.com/docs/en/hpdaoso/1.4.1?topic=setting-up-environment) to continue with setting up OSO and configuring the contracts. In doing so, the system administrator 
- uses the `FRONTEND_WORKLOADS` and `BACKEND_WORKLOADS` sections as described in the documentation. 
- creates persistent volumes on LPAR 3 and reviews and adapts the persistent data definition and `volume_path` in the `BACKEND_WORKLOADS` section as required.
- reviews and adapts the `hipersocket34` setting in `BACKEND_WORKLOADS` as required: When using crypto passthrough, `hipersocket34` in `BACKEND_WORKLOADS` should be set to `false`.
- changes the environment seed `env_seed` within the backend workload section (important: see Note below)
- pushes the Plugin container image, the HSM Driver container image to the OSO container registry as described in the OSO documentation.

Note: The system administrator must keep safe and securely backup the environment seed and must ensure to not loose nor forget nor leak the environment seed.
