from fireblocks.models.create_validation_key_dto import CreateValidationKeyDto
from fireblocks.client import Fireblocks
from fireblocks.client_configuration import ClientConfiguration
from fireblocks.base_path import BasePath
from pprint import pprint
import os

# load the secret key content from a file
with open(os.environ["SECRET_KEY_PATH"], "r") as file:
    secret_key_value = file.read()
    print(secret_key_value)

# build the configuration
configuration = ClientConfiguration(
    api_key=os.environ["FB_API_KEY"],
    secret_key=secret_key_value,
    base_path=BasePath.US,
)

with open(os.environ["VALIDATION_PUBLICKEY_PATH"], "r") as file:
    validation_publickey_value = file.read()
    print(validation_publickey_value)


# Enter a context with an instance of the API client
with Fireblocks(configuration) as fireblocks:
    create_validation_key_dto = CreateValidationKeyDto(
        publicKeyPem=validation_publickey_value, daysTillExpired=999
    )
    idempotency_key = "idempotency_key_0"  # str | A unique identifier for the request. If the request is sent multiple times with the same idempotency key, the server will return the same response as the first request. The idempotency key is valid for 24 hours. (optional)

    try:
        # Add a new validation key
        api_response = fireblocks.key_link_beta.create_validation_key(
            create_validation_key_dto, idempotency_key=idempotency_key
        ).result()
        print("The response of KeyLinkBetaApi->create_validation_key:\n")
        pprint(api_response)
    except Exception as e:
        print("Exception when calling KeyLinkBetaApi->create_validation_key: %s\n" % e)
