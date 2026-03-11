# Offline Signing Orchestrator Fireblocks Plugins

## Verify the Offline Signing Orchestrator Plugin image

### Prerequisites
- The supporting infrastructure containing syslog/registry/etc across LPAR1-LPAR3.

## Frontend Plugin
The Offline Signing Orchestrator frontend plugin performs import or export operations to or from the Fireblocks API Gateway which is accessible from LPAR1 (hot).

### Prerequisites
- The supporting infrastructure containing syslog/registry/etc across LPAR1-LPAR3.
- Download OpenTofu and the required terraform providers (hpcr and local) from the Offline Signing Orchestrator release archive.

### Create a agent API user for the OSO frontend

Prereq: A Fireblocks Keylink workspace where you have administrator permissions

1. Create a secret private key and CSR for the to be created agent API user. To do so, follow the  [Fireblocks documentation](https://developers.fireblocks.com/reference/quickstart#step-1-generate-a-csr-file) under `Step 1: Generate a CSR file` and run the following command:
   - `openssl req -new -newkey rsa:4096 -nodes -keyout fireblocks_secret.key -out fireblocks.csr -subj '/O=<your_organization>'`
   - This command will create two files: `fireblocks_secret.key` containing the secret key and `fireblocks.csr` containing the CSR

1. Log in to the Fireblocks Console to create an agent API user. To do so, follow the [Fireblocks documentation](https://developers.fireblocks.com/reference/quickstart#step-1-generate-a-csr-file) `Step 2: Create the API user` and:
    - Select `Signer` role
    - Provide the previously created CSR
    - Ensure in the `Co-signer setup` field option `Fireblocks Agent` is selected

1. Wait until user creation is approved.

1. Login to the Fireblocks Console, open the [Users list](https://console.fireblocks.io/v2/settings/users), find the previously created agent API user, make sure the user is in status `Pending setup` and retrieve the API key (via the small key symbol next to the user name) and the pairing token for the agent user (by clicking on the `Pending setup` status message). Keep both the API key and the pairing token.

1. Create the refresh token for the agent user. This step needs to be performed by a developer or a user who has a node.js/npm development or test environment. To do so
    - Install a CLI tool to decode JWT tokens, e.g. `npm install -g jwt-cli`
    - Run the CLI tool to decode the pairing token, e.g. `jwt <pairingtoken> --output=json`. This will display the decoded token in form of a json document like e.g.
```
{
  "header": {
    "typ": "JWT",
    "alg": "HS256"
  },
  "payload": {
    "iat": redacted-timestamp,
    "exp": redacted-timestamp,
    "tenantId": "redacted",
    "tenantName": "redacted",
    "type": "devicePairing",
    "userId": "redacted"
  },
  "signature": "redacted",
  "input": "redacted-base64-encoded-string"
}
```

6. Retrieve the refresh token
    - Copy and save the `userId` value from the JSON document
    - Prepare and run the following command:
      - `curl --url https://mobile-api.fireblocks.io/pair_device --header 'Content-Type: application/json' --data '{ "userId": "<userId>", "pairingToken": "<pairingToken>"}'`
    - Save the JSON document returned/displayed by this command. The document looks like e.g.
      - `{"refreshToken":"redacted-hex","initialConfiguration":{"twoFAtype":"BIOMETRIC"},"deviceId":"redacted-uuid"}`
    - Review, and if required edit this JSON document: Add missing properties (e.g. `userID`) and remove surplus properties (e.g. `initialConfiguration`). Below is the required final JSON structure:
       - `{"refreshToken":"<hex>","deviceId":"<uuid>","userId":"<uuid>"}`
    - Base64 encode the JSON document
       - run command `echo '{"refreshToken":"<redacted-hex>","deviceId":"<redacted-uuid>","userId":"<redacted-uuid>"}' | base64 -w0`
       - and save the output
    - In the Fireblocks Console, ensure the agent user is now displayed in state `Active`.


### Generate encrypted workload
OSO uses the encrypted workload to deploy the frontend (LPAR1) components during the `init` process.  Change to the `frontend` directory, and complete the following steps:

1. Copy the terraform template.

    `cp terraform.tfvars.template terraform.tfvars`
1. Edit the `terraform.tfvars` file and assign values to the following terraform variables:
    - `FRONTEND_PLUGIN_IMAGE` - Frontend plugin image with sha256 digest
    - `FIREBLOCKS_AGENT_IMAGE` - Fireblocks agent image with sha256 digest
    - `MOBILE_GATEWAY_URL` - Mobile gateway url endpoint (default: https://mobile-api.fireblocks.io)
    - `REFRESH_TOKEN` - Refresh token for the API user (base64 encoded JSON as described above)
1. To generate the encrypted workload, change to the `contracts` directory and run:

    `./create-frontend.sh`

## Backend

### Prerequisites
- The supporting infrastructure containing syslog/registry/etc across LPAR1-LPAR3.
- Download OpenTofu and the required terraform providers (hpcr, tls, and local) from the Offline Signing Orchestrator release archive.
- A configured Crypto appliance accessible from HiperSocket34 network on LPAR3.
- (Optional) Client certificates for a GREP11 instance deployed outside the backend pod.

### Generate encrypted workload
The encrypted workload will be used within OSO when deploying along with the GREP11 services during a signing iteration process on LPAR3. Change to the `backend` directory and perform the following steps:
1. Copy the terraform template

    `cp terraform.tfvars.template terraform.tfvars`
1. Edit the `terraform.tfvars` file and assign values to the following terraform variables:
    - `PREFIX` - Prefix used for OSO deployment
    - `BACKEND_PLUGIN_IMAGE` - Backend plugin image with sha256 (see above)
    - `WORKLOAD_VOL_SEED` - Workload volume encryption seed

#### GREP11 Configuration Options
By default, the backend deploys an internal GREP11 instance in the VM. To use an external instance instead, disable the internal deployment and provide the GREP11 client credentials.

##### Internal GREP11 (Default)
GREP11 will be running in the backend VM and will be communicated to over localhost.

###### Copy grep11-c16 image to registry
Download the grep11-c16 image, copy it to the private registry, and obtain the sha256 of the image.  See the [IBM Hyper Protect Virtual Servers Documentation](https://www.ibm.com/docs/en/hpvs/2.1.x?topic=dcenasee-downloading-crypto-express-network-api-secure-execution-enclaves-major-release) for steps to locate and download the image.

    - `GREP11_IMAGE` - GREP11-C16 image with sha256 (see above)
    - `DOMAIN` - Crypto appliance domain
    - `C16_CA_CERT` - Crypto appliance CA certificate (certs/ca.pem)
    - `C16_CLIENT_CERT` - Crypto appliance client certificate (certs/c16client.pem)
    - `C16_CLIENT_KEY` - Crypto appliance client key (certs/c16client-key.pem)

##### External GREP11

    - `INTERNAL_GREP11` - should be set to `false`
    - `GREP11_ENDPOINT` - endpoint for GREP11 (default: `<PREFIX>-cs-backend-grep11.control23.dap.local:9876`)
    - `GREP11_CA` - GREP11 CA certificate
    - `GREP11_CLIENT_KEY` - GREP11 client key
    - `GREP11_CLIENT_CERT` - GREP11 client certificate

1. To generate the encrypted workload, change to the `contracts` directory and run:

    `./create-backend.sh`

## OSO Encrypted Workloads
Within the orchestration process, OSO requires plugin workload definitions to be encrypted. When configuring OSO, the encrypted plugin workloads are specified in the FRONTEND_WORKLOADS and BACKEND_WORKLOADS OSO variables within the OSO `terraform.tfvars` file. After generating the encrypted plugin workloads using the `create_frontend.sh` and `create_backend.sh`, obtain the values for the FRONTEND_WORKLOADS and BACKEND_WORKLOADS OSO variables by running the following command from the `contracts` directory:

### Hipersocket34
When using an external grep11 server or crypto passthrough, `hipersocket34` for the `backend-plugin` in `BACKEND_WORKLOADS` should be set to false by setting the environment variable `HIPERSOCKET34=false` when running the `get_workloads.sh` script.

`./get_workloads.sh`

Note: update the `env_seed` and `volume_path` within the backend workload section.

## Signing Key Registration Process

Before deploying workloads with OSO, you must register the signing keys manually. The process requires running an empty signing iteration with OSO.

### Prerequisites
- Supporting infrastructure containing syslog/registry/etc across LPAR1-LPAR3 with hipersocket networks defined.
- Conductor fully deployed and initialized with the required frontend/backend workloads.

### Bootstrap Backend
1. Login to LPAR3 (temporarily attach a network if required to access LPAR3 as part of the setup process)
1. Create an empty fb-vault-data.qcow2 image:

    `sudo qemu-img create -f qcow2 /var/lib/libvirt/images/oso/fb-vault-data.qcow2 10G`
1. Ensure the qcow2 has the correct libvirt read/write ownership
1. Refresh the pool:

    `virsh pool-refresh --pool images`
1. After deploying the Conductor and initializing the frontend components, run an empty signing iteration:

    `oso_cli.py <prefix> operator --cert <admin-cert> --key <admin-key> --cacert <cacert> run --allow_empty`
1. Monitor the startup logs of the signing server and search for the public keys for both the `ECDSA_SECP256K1` and `EDDSA_ED25519` created keys. Copy and store the key id and the public signing keys. Example:
    ```
    INFO:fb.plugin:Key Type: 'SECP256K1', Key ID: '...', Public Key PEM: '-----BEGIN PUBLIC KEY-----...-----END PUBLIC KEY-----'

    INFO:fb.plugin:Key Type: 'ED25519', Key ID: '...', Public Key PEM: '-----BEGIN PUBLIC KEY-----...-----END PUBLIC KEY-----'
    ```
1. OSO iteration should complete successfully
1. Take a backup of volume `fb-vault-data.qcow2`. For disaster recovery planning purposes, this volume is critical and would need to be restored in order to resume signing operations.

### Create a validation key
You need to create at least one validation key. To do so
- Use openssl to create a RSA validation key pair:
  - `openssl genrsa -out validationkey.pem 2048`
  - `openssl rsa -in validationkey.pem -out validationpubkey.pem -outform PEM -pubout`
- Follow the [fireblocks documentation](https://support.fireblocks.io/hc/en-us/articles/23115386650780-Managing-keys-with-the-Key-Management-Dashboard) step `Adding a validation key` to add one validation key

### Add signing keys
- Find the key id and the public key PEM of the ECDSA key and the EDDSA key that were created during by the OSO backend plugin during the previous "Bootstrap Backend" step. 
- Determine which of the two signing keys you need to add to the Fireblocks workspace. You may add one or two signing keys. 
- For each signing keys, follow the Fireblocks documentation](https://support.fireblocks.io/hc/en-us/articles/23115386650780-Managing-keys-with-the-Key-Management-Dashboard) step `Adding a signing key` to add the signing key. In the UI dialog, select the API agent user created in one of the previous steps, and provide the key id (in field `Signing device ID`) and the public key PEM of the signing key in the Fireblocks UI. 
- Run a signing iteration with OSO to complete the interactive proof of ownership for the signing key. (Fireblocks will create two `KEY_LINK_PROOF_OF_OWNERSHIP_REQUEST` messages to be signed by the backend. After these message are signed and received by Fireblocks, the keys can be linked to a Vault account.)

### Link the signing key to a vault
- In Fireblocks Console, create a new Vault and note the Vault ID (e.g. from the URL). You can either have the previously created signing key automatically be linked to your new vault, or you can run the following steps:
- Download the example code https://github.com/fireblocks/py-sdk/blob/master/docs/KeyLinkBetaApi.md#update_signing_key  to the cloned directory
- Adapt the downloaded example code [update_signing_key.py]
  - Add the user ID of the agent user
  - Add the path of the file containing said secret private key for your agent user
  - Add the API key of your agent user
  - Add the path of the file containing the private validation key in pem format
  - Add the key id of the signing key
  - Add the vault id
- Run `python update_signing_key.py`
- The signing key is now linked to the vault account.
