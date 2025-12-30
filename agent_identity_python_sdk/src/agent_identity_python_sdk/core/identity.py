"""
Agent Identity Python SDK Core Module

This module provides the core IdentityClient class which serves as the main interface 
for interacting with the Agent Identity service. The IdentityClient enables workload 
identity management, credential retrieval (OAuth2 token, API key and Alibaba cloud STS credential), and secure credential
handling for applications running in Alibaba Cloud environments.

The client supports various authentication flows including JWT-based authentication, 
user ID-based authentication, and OAuth2 authorization flows with resource providers.
"""

import asyncio
import logging
import os
import uuid
from typing import Any, Callable, Dict, List, Literal, Optional

from alibabacloud_agentidentity20250901.client import Client as ControlClient
from alibabacloud_agentidentity20250901.models import CreateWorkloadIdentityRequest
from alibabacloud_agentidentitydata20251127.client import Client as DataClient
from alibabacloud_agentidentitydata20251127.models import (
    AssumeRoleForWorkloadIdentityRequest,
    CompleteResourceTokenAuthRequest,
    CompleteResourceTokenAuthRequestUserIdentifier,
    GetResourceAPIKeyRequest,
    GetResourceOAuth2TokenRequest,
    GetWorkloadAccessTokenForJWTRequest,
    GetWorkloadAccessTokenForUserIdRequest,
    GetWorkloadAccessTokenRequest
)
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_credentials.models import Config as CredentialConfig
from alibabacloud_tea_openapi import models as open_api_models

from ..model.stscredential import STSCredential
from ..utils.cache import get_cached_credential, store_credential_in_cache


def _get_sts_cache_key(user_id: str, id_token: str, role_session_name: str) -> str:
    """Generate a cache key for the given user ID, ID token, and role session name."""
    return f"{user_id}:{id_token}:{role_session_name}"


class IdentityClient:
    def __init__(self, region_id: str, data_api_endpoint: Optional[str] = None,
                 control_api_endpoint: Optional[str] = None
                 ):
        self.logger = logging.getLogger("agentidentity.identity_client")
        self.use_sts = os.getenv("AGENT_IDENTITY_USE_STS", "true") == "true"
        self.region_id = region_id
        self.credential = CredentialClient()
        self.control_api_endpoint = control_api_endpoint
        self.data_api_endpoint = data_api_endpoint
        self.control_client = ControlClient(config=open_api_models.Config(
            credential=self.credential,
            region_id=region_id,
            endpoint=control_api_endpoint or f"agentidentity.{region_id}.aliyuncs.com"
        ))
        self.data_client = DataClient(config=open_api_models.Config(
            credential=self.credential,
            region_id=region_id,
            endpoint=data_api_endpoint or f"agentidentitydata.{region_id}.aliyuncs.com"
        ))


    def create_workload_identity(
            self, workload_identity_name: Optional[str] = None,
            role_arn: Optional[str] = None,
            allowed_resource_oauth2_return_urls: Optional[list[str]] = None,
            identity_provider_name: Optional[str] = None
    ) -> str:

        """
        Create a workload identity with the specified parameters.

        Args:
            workload_identity_name (Optional[str]): The name of the workload identity. If not specified,
                a random workload name will be assigned in the format 'workload-{uuid}'.
            role_arn (Optional[str]): The ARN of the agent role to be associated with this
                workload identity.
            allowed_resource_oauth2_return_urls (Optional[list[str]]): A list of allowed
                return URLs for OAuth2 flows. Only return URLs in this list will be
                permitted when obtaining OAuth2 access tokens.
            identity_provider_name (Optional[str]): The name of the identity provider
                associated with this workload identity. If configured, this workload identity
                will only accept user tokens issued by this provider.

        Returns:
            str: The name of the created workload identity.
        """
        if not workload_identity_name:
            workload_identity_name = f"workload-{uuid.uuid4().hex[:8]}"

        self.logger.info(f"Creating workload identity: {workload_identity_name}")
        request = CreateWorkloadIdentityRequest(workload_identity_name=workload_identity_name,
                                                allowed_resource_oauth2_return_urls=allowed_resource_oauth2_return_urls or [],
                                                role_arn=role_arn, identity_provider_name=identity_provider_name)
        response = self.control_client.create_workload_identity(request)
        try:
            return response.body.workload_identity.workload_identity_name
        except Exception as e:
            self.logger.error("Error creating workload identity: %s", e)
            raise e


    def get_workload_access_token(
        self, workload_name: str, user_token: Optional[str] = None, user_id: Optional[str] = None
    ) -> str:

        """
        Get a workload access token using workload name and optionally user token.
        
        Priority order for authentication:
        1. Use user_token if provided to get workload access token for JWT
        2. If user_token not provided but user_id is given, use user_id to get workload access token
        3. If neither user_token nor user_id provided, get workload access token without end-user context
        """
        try:
            if user_token:
                self.logger.info(f"Fetching workload access token for {workload_name} using user token.")
                request = GetWorkloadAccessTokenForJWTRequest(workload_identity_name=workload_name,
                                                              user_token=user_token)
                resp = self.data_client.get_workload_access_token_for_jwt(request)
                return resp.body.workload_access_token
            elif user_id:
                self.logger.info(f"Fetching workload access token for {workload_name} using user id.")
                request = GetWorkloadAccessTokenForUserIdRequest(workload_identity_name=workload_name, user_id=user_id)
                resp = self.data_client.get_workload_access_token_for_user_id(request)
                return resp.body.workload_access_token
            else:
                self.logger.info(f"Fetching workload access token for {workload_name} without end user information.")
                request = GetWorkloadAccessTokenRequest(workload_identity_name=workload_name)
                resp = self.data_client.get_workload_access_token(request)
                return resp.body.workload_access_token
        except Exception as e:
            self.logger.error(f"Error occurred when fetching workload access token for {workload_name}: %s", e)
            raise e


    def confirm_user_auth(
        self, session_uri: str, user_id: Optional[str] = None, user_token: Optional[str] = None
    ):

        """
        Confirm the user authentication session to obtain OAuth2.0 tokens for a resource.

        This function is used by applications to confirm user OAuth2 authorization. After confirmation,
        Agent Identity will start calling the OAuth2 Credential Provider's token endpoint to obtain
        the access token.

        Args:
            session_uri: The session identifier returned from the GetResourceOAuth2Token call.
            user_id: End-user ID. Required if workload access token was obtained using user ID.
            user_token: End-user token (JWT). Required if workload access token was obtained using JWT.
        """

        self.logger.info("Confirming authorization to complete OAuth2 3LO flow for access token.")

        identifier = CompleteResourceTokenAuthRequestUserIdentifier(user_id=user_id, user_jwt=user_token)
        request = CompleteResourceTokenAuthRequest(user_identifier=identifier, session_uri=session_uri)
        try:
            return self.data_client.complete_resource_token_auth(request)
        except Exception as e:
            self.logger.error("Error occurred when confirming authorization: %s", e)
            raise e

    async def get_token(
        self,
        *,
        credential_provider_name: str,
        scopes: Optional[List[str]] = None,
        workload_identity_token: str,
        on_auth_url: Optional[Callable[[str], Any]] = None,
        auth_flow: Literal["USER_FEDERATION"],
        callback_url: Optional[str] = None,
        force_authentication: bool = False,
        custom_state: Optional[str] = None,
        custom_parameters: Optional[Dict[str, str]] = None,
        credential: Optional[CredentialClient] = None,
        poll_for_token: bool = True,
    ) -> str:
        """Get an OAuth2 access token for the specified provider.

        Args:
            credential_provider_name: The credential provider name
            scopes: Optional list of OAuth2 scopes to request
            workload_identity_token: Agent identity access token for authentication
            on_auth_url: Callback for handling authorization URLs
            auth_flow: Authentication flow type ("USER_FEDERATION")
            callback_url: OAuth2 callback URL (must be pre-registered)
            force_authentication: Force re-authentication even if token exists in the token vault
            custom_state: A state that allows applications to verify the validity of callbacks to callback_url
            custom_parameters: A map of custom parameters to include in authorization request to the credential provider
                               Note: these parameters are in addition to standard OAuth 2.0 flow parameters
            credential: Optional credential for fetching the OAuth2 access token, used for calling data APIs.
            If not provided, defaults to the credential obtained when initializing the Identity Client.
            poll_for_token: Whether to poll for the token when authorization is required. If False, when getting OAuth Token and an authorization URL is returned, an exception will be thrown after calling on_auth_url.
        Returns:
            The access token string

        Raises:
            RuntimeError: When the agent identity service does not return a token or an authorization URL
            Exception: Various other exceptions for error conditions
        """
        self.logger.info("Getting OAuth2 token...")

        client = self.data_client
        if self.use_sts:
            client = DataClient(config=open_api_models.Config(
                credential=credential,
                region_id=self.region_id,
                endpoint=self.data_api_endpoint or f"agentidentitydata.{self.region_id}.aliyuncs.com"
            ))

        request = GetResourceOAuth2TokenRequest(
            resource_credential_provider_name=credential_provider_name,
            scopes=scopes,
            oauth2_flow=auth_flow,
            workload_access_token=workload_identity_token,
            resource_oauth2_return_url=callback_url,
            force_authentication=force_authentication,
            custom_state=custom_state,
            custom_parameters=custom_parameters,
        )
        try:
            response = client.get_resource_oauth2_token(request)
        except Exception as e:
            self.logger.error("Failed to get OAuth2 token: %s", str(e))
            raise
        response_body = response.body

        if response_body.access_token:
            return response_body.access_token

        if response_body.authorization_url:
            if on_auth_url:
                if asyncio.iscoroutinefunction(on_auth_url):
                    await on_auth_url(response_body.authorization_url)
                else:
                    on_auth_url(response_body.authorization_url)

            if force_authentication:
                request.force_authentication = False

            if response_body.session_uri:
                request.session_uri = response_body.session_uri

            if poll_for_token:
                self.logger.info("Waiting for OAuth2 token...")
                return await self.poll_for_oauth2_token(request)
            else:
                raise RuntimeError("Agent Identity service returned an authorization URL, authorization flow needs to be completed.")

        raise RuntimeError("Failed to obtain OAuth2 token for current workload identity: Agent Identity service did not return a token or an authorization URL.")

    async def get_api_key(self, *, credential_provider_name: str, agent_identity_token: str, credential: Optional[CredentialClient] = None) -> str:
        self.logger.info("Getting API key...")
        req = GetResourceAPIKeyRequest(resource_credential_provider_name=credential_provider_name, workload_access_token=agent_identity_token)

        client = self.data_client
        if self.use_sts:
            client = DataClient(config=open_api_models.Config(
                credential=credential,
                region_id=self.region_id,
                endpoint=self.data_api_endpoint or f"agentidentitydata.{self.region_id}.aliyuncs.com"
            ))

        response = client.get_resource_apikey(req)
        if response.body.apikey:
            return response.body.apikey
        raise RuntimeError("Agent identity service did not return an API key.")

    @staticmethod
    def _convert_to_credential(sts_credential: STSCredential) -> CredentialClient:
        credentials_config = CredentialConfig(
            type='sts',
            access_key_id=sts_credential.access_key_id,
            access_key_secret=sts_credential.access_key_secret,
            security_token=sts_credential.security_token
        )
        return CredentialClient(credentials_config)


    async def get_sts_credential_client(self, workload_token: str, user_id: Optional[str], user_token: Optional[str]) -> CredentialClient:
        cache_key = _get_sts_cache_key(workload_token, user_id, user_token)
        cached_credential = get_cached_credential(cache_key)
        if cached_credential:
            return self._convert_to_credential(cached_credential)
        sts_credential = await self.assume_role_for_workload_identity(
            workload_token=workload_token,
            role_session_name=f'AgentIdentitySessionRole-{uuid.uuid4()}'
        )
        store_credential_in_cache(cache_key, sts_credential)
        return self._convert_to_credential(sts_credential)


    async def assume_role_for_workload_identity(self, *, workload_token: str, role_session_name: str,
                                                           duration_seconds: Optional[int] = 3600,
                                                           policy: Optional[str] = None) -> STSCredential:

        request = AssumeRoleForWorkloadIdentityRequest(
            workload_access_token=workload_token,
            role_session_name=role_session_name,
            duration_seconds=duration_seconds,
            policy=policy
        )
        try:
            response = self.data_client.assume_role_for_workload_identity(request)
        except Exception as e:
            self.logger.error("Failed to assume role for workload identity: %s", str(e))
            raise
        credential = response.body.credentials
        return STSCredential(
            access_key_id=credential.access_key_id,
            access_key_secret=credential.access_key_secret,
            security_token=credential.security_token,
            expiration=credential.expiration
        )


    async def poll_for_oauth2_token(self, request: GetResourceOAuth2TokenRequest, max_retries: int = 20, delay_sec: float = 3.0) -> str:

        """
        Poll the GetResourceOAuth2Token endpoint until a token is obtained or maximum retries are reached
        
        Args:
            request: GetResourceOAuth2TokenRequest object
            max_retries: Maximum number of retry attempts
            delay_sec: Delay in seconds between each retry
            
        Returns:
            Returns the access token on success, throws an exception on failure
        """
        for attempt in range(max_retries):
            try:
                response = self.data_client.get_resource_oauth2_token(request)
                access_token = response.body.access_token

                if access_token:
                    return access_token

                self.logger.info(f"Polling for OAuth2 token, attempt {attempt + 1}")

            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed to get OAuth2 token: {str(e)}")
                
            if attempt < max_retries - 1:
                await asyncio.sleep(delay_sec)
        
        raise RuntimeError(f"Failed to get OAuth2 token after {max_retries} attempts")

