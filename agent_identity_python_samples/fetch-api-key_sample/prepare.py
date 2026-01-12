import json
import logging

from agent_identity_python_sdk.core import IdentityClient
from agent_identity_python_sdk.core.decorators import get_region
from agent_identity_python_sdk.utils.config import write_local_config
from alibabacloud_agentidentity20250901.models import (
    CreateAPIKeyCredentialProviderRequest,
)

from alibabacloud_tea_openapi.exceptions import ClientException
from alibabacloud_credentials.client import Client as CredentialClient

REGION = get_region()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_KEY_CREDENTIAL_PROVIDER_NAME = 'test-for-api-key-sample'

# Initialize clients
client = IdentityClient(REGION)
credential = CredentialClient()

def create_api_key_provider(api_key: str) -> str:
    """
    Create API key provider
    
    Returns:
        API key credential provider name
    """
    try:
        response = client.control_client.create_apikey_credential_provider(
            CreateAPIKeyCredentialProviderRequest(
                apikey_credential_provider_name=API_KEY_CREDENTIAL_PROVIDER_NAME,
                description='This is a test API key provider.',
                apikey=api_key
            )
        )
        logger.info(f'API key credential provider: {response.body.apikey_credential_provider.apikey_credential_provider_name} created.')
        return response.body.apikey_credential_provider.apikey_credential_provider_name
    except ClientException as error:
        if error.code == 'EntityAlreadyExists.APIKeyCredentialProvider':
            logger.warning('[409] APIKeyCredentialProvider already exists, skip creating.')
            return API_KEY_CREDENTIAL_PROVIDER_NAME
        else:
            raise


if __name__ == '__main__':
    import sys
    import getopt
    
    api_key = "mock"
    
    opts, args = getopt.getopt(sys.argv[1:], "", ["api-key="])
    
    for opt, arg in opts:
        if opt in ("--api-key"):
            api_key = arg

    api_key_provider_name = create_api_key_provider(api_key)

    # Output structured JSON summary
    write_local_config('api_key_provider_name', api_key_provider_name)

    logger.info("Resources Summary:")
    summary = {
        "credential_providers": {
            "api_key": api_key_provider_name
        }
    }
    logger.info(json.dumps(summary, indent=2, ensure_ascii=False))

