import json
import logging
import os
import uuid

from agent_identity_cli import CreateWorkloadIdentityConfig, create_workload_identity
from agent_identity_python_sdk.core import IdentityClient
from agent_identity_python_sdk.core.decorators import get_region
from agent_identity_python_sdk.utils.config import write_local_config
from alibabacloud_agentidentity20250901.models import (
    CreateIdentityProviderRequest,
    OAuth2ProviderConfig, IncludedOAuth2ProviderConfig, CreateOAuth2CredentialProviderRequest,
    CreateAPIKeyCredentialProviderRequest,
)

from alibabacloud_ims20190815.client import Client as ImsClient
from alibabacloud_ims20190815.models import CreateApplicationRequest, CreateAppSecretRequest
from alibabacloud_tea_openapi.exceptions import ClientException
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_tea_openapi import models as open_api_models

from application.backend.config import get_app_config_with_default
from deploy_starter.tools.context.config import get_config_with_default

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Basic Constants
REGION = get_region()
OAUTH_REDIRECT_URI_FOR_CONFIRM = f"{get_config_with_default('APP_REDIRECT_URI', 'http://localhost:8090')}/callback"
OAUTH_REDIRECT_URI_FOR_INBOUND = get_app_config_with_default('INBOUND_REDIRECT_URI', 'http://localhost:8090')

# Inbound configuration
INBOUND_APP_NAME = f'aliyun-inbound-{uuid.uuid4()}'
INBOUND_PROVIDER_NAME = 'test-provider'

# Outbound configuration
MCP_APP_NAME = f'aliyun-mcp-{uuid.uuid4()}'
PROTOCOL_VERSION = '2.1'
OAUTH2_CREDENTIAL_PROVIDER_NAME = 'test-provider-for-mcp-oauth'
API_KEY_CREDENTIAL_PROVIDER_NAME = 'test-provider-api-key'

# Alibaba cloud OAuth basic configuration
DISCOVERY_URL = 'https://oauth.aliyun.com/.well-known/openid-configuration'

# Initialize clients
client = IdentityClient(REGION)
credential = CredentialClient()
ims_client = ImsClient(config=open_api_models.Config(
            credential=credential
        ))

def create_mcp_application(app_name: str,
                           app_type: str,
                           predefined_scopes: str,
                           redirect_uris: str,
                           protocol_version: str) -> (str, str, str):
    """
    Create MCP application
    
    Returns:
        Tuple of application ID and callback URL
    """
    request = CreateApplicationRequest(app_name=app_name,
                                       app_type=app_type,
                                       display_name=app_name,
                                       predefined_scopes=predefined_scopes,
                                       redirect_uris = redirect_uris,
                                       required_scopes = predefined_scopes,
                                       protocol_version=protocol_version,
                                       )
    response = ims_client.create_application(request)

    logger.info(f'Application {response.body.application.app_id} created.')
    return response.body.application.app_id, response.body.application.app_name, redirect_uris


def create_identity_provider(audience: str) -> str:
    """
    Create identity provider
    
    Returns:
        Identity provider name
    """
    create_identity_provider_request = CreateIdentityProviderRequest(
        identity_provider_name=INBOUND_PROVIDER_NAME,
        description=INBOUND_PROVIDER_NAME,
        allowed_audience=[audience],
        discovery_url=DISCOVERY_URL
    )
    try:
        response = client.control_client.create_identity_provider(request=create_identity_provider_request)

        logger.info(f'Identity provider: {response.body.identity_provider.identity_provider_name} created.')

        return response.body.identity_provider.identity_provider_name
    except ClientException as error:
        if error.code == 'EntityAlreadyExists.IdentityProvider':
            logger.warning('[409] IdentityProvider already exists, skip creating.')
            return INBOUND_PROVIDER_NAME
        else:
            raise

def create_role_and_workload_identity(oauth_app_callback_url) -> (str, str):
    """
    Create role and workload identity
    
    Args:
        oauth_app_callback_url (str): OAuth application callback URL
        
    Returns:
        Tuple of workload identity name and role ARN
    """
    create_config = CreateWorkloadIdentityConfig(
        workload_identity_name=f'workload-{uuid.uuid4()}',
        identity_provider_name=INBOUND_PROVIDER_NAME,
        allowed_resource_oauth2_return_urls=[oauth_app_callback_url],
    )
    result = create_workload_identity(create_config)

    logger.info(f'Workload identity: {result.workload_identity_name} created.')
    logger.info(f'Role: {result.role_result.role_name} created.')
    return result.workload_identity_name, result.role_result.role_arn


def create_oauth2_credential_provider(app_id: str, callback_url: str) -> str:
    """
    Create OAuth2 credential provider
    
    Args:
        app_id (str): Application ID
        callback_url (str): Callback URL
        
    Returns:
        OAuth2 credential provider name
    """
    config = OAuth2ProviderConfig(
        included_oauth2_provider_config=IncludedOAuth2ProviderConfig(client_id=app_id),
    )
    try:
        response = client.control_client.create_oauth2_credential_provider(
            request=CreateOAuth2CredentialProviderRequest(
                oauth2_credential_provider_name=OAUTH2_CREDENTIAL_PROVIDER_NAME,
                credential_provider_vendor='AliyunOAuth2',
                oauth2_provider_config=config,
                description='This is a OAuth2 credential provider for alibaba cloud mcp server.',
                callback_url=callback_url
            )
        )
        logger.info(f'OAuth2 credential provider: {response.body.oauth2_credential_provider.oauth2_credential_provider_name} created.')
        return response.body.oauth2_credential_provider.oauth2_credential_provider_name
    except ClientException as error:
        if error.code == 'EntityAlreadyExists.OAuth2CredentialProvider':
            logger.warning('[409] OAuth2CredentialProvider already exists, skip creating.')
            return OAUTH2_CREDENTIAL_PROVIDER_NAME
        else:
            raise


def create_api_key_provider() -> str:
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
                apikey="12345678"
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
    inbound_app_id, inbound_app_name, inbound_callback_url = create_mcp_application(
        app_name=INBOUND_APP_NAME,
        app_type='WebApp',
        predefined_scopes='aliuid;profile;openid',
        redirect_uris=OAUTH_REDIRECT_URI_FOR_INBOUND,
        protocol_version='2.1',
    )

    mcp_app_id, mcp_app_name, mcp_callback_url = create_mcp_application(
        app_name=MCP_APP_NAME,
        app_type='NativeApp',
        predefined_scopes='aliuid;profile;openid;/acs/mcp-server',
        redirect_uris=f'https://agentidentitydata.{REGION}.aliyuncs.com/oauth2/callback/{uuid.uuid4()}',
        protocol_version='2.1',
    )

    identity_provider_name = create_identity_provider(inbound_app_id)
    workload_identity_name, role_arn = create_role_and_workload_identity(OAUTH_REDIRECT_URI_FOR_CONFIRM)
    oauth_credential_provider_name = create_oauth2_credential_provider(app_id=mcp_app_id, callback_url=mcp_callback_url)
    api_key_provider_name = create_api_key_provider()

    # Output structured JSON summary

    write_local_config('inbound_app_id', inbound_app_id)
    write_local_config('inbound_app_name', inbound_app_name)
    write_local_config('mcp_app_id', mcp_app_id)
    write_local_config('mcp_app_name', mcp_app_name)
    write_local_config('workload_identity_name', workload_identity_name)
    write_local_config('role_arn', role_arn)
    write_local_config('identity_provider_name', identity_provider_name)
    write_local_config('api_key_provider_name', api_key_provider_name)
    write_local_config('oauth_credential_provider_name', oauth_credential_provider_name)


    logger.info("Resources Summary:")
    summary = {
        "inbound_application": {
            "app_id": inbound_app_id,
            "callback_url": inbound_callback_url,
        },
        "mcp_application": {
            "app_id": mcp_app_id,
            "callback_url": mcp_callback_url
        },
        "identity_provider": identity_provider_name,
        "workload_identity": {
            "name": workload_identity_name
        },
        "role": {
            "arn": role_arn
        },
        "credential_providers": {
            "oauth2": oauth_credential_provider_name,
            "api_key": api_key_provider_name
        }
    }
    logger.info(json.dumps(summary, indent=2, ensure_ascii=False))

