from fireblocks.models.modify_signing_key_dto import ModifySigningKeyDto
from fireblocks.client import Fireblocks
from fireblocks.client_configuration import ClientConfiguration
from fireblocks.base_path import BasePath
from pprint import pprint
import os

vaultid = os.environ["VAULTID"]
keyid = os.environ["FB_KEYID"]

# load the secret key content from a file
with open(os.environ["SECRET_KEY_PATH"], "r") as file:
    secret_key_value = file.read()

# build the configuration
configuration = ClientConfiguration(
    api_key=os.environ["FB_API_KEY"],
    secret_key=secret_key_value,
    base_path=BasePath.US,
)

# Enter a context with an instance of the API client
with Fireblocks(configuration) as fireblocks:
    try:
        update_signing_key_dto = ModifySigningKeyDto(vaultAccountId=int(vaultid))
        api_response = fireblocks.key_link_beta.update_signing_key(
            key_id=keyid, modify_signing_key_dto=update_signing_key_dto
        ).result()
        print("The response of KeyLinkBetaApi->update_signing_key:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling KeyLinkBetaApi->update_signing_key: %s\n" % e)
