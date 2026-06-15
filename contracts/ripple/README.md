# Offline Signing Orchestrator Ripple Custody Plugins

## Overview
This function provides the integration of IBM Hyper Protect Offline Signing Orchestrator with the Ripple Custody product for the purposes of reviewing, approving, and automating the cold signing process of digital transactions originating in Ripple Custody.  For more information, please see the [IBM Hyper Protect Offline Signing Orchestrator product documentation](https://www.ibm.com/docs/en/hpdaoso).

## Verify the Offline Signing Orchestrator Plugin image

### Prerequisites
- The supporting infrastructure containing syslog/registry/etc across LPAR1-LPAR3.

## Frontend Plugin
The Offline Signing Orchestrator frontend plugin performs import or export operations to or from the Ripple Custody core which is accessible from LPAR1 (hot).

### Prerequisites
- The supporting infrastructure containing syslog/registry/etc across LPAR1-LPAR3 with hipersocket networks defined.
- To retrieve operations in JSON format, you must have an empty passphrase.
- Download OpenTofu and the required terraform providers (hpcr and local) from the Offline Signing Orchestrator release archive.
- SHA256 hash of the Ripple Custody plugin image within the private registry (see [ripple readme](../../ripple-plugin/README.md) for instructions on how to build and copy the image to the private registry)

### Create a functional OSO user
Using the Ripple Custody UI, create a functional user specifically for OSO. The user will be used to perform import or export operations to and from Ripple Custody.

1. Generate a private key for the functional user by executing one of the following commands based on the elliptic curve algorithm required.
    1. Generate a key using secp256k1 elliptic curve.

    `openssl ecparam -genkey -name secp256k1 -noout -out privateKey.pem`

    2. Generate a key using secp256r1 elliptic curve.

    `openssl ecparam -genkey -name secp256r1 -noout -out privateKey.pem`

    3. Generate a key using ED25519 elliptic curve.

    `openssl genpkey -algorithm Ed25519 -out privateKey.pem`

1. Generate a public key from the previously generated private key.

    `openssl ec -in privateKey.pem -pubout -outform DER | openssl base64 -A -out publicKey.pem`

1. In the Ripple Custody UI, create a functional user with the user public key. Use the `publicKey.pem` for the public key content.
1. Obtain the base64 value used for the `SK` terraform variable within the contract.

    `cat privateKey.pem | base64 -w0`

### Generate encrypted workload
OSO uses the encrypted workload to deploy the frontend (LPAR1) components during the `init` process.  Change to the `frontend_plugin` directory, and complete the following steps:

1. Copy the terraform template.

    `cp terraform.tfvars.template terraform.tfvars`
1. Edit the `terraform.tfvars` file and assign values to the following terraform variables:
    - `HMZ_AUTH_HOSTNAME` - Ripple Custody frontend auth hostname
    - `HMZ_API_HOSTNAME` - Ripple Custody frontend api hostname
    - `VAULT_ID` - Vault ID used for cold vault operations. If you are using a new vault, then generate a new uuid.
    - `SK` - Base64 private key for OSO functional user account
    - `FRONTEND_PLUGIN_IMAGE` - Frontend plugin image with sha256
    - `SEED` - Passphrase used to optionally encrypt the data being transferred between OSO and Ripple Custody. The passphrase must match with the backend.
    - `TOKEN_EXP` - Expiration time configured in Ripple Custody for the bearer token returned upon authentication
1. To generate the encrypted workload, change to the `contracts/ripple` directory and run:

    `./create-frontend.sh`

## Backend

### Prerequisites
- Supporting infrastructure deployed containing syslog/registry/etc across LPAR1-LPAR3 with hipersocket networks defined.
- Download OpenTofu and the required terraform providers (hpcr, null and local) from the Offline Signing Orchestrator release archive.
- Build the Ripple Custody plugin image [by following the doc](../../ripple-plugin/README.md), copy it to the private registry, and obtain the sha256 hash of the image.
- SHA256 hash of the Ripple Custody plugin image within the private registry (see [ripple readme](../../ripple-plugin/README.md) for instructions on how to build and copy the image to the private registry)

### Copy cold bridge, cold vault and kmsconnect images to registry
Obtain the cold bridge, cold vault, and kmsconnect images from Ripple and copy them to the private registry. Obtain the sha256 hashes for each of the images.

### Generate encrypted workload
The encrypted workload will be used within OSO when deploying along with the GREP11 services during a signing iteration process on LPAR3. Change to the `contracts/ripple/backend` directory and perform the following steps:
1. Copy the terraform template

    `cp terraform.tfvars.template terraform.tfvars`
2. Edit the `terraform.tfvars` file and assign values to the following terraform variables:
    - `PREFIX` - Prefix used for OSO deployment
    - `STATIC_IP` - true for releases OSO 1.4 and higher where static IP addresses are used, otherwise set to false
    - `BACKEND_PLUGIN_IMAGE` - Backend plugin image with sha256 (see above)
    - `SEED` - Passphrase used to optionally encrypt the data being transferred between OSO and Ripple Custody (matches frontend)
    - `COLD_BRIDGE_IMAGE` - Cold bridge image with sha256 (see above)
    - `COLD_VAULT_IMAGE` - Cold vault image with sha256 (see above)
    - `KMSCONNECT_IMAGE` - KMS connect image with sha256 (see above)
    - `VAULT_ID` - Vault ID used for cold vault operations
    - `NOTARY_MESSAGING_PUBLIC_KEY` - Notary messaging public key after genesis
    - `WORKLOAD_VOL_SEED` - Workload volume encryption seed
    - `CRYPTO_PASSTHROUGH_ENABLEMENT` - To enable crypto passthrough
    - `INTERNAL_GREP11` - boolean value for to bringup grep11 interanally or externally
    - `GREP11_IMAGE` - grep11 image with with sha256
    - `DOMAIN` - Domain id.

    below grep11 certs are optional, when `INTERNAL_GREP11` is true
    - `GREP11_CA` - GREP11 CA certificate
    - `GREP11_CLIENT_KEY` - GREP11 client key
    - `GREP11_CLIENT_CERT` - GREP11 client certificate

    below c16 certs are optional, when `CRYPTO_PASSTHROUGH_ENABLEMENT` is true
    - `C16_CA_CERT` - Crypto appliance CA certificate (certs/ca.pem)
    - `C16_CLIENT_CERT` - Crypto appliance client certificate (certs/c16client.pem)
    - `C16_CLIENT_KEY` - Crypto appliance client key (certs/c16client-key.pem)
    - `C16_CLIENT_HOST` - Crypto appliance host IP address - only set if default value (192.168.128.4) is not correct

3. To generate the encrypted workload, change to the `contracts/ripple` directory and run:

    `./create-backend.sh`

## OSO Ripple Custody Encrypted Workloads
Within the orchestration process, OSO requires plugin workload definitions to be encrypted. When configuring OSO, the encrypted plugin workloads are specified in the FRONTEND_WORKLOADS and BACKEND_WORKLOADS OSO variables within the OSO `terraform.tfvars` file. After generating the encrypted plugin workloads using the `create_frontend.sh`and `create_backend.sh` scripts, obtain the values for the FRONTEND_WORKLOADS and BACKEND_WORKLOADS OSO variables by running the following command from the `contracts/ripple` directory:

`./get_workloads.sh`

Note: update the env_seed within the backend workload section.

## Cold Vault Registration Process
Before deploying workloads with OSO, you must register the cold vault manually. The process requires running an empty signing iteration with OSO.

### Prerequisites
- Supporting infrastructure containing syslog/registry/etc across LPAR1-LPAR3 with hipersocket networks defined.
- Conductor fully deployed and initialized with the required frontend/backend workloads

### Bootstrap Cold Vault
1. Login to LPAR3
1. Create an empty vault-data.qcow2 image:

    `sudo qemu-img create -f qcow2 /var/lib/libvirt/images/oso/vault-data.qcow2 10G`
1. Ensure the qcow2 has the correct libvirt read/write ownership
1. Refresh the pool:

    `virsh pool-refresh --pool images`
1. After deploying the Conductor and initializing the frontend components, run an empty signing iteration:

    `oso_cli.py <prefix> operator --cert <admin-cert> --key <admin-key> --cacert <cacert> run --allow_empty`
1. Monitor the startup logs of the cold vault and search for the der base64 public key signature (pubKeySig) and signed payload (signedPayload). Example:
    ```
    [INFO] [] [InitSvc]: Vault Core pubKeySig (hex): 926986b0d930e9b8d7451023712cf8390bb367af5b0ca328c4d99281a0226d37
    [INFO] [] [InitSvc]: Vault Core pubKeySig (der base64): MCowBQYDK2VwAyEAkmmGsNkw6bjXRRAjcSz4OQuzZ69bDKMoxNmSgaAibTc=
    [INFO] [] [InitSvc]: Response: {
        "signedPayload": "CqkHC..."
    }
    ```
1. OSO iteration should complete successfully
1. Take a backup of volume `vault-data.qcow2`. For disaster recovery planning purposes, this volume is critical and would need to be restored in order to resume signing operations.

### Vault Creation
1. Within the Ripple Custody UI, create a new vault with the der base64 public key signature obtained above and the vault id specified within the contracts.
1. The vault should show the activation status as `Pending`.

### Vault Registration
1. Using the vault id and signed payload (signedPayload) from above, create a `reg.dat` file containing:
    ```
    {
        "accounts": [],
        "transactions": [],
        "manifests": [],
        "vaults": [
            {
                "vaultId": "vault-id",
                "signedPayload": "CtMHC..."
            }
        ]
    }
    ```
1. Import the `reg.dat` into the cold vault pending operations through the Ripple Custody UI.
1. Once successfully imported, the vault activation status shows `Completed`.
1. New accounts created for the new cold vault will need to be approved through the OSO signing process.
