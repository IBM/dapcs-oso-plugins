from fireblocks.client import Fireblocks
from fireblocks.client_configuration import ClientConfiguration
from fireblocks.base_path import BasePath
from pprint import pprint
import os


user_id = os.environ["USERID"]

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
    """"
    page_cursor = 'MjAyMy0xMi0xMyAyMDozNjowOC4zMDI=:MTEwMA==' # str | Cursor to the next page (optional)
    page_size = 10 # float | Amount of results to return in the next page (optional) (default to 10)
    sort_by = 'createdAt' # str | Field(s) to use for sorting (optional) (default to 'createdAt')
    order = 'ASC' # str | Is the order ascending or descending (optional) (default to 'ASC')
    vault_account_id = 4 # float | Return keys assigned to a specific vault (optional)
    agent_user_id = user_id # str | Return keys associated with a specific agent user (optional)
    algorithm = 'ECDSA_SECP256K1' # str | Return only keys with a specific algorithm (optional)
    enabled = True # bool | Return keys that have been proof of ownership (optional)
    available = True # bool | Return keys that are proof of ownership but not assigned. Available filter can be used only when vaultAccountId and enabled filters are not set (optional)
    """
    try:
        # Get list of signing keys
        api_response = fireblocks.key_link_beta.get_signing_keys_list().result()  # page_cursor=page_cursor, page_size=page_size, sort_by=sort_by, order=order, vault_account_id=vault_account_id, agent_user_id=agent_user_id, algorithm=algorithm, enabled=enabled, available=available).result()
        print("The response of KeyLinkBetaApi->get_signing_keys_list:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling KeyLinkBetaApi->get_signing_keys_list: %s\n" % e)
