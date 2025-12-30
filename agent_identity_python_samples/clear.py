import os
import logging

from agent_identity_python_sdk.core import IdentityClient
from agent_identity_python_sdk.utils.config import read_local_config
from alibabacloud_agentidentity20250901.models import DeleteIdentityProviderRequest, ListWorkloadIdentitiesRequest, \
    DeleteWorkloadIdentityRequest, DeleteAPIKeyCredentialProviderRequest, DeleteOAuth2CredentialProviderRequest
from alibabacloud_tea_openapi.exceptions import ClientException
from alibabacloud_ims20190815.models import DeleteApplicationRequest
from alibabacloud_ims20190815.client import Client as ImsClient
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_tea_openapi import models as open_api_models


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

REGION = os.environ.get("AGENT_IDENTITY_REGION_ID", "cn-beijing")
identity_client = IdentityClient(REGION)
credential = CredentialClient()
ims_client = ImsClient(config=open_api_models.Config(
            credential=credential
        ))

def delete_workload_identity_with_identity_provider(identity_provider_name: str):
    """
    Delete workload identity with identity provider

    Returns:
        Identity provider name
    """
    next_token = None
    while True:
        list_req = ListWorkloadIdentitiesRequest(next_token = next_token)
        list_result = identity_client.control_client.list_workload_identities(request=list_req)
        for identity in list_result.body.workload_identities:
            logger.info(f'Deleting identity: {identity.workload_identity_name}')
            if identity.identity_provider_name != identity_provider_name:
                logger.info(f'SKIP: Identity "{identity.workload_identity_name}" is not associated with identity provider "{identity_provider_name}"')
                continue
            identity_client.control_client.delete_workload_identity(
                DeleteWorkloadIdentityRequest(
                    workload_identity_name=identity.workload_identity_name
                )
            )

        if list_result.body.next_token is None:
            break
        next_token = list_result.body.next_token

def delete_identity_provider(name: str) :
    """
    Delete identity provider

    Returns:
        Identity provider name
    """

    delete_workload_identity_with_identity_provider(name)

    req = DeleteIdentityProviderRequest(
        identity_provider_name=name
    )

    try:
        identity_client.control_client.delete_identity_provider(request=req)
    except ClientException as e:
        if e.code == "EntityNotExists.IdentityProvider":
            logger.warning(f'Identity provider "{name}" not found.')
            return
        else:
            raise e
    logger.info(f'Identity provider "{name}" deleted.')

def delete_api_key_credential_provider(name: str):
    """
    Delete API key credential provider

    Returns:
        credential provider name
    """
    req = DeleteAPIKeyCredentialProviderRequest(
        apikey_credential_provider_name=name
    )

    try:
        identity_client.control_client.delete_apikey_credential_provider(request=req)
    except ClientException as e:
        if e.code == "EntityNotExists.APIKeyCredentialProvider":
            logger.warning(f'API key credential provider "{name}" not found.')
            return
        else:
            raise e
    logger.info(f'API key credential "{name}" deleted.')

def delete_oauth2_credential_provider(name: str):
    """
    Delete OAuth2 credential provider
    """
    req = DeleteOAuth2CredentialProviderRequest(
        oauth2_credential_provider_name=name
    )

    try:
        identity_client.control_client.delete_oauth2_credential_provider(request=req)
    except ClientException as e:
        if e.code == "EntityNotExists.OAuth2CredentialProvider":
            logger.warning(f'OAuth2 credential provider "{name}" not found.')
            return
        else:
            raise e
    logger.info(f'OAuth2 credential "{name}" deleted.')

def delete_application(app_id: str):
    """
    Delete application
    """
    req = DeleteApplicationRequest(
        app_id = app_id
    )
    try:
        ims_client.delete_application(request=req)
    except ClientException as e:
        if e.code == "EntityNotExist.Application":
            logger.warning(f'Application "{app_id}" not found.')
            return
        else:
            raise e
    logger.info(f'Application "{app_id}" deleted.')

if __name__ == "__main__":

    identity_provider_name = read_local_config("identity_provider_name")
    if identity_provider_name:
        delete_identity_provider(identity_provider_name)

    inbound_app_id = read_local_config("inbound_app_id")
    if inbound_app_id:
        delete_application(inbound_app_id)

    mcp_app_id = read_local_config("mcp_app_id")
    if mcp_app_id:
        delete_application(mcp_app_id)

    api_key_provider_name = read_local_config("api_key_provider_name")
    if api_key_provider_name:
        delete_api_key_credential_provider(api_key_provider_name)

    oauth_credential_provider_name = read_local_config("oauth_credential_provider_name")
    if oauth_credential_provider_name:
        delete_oauth2_credential_provider(oauth_credential_provider_name)

