# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
from typing import Dict
from Tea.core import TeaCore

from alibabacloud_tea_openapi.client import Client as OpenApiClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util.client import Client as UtilClient
from alibabacloud_endpoint_util.client import Client as EndpointUtilClient
from alibabacloud_agentidentity20250901_inner import models as agent_identity_20250901_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_openapi_util.client import Client as OpenApiUtilClient


class Client(OpenApiClient):
    """
    *\
    """
    def __init__(
        self, 
        config: open_api_models.Config,
    ):
        super().__init__(config)
        self._endpoint_rule = 'regional'
        self.check_config(config)
        self._endpoint = self.get_endpoint('agentidentity', self._region_id, self._endpoint_rule, self._network, self._suffix, self._endpoint_map, self._endpoint)

    def get_endpoint(
        self,
        product_id: str,
        region_id: str,
        endpoint_rule: str,
        network: str,
        suffix: str,
        endpoint_map: Dict[str, str],
        endpoint: str,
    ) -> str:
        if not UtilClient.empty(endpoint):
            return endpoint
        if not UtilClient.is_unset(endpoint_map) and not UtilClient.empty(endpoint_map.get(region_id)):
            return endpoint_map.get(region_id)
        return EndpointUtilClient.get_endpoint_rules(product_id, region_id, endpoint_rule, network, suffix)

    def add_samlidentity_provider_certificate_with_options(
        self,
        request: agent_identity_20250901_models.AddSAMLIdentityProviderCertificateRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.AddSAMLIdentityProviderCertificateResponse:
        """
        @summary 创建应用
        
        @param request: AddSAMLIdentityProviderCertificateRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: AddSAMLIdentityProviderCertificateResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        if not UtilClient.is_unset(request.x_509certificate):
            body['X509Certificate'] = request.x_509certificate
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='AddSAMLIdentityProviderCertificate',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.AddSAMLIdentityProviderCertificateResponse(),
            self.call_api(params, req, runtime)
        )

    async def add_samlidentity_provider_certificate_with_options_async(
        self,
        request: agent_identity_20250901_models.AddSAMLIdentityProviderCertificateRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.AddSAMLIdentityProviderCertificateResponse:
        """
        @summary 创建应用
        
        @param request: AddSAMLIdentityProviderCertificateRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: AddSAMLIdentityProviderCertificateResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        if not UtilClient.is_unset(request.x_509certificate):
            body['X509Certificate'] = request.x_509certificate
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='AddSAMLIdentityProviderCertificate',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.AddSAMLIdentityProviderCertificateResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def add_samlidentity_provider_certificate(
        self,
        request: agent_identity_20250901_models.AddSAMLIdentityProviderCertificateRequest,
    ) -> agent_identity_20250901_models.AddSAMLIdentityProviderCertificateResponse:
        """
        @summary 创建应用
        
        @param request: AddSAMLIdentityProviderCertificateRequest
        @return: AddSAMLIdentityProviderCertificateResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.add_samlidentity_provider_certificate_with_options(request, runtime)

    async def add_samlidentity_provider_certificate_async(
        self,
        request: agent_identity_20250901_models.AddSAMLIdentityProviderCertificateRequest,
    ) -> agent_identity_20250901_models.AddSAMLIdentityProviderCertificateResponse:
        """
        @summary 创建应用
        
        @param request: AddSAMLIdentityProviderCertificateRequest
        @return: AddSAMLIdentityProviderCertificateResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.add_samlidentity_provider_certificate_with_options_async(request, runtime)

    def attach_policy_set_to_gateway_with_options(
        self,
        request: agent_identity_20250901_models.AttachPolicySetToGatewayRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.AttachPolicySetToGatewayResponse:
        """
        @summary 策略集关联网关
        
        @param request: AttachPolicySetToGatewayRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: AttachPolicySetToGatewayResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.enforcement_mode):
            body['EnforcementMode'] = request.enforcement_mode
        if not UtilClient.is_unset(request.gateway_arn):
            body['GatewayArn'] = request.gateway_arn
        if not UtilClient.is_unset(request.policy_set_name):
            body['PolicySetName'] = request.policy_set_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='AttachPolicySetToGateway',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.AttachPolicySetToGatewayResponse(),
            self.call_api(params, req, runtime)
        )

    async def attach_policy_set_to_gateway_with_options_async(
        self,
        request: agent_identity_20250901_models.AttachPolicySetToGatewayRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.AttachPolicySetToGatewayResponse:
        """
        @summary 策略集关联网关
        
        @param request: AttachPolicySetToGatewayRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: AttachPolicySetToGatewayResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.enforcement_mode):
            body['EnforcementMode'] = request.enforcement_mode
        if not UtilClient.is_unset(request.gateway_arn):
            body['GatewayArn'] = request.gateway_arn
        if not UtilClient.is_unset(request.policy_set_name):
            body['PolicySetName'] = request.policy_set_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='AttachPolicySetToGateway',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.AttachPolicySetToGatewayResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def attach_policy_set_to_gateway(
        self,
        request: agent_identity_20250901_models.AttachPolicySetToGatewayRequest,
    ) -> agent_identity_20250901_models.AttachPolicySetToGatewayResponse:
        """
        @summary 策略集关联网关
        
        @param request: AttachPolicySetToGatewayRequest
        @return: AttachPolicySetToGatewayResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.attach_policy_set_to_gateway_with_options(request, runtime)

    async def attach_policy_set_to_gateway_async(
        self,
        request: agent_identity_20250901_models.AttachPolicySetToGatewayRequest,
    ) -> agent_identity_20250901_models.AttachPolicySetToGatewayResponse:
        """
        @summary 策略集关联网关
        
        @param request: AttachPolicySetToGatewayRequest
        @return: AttachPolicySetToGatewayResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.attach_policy_set_to_gateway_with_options_async(request, runtime)

    def create_apikey_credential_provider_with_options(
        self,
        request: agent_identity_20250901_models.CreateAPIKeyCredentialProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.CreateAPIKeyCredentialProviderResponse:
        """
        @summary 创建一个 API 密钥凭证提供商
        
        @param request: CreateAPIKeyCredentialProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: CreateAPIKeyCredentialProviderResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.apikey):
            body['APIKey'] = request.apikey
        if not UtilClient.is_unset(request.apikey_credential_provider_name):
            body['APIKeyCredentialProviderName'] = request.apikey_credential_provider_name
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='CreateAPIKeyCredentialProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.CreateAPIKeyCredentialProviderResponse(),
            self.call_api(params, req, runtime)
        )

    async def create_apikey_credential_provider_with_options_async(
        self,
        request: agent_identity_20250901_models.CreateAPIKeyCredentialProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.CreateAPIKeyCredentialProviderResponse:
        """
        @summary 创建一个 API 密钥凭证提供商
        
        @param request: CreateAPIKeyCredentialProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: CreateAPIKeyCredentialProviderResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.apikey):
            body['APIKey'] = request.apikey
        if not UtilClient.is_unset(request.apikey_credential_provider_name):
            body['APIKeyCredentialProviderName'] = request.apikey_credential_provider_name
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='CreateAPIKeyCredentialProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.CreateAPIKeyCredentialProviderResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def create_apikey_credential_provider(
        self,
        request: agent_identity_20250901_models.CreateAPIKeyCredentialProviderRequest,
    ) -> agent_identity_20250901_models.CreateAPIKeyCredentialProviderResponse:
        """
        @summary 创建一个 API 密钥凭证提供商
        
        @param request: CreateAPIKeyCredentialProviderRequest
        @return: CreateAPIKeyCredentialProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.create_apikey_credential_provider_with_options(request, runtime)

    async def create_apikey_credential_provider_async(
        self,
        request: agent_identity_20250901_models.CreateAPIKeyCredentialProviderRequest,
    ) -> agent_identity_20250901_models.CreateAPIKeyCredentialProviderResponse:
        """
        @summary 创建一个 API 密钥凭证提供商
        
        @param request: CreateAPIKeyCredentialProviderRequest
        @return: CreateAPIKeyCredentialProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.create_apikey_credential_provider_with_options_async(request, runtime)

    def create_client_secret_with_options(
        self,
        request: agent_identity_20250901_models.CreateClientSecretRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.CreateClientSecretResponse:
        """
        @summary 创建WorkloadIdentity
        
        @param request: CreateClientSecretRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: CreateClientSecretResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.client_id):
            body['ClientId'] = request.client_id
        if not UtilClient.is_unset(request.client_name):
            body['ClientName'] = request.client_name
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='CreateClientSecret',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.CreateClientSecretResponse(),
            self.call_api(params, req, runtime)
        )

    async def create_client_secret_with_options_async(
        self,
        request: agent_identity_20250901_models.CreateClientSecretRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.CreateClientSecretResponse:
        """
        @summary 创建WorkloadIdentity
        
        @param request: CreateClientSecretRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: CreateClientSecretResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.client_id):
            body['ClientId'] = request.client_id
        if not UtilClient.is_unset(request.client_name):
            body['ClientName'] = request.client_name
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='CreateClientSecret',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.CreateClientSecretResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def create_client_secret(
        self,
        request: agent_identity_20250901_models.CreateClientSecretRequest,
    ) -> agent_identity_20250901_models.CreateClientSecretResponse:
        """
        @summary 创建WorkloadIdentity
        
        @param request: CreateClientSecretRequest
        @return: CreateClientSecretResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.create_client_secret_with_options(request, runtime)

    async def create_client_secret_async(
        self,
        request: agent_identity_20250901_models.CreateClientSecretRequest,
    ) -> agent_identity_20250901_models.CreateClientSecretResponse:
        """
        @summary 创建WorkloadIdentity
        
        @param request: CreateClientSecretRequest
        @return: CreateClientSecretResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.create_client_secret_with_options_async(request, runtime)

    def create_identity_provider_with_options(
        self,
        tmp_req: agent_identity_20250901_models.CreateIdentityProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.CreateIdentityProviderResponse:
        """
        @summary 创建IdentityProvider
        
        @param tmp_req: CreateIdentityProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: CreateIdentityProviderResponse
        """
        UtilClient.validate_model(tmp_req)
        request = agent_identity_20250901_models.CreateIdentityProviderShrinkRequest()
        OpenApiUtilClient.convert(tmp_req, request)
        if not UtilClient.is_unset(tmp_req.allowed_audience):
            request.allowed_audience_shrink = OpenApiUtilClient.array_to_string_with_specified_style(tmp_req.allowed_audience, 'AllowedAudience', 'json')
        body = {}
        if not UtilClient.is_unset(request.allowed_audience_shrink):
            body['AllowedAudience'] = request.allowed_audience_shrink
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.discovery_url):
            body['DiscoveryURL'] = request.discovery_url
        if not UtilClient.is_unset(request.identity_provider_name):
            body['IdentityProviderName'] = request.identity_provider_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='CreateIdentityProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.CreateIdentityProviderResponse(),
            self.call_api(params, req, runtime)
        )

    async def create_identity_provider_with_options_async(
        self,
        tmp_req: agent_identity_20250901_models.CreateIdentityProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.CreateIdentityProviderResponse:
        """
        @summary 创建IdentityProvider
        
        @param tmp_req: CreateIdentityProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: CreateIdentityProviderResponse
        """
        UtilClient.validate_model(tmp_req)
        request = agent_identity_20250901_models.CreateIdentityProviderShrinkRequest()
        OpenApiUtilClient.convert(tmp_req, request)
        if not UtilClient.is_unset(tmp_req.allowed_audience):
            request.allowed_audience_shrink = OpenApiUtilClient.array_to_string_with_specified_style(tmp_req.allowed_audience, 'AllowedAudience', 'json')
        body = {}
        if not UtilClient.is_unset(request.allowed_audience_shrink):
            body['AllowedAudience'] = request.allowed_audience_shrink
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.discovery_url):
            body['DiscoveryURL'] = request.discovery_url
        if not UtilClient.is_unset(request.identity_provider_name):
            body['IdentityProviderName'] = request.identity_provider_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='CreateIdentityProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.CreateIdentityProviderResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def create_identity_provider(
        self,
        request: agent_identity_20250901_models.CreateIdentityProviderRequest,
    ) -> agent_identity_20250901_models.CreateIdentityProviderResponse:
        """
        @summary 创建IdentityProvider
        
        @param request: CreateIdentityProviderRequest
        @return: CreateIdentityProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.create_identity_provider_with_options(request, runtime)

    async def create_identity_provider_async(
        self,
        request: agent_identity_20250901_models.CreateIdentityProviderRequest,
    ) -> agent_identity_20250901_models.CreateIdentityProviderResponse:
        """
        @summary 创建IdentityProvider
        
        @param request: CreateIdentityProviderRequest
        @return: CreateIdentityProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.create_identity_provider_with_options_async(request, runtime)

    def create_oauth_2credential_provider_with_options(
        self,
        tmp_req: agent_identity_20250901_models.CreateOAuth2CredentialProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.CreateOAuth2CredentialProviderResponse:
        """
        @summary 创建 OAuth2 凭证提供商
        
        @param tmp_req: CreateOAuth2CredentialProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: CreateOAuth2CredentialProviderResponse
        """
        UtilClient.validate_model(tmp_req)
        request = agent_identity_20250901_models.CreateOAuth2CredentialProviderShrinkRequest()
        OpenApiUtilClient.convert(tmp_req, request)
        if not UtilClient.is_unset(tmp_req.oauth_2provider_config):
            request.oauth_2provider_config_shrink = OpenApiUtilClient.array_to_string_with_specified_style(tmp_req.oauth_2provider_config, 'OAuth2ProviderConfig', 'json')
        body = {}
        if not UtilClient.is_unset(request.callback_url):
            body['CallbackURL'] = request.callback_url
        if not UtilClient.is_unset(request.credential_provider_vendor):
            body['CredentialProviderVendor'] = request.credential_provider_vendor
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.oauth_2credential_provider_name):
            body['OAuth2CredentialProviderName'] = request.oauth_2credential_provider_name
        if not UtilClient.is_unset(request.oauth_2provider_config_shrink):
            body['OAuth2ProviderConfig'] = request.oauth_2provider_config_shrink
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='CreateOAuth2CredentialProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.CreateOAuth2CredentialProviderResponse(),
            self.call_api(params, req, runtime)
        )

    async def create_oauth_2credential_provider_with_options_async(
        self,
        tmp_req: agent_identity_20250901_models.CreateOAuth2CredentialProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.CreateOAuth2CredentialProviderResponse:
        """
        @summary 创建 OAuth2 凭证提供商
        
        @param tmp_req: CreateOAuth2CredentialProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: CreateOAuth2CredentialProviderResponse
        """
        UtilClient.validate_model(tmp_req)
        request = agent_identity_20250901_models.CreateOAuth2CredentialProviderShrinkRequest()
        OpenApiUtilClient.convert(tmp_req, request)
        if not UtilClient.is_unset(tmp_req.oauth_2provider_config):
            request.oauth_2provider_config_shrink = OpenApiUtilClient.array_to_string_with_specified_style(tmp_req.oauth_2provider_config, 'OAuth2ProviderConfig', 'json')
        body = {}
        if not UtilClient.is_unset(request.callback_url):
            body['CallbackURL'] = request.callback_url
        if not UtilClient.is_unset(request.credential_provider_vendor):
            body['CredentialProviderVendor'] = request.credential_provider_vendor
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.oauth_2credential_provider_name):
            body['OAuth2CredentialProviderName'] = request.oauth_2credential_provider_name
        if not UtilClient.is_unset(request.oauth_2provider_config_shrink):
            body['OAuth2ProviderConfig'] = request.oauth_2provider_config_shrink
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='CreateOAuth2CredentialProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.CreateOAuth2CredentialProviderResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def create_oauth_2credential_provider(
        self,
        request: agent_identity_20250901_models.CreateOAuth2CredentialProviderRequest,
    ) -> agent_identity_20250901_models.CreateOAuth2CredentialProviderResponse:
        """
        @summary 创建 OAuth2 凭证提供商
        
        @param request: CreateOAuth2CredentialProviderRequest
        @return: CreateOAuth2CredentialProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.create_oauth_2credential_provider_with_options(request, runtime)

    async def create_oauth_2credential_provider_async(
        self,
        request: agent_identity_20250901_models.CreateOAuth2CredentialProviderRequest,
    ) -> agent_identity_20250901_models.CreateOAuth2CredentialProviderResponse:
        """
        @summary 创建 OAuth2 凭证提供商
        
        @param request: CreateOAuth2CredentialProviderRequest
        @return: CreateOAuth2CredentialProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.create_oauth_2credential_provider_with_options_async(request, runtime)

    def create_policy_with_options(
        self,
        tmp_req: agent_identity_20250901_models.CreatePolicyRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.CreatePolicyResponse:
        """
        @summary 创建一个权限策略
        
        @param tmp_req: CreatePolicyRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: CreatePolicyResponse
        """
        UtilClient.validate_model(tmp_req)
        request = agent_identity_20250901_models.CreatePolicyShrinkRequest()
        OpenApiUtilClient.convert(tmp_req, request)
        if not UtilClient.is_unset(tmp_req.definition):
            request.definition_shrink = OpenApiUtilClient.array_to_string_with_specified_style(tmp_req.definition, 'Definition', 'json')
        body = {}
        if not UtilClient.is_unset(request.definition_shrink):
            body['Definition'] = request.definition_shrink
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.policy_name):
            body['PolicyName'] = request.policy_name
        if not UtilClient.is_unset(request.policy_set_name):
            body['PolicySetName'] = request.policy_set_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='CreatePolicy',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.CreatePolicyResponse(),
            self.call_api(params, req, runtime)
        )

    async def create_policy_with_options_async(
        self,
        tmp_req: agent_identity_20250901_models.CreatePolicyRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.CreatePolicyResponse:
        """
        @summary 创建一个权限策略
        
        @param tmp_req: CreatePolicyRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: CreatePolicyResponse
        """
        UtilClient.validate_model(tmp_req)
        request = agent_identity_20250901_models.CreatePolicyShrinkRequest()
        OpenApiUtilClient.convert(tmp_req, request)
        if not UtilClient.is_unset(tmp_req.definition):
            request.definition_shrink = OpenApiUtilClient.array_to_string_with_specified_style(tmp_req.definition, 'Definition', 'json')
        body = {}
        if not UtilClient.is_unset(request.definition_shrink):
            body['Definition'] = request.definition_shrink
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.policy_name):
            body['PolicyName'] = request.policy_name
        if not UtilClient.is_unset(request.policy_set_name):
            body['PolicySetName'] = request.policy_set_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='CreatePolicy',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.CreatePolicyResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def create_policy(
        self,
        request: agent_identity_20250901_models.CreatePolicyRequest,
    ) -> agent_identity_20250901_models.CreatePolicyResponse:
        """
        @summary 创建一个权限策略
        
        @param request: CreatePolicyRequest
        @return: CreatePolicyResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.create_policy_with_options(request, runtime)

    async def create_policy_async(
        self,
        request: agent_identity_20250901_models.CreatePolicyRequest,
    ) -> agent_identity_20250901_models.CreatePolicyResponse:
        """
        @summary 创建一个权限策略
        
        @param request: CreatePolicyRequest
        @return: CreatePolicyResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.create_policy_with_options_async(request, runtime)

    def create_policy_set_with_options(
        self,
        request: agent_identity_20250901_models.CreatePolicySetRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.CreatePolicySetResponse:
        """
        @summary 创建一个权限策略集合
        
        @param request: CreatePolicySetRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: CreatePolicySetResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.policy_set_name):
            body['PolicySetName'] = request.policy_set_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='CreatePolicySet',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.CreatePolicySetResponse(),
            self.call_api(params, req, runtime)
        )

    async def create_policy_set_with_options_async(
        self,
        request: agent_identity_20250901_models.CreatePolicySetRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.CreatePolicySetResponse:
        """
        @summary 创建一个权限策略集合
        
        @param request: CreatePolicySetRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: CreatePolicySetResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.policy_set_name):
            body['PolicySetName'] = request.policy_set_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='CreatePolicySet',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.CreatePolicySetResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def create_policy_set(
        self,
        request: agent_identity_20250901_models.CreatePolicySetRequest,
    ) -> agent_identity_20250901_models.CreatePolicySetResponse:
        """
        @summary 创建一个权限策略集合
        
        @param request: CreatePolicySetRequest
        @return: CreatePolicySetResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.create_policy_set_with_options(request, runtime)

    async def create_policy_set_async(
        self,
        request: agent_identity_20250901_models.CreatePolicySetRequest,
    ) -> agent_identity_20250901_models.CreatePolicySetResponse:
        """
        @summary 创建一个权限策略集合
        
        @param request: CreatePolicySetRequest
        @return: CreatePolicySetResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.create_policy_set_with_options_async(request, runtime)

    def create_role_with_options(
        self,
        request: agent_identity_20250901_models.CreateRoleRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.CreateRoleResponse:
        """
        @summary 创建Role
        
        @param request: CreateRoleRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: CreateRoleResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.role_name):
            body['RoleName'] = request.role_name
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='CreateRole',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.CreateRoleResponse(),
            self.call_api(params, req, runtime)
        )

    async def create_role_with_options_async(
        self,
        request: agent_identity_20250901_models.CreateRoleRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.CreateRoleResponse:
        """
        @summary 创建Role
        
        @param request: CreateRoleRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: CreateRoleResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.role_name):
            body['RoleName'] = request.role_name
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='CreateRole',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.CreateRoleResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def create_role(
        self,
        request: agent_identity_20250901_models.CreateRoleRequest,
    ) -> agent_identity_20250901_models.CreateRoleResponse:
        """
        @summary 创建Role
        
        @param request: CreateRoleRequest
        @return: CreateRoleResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.create_role_with_options(request, runtime)

    async def create_role_async(
        self,
        request: agent_identity_20250901_models.CreateRoleRequest,
    ) -> agent_identity_20250901_models.CreateRoleResponse:
        """
        @summary 创建Role
        
        @param request: CreateRoleRequest
        @return: CreateRoleResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.create_role_with_options_async(request, runtime)

    def create_role_assignment_with_options(
        self,
        request: agent_identity_20250901_models.CreateRoleAssignmentRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.CreateRoleAssignmentResponse:
        """
        @summary 策略集关联网关
        
        @param request: CreateRoleAssignmentRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: CreateRoleAssignmentResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.principal_name):
            body['PrincipalName'] = request.principal_name
        if not UtilClient.is_unset(request.principal_type):
            body['PrincipalType'] = request.principal_type
        if not UtilClient.is_unset(request.role_name):
            body['RoleName'] = request.role_name
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='CreateRoleAssignment',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.CreateRoleAssignmentResponse(),
            self.call_api(params, req, runtime)
        )

    async def create_role_assignment_with_options_async(
        self,
        request: agent_identity_20250901_models.CreateRoleAssignmentRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.CreateRoleAssignmentResponse:
        """
        @summary 策略集关联网关
        
        @param request: CreateRoleAssignmentRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: CreateRoleAssignmentResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.principal_name):
            body['PrincipalName'] = request.principal_name
        if not UtilClient.is_unset(request.principal_type):
            body['PrincipalType'] = request.principal_type
        if not UtilClient.is_unset(request.role_name):
            body['RoleName'] = request.role_name
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='CreateRoleAssignment',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.CreateRoleAssignmentResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def create_role_assignment(
        self,
        request: agent_identity_20250901_models.CreateRoleAssignmentRequest,
    ) -> agent_identity_20250901_models.CreateRoleAssignmentResponse:
        """
        @summary 策略集关联网关
        
        @param request: CreateRoleAssignmentRequest
        @return: CreateRoleAssignmentResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.create_role_assignment_with_options(request, runtime)

    async def create_role_assignment_async(
        self,
        request: agent_identity_20250901_models.CreateRoleAssignmentRequest,
    ) -> agent_identity_20250901_models.CreateRoleAssignmentResponse:
        """
        @summary 策略集关联网关
        
        @param request: CreateRoleAssignmentRequest
        @return: CreateRoleAssignmentResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.create_role_assignment_with_options_async(request, runtime)

    def create_token_vault_with_options(
        self,
        tmp_req: agent_identity_20250901_models.CreateTokenVaultRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.CreateTokenVaultResponse:
        """
        @summary 创建一个凭证库
        
        @param tmp_req: CreateTokenVaultRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: CreateTokenVaultResponse
        """
        UtilClient.validate_model(tmp_req)
        request = agent_identity_20250901_models.CreateTokenVaultShrinkRequest()
        OpenApiUtilClient.convert(tmp_req, request)
        if not UtilClient.is_unset(tmp_req.encryption_config):
            request.encryption_config_shrink = OpenApiUtilClient.array_to_string_with_specified_style(tmp_req.encryption_config, 'EncryptionConfig', 'json')
        body = {}
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.encryption_config_shrink):
            body['EncryptionConfig'] = request.encryption_config_shrink
        if not UtilClient.is_unset(request.role_arn):
            body['RoleArn'] = request.role_arn
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='CreateTokenVault',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.CreateTokenVaultResponse(),
            self.call_api(params, req, runtime)
        )

    async def create_token_vault_with_options_async(
        self,
        tmp_req: agent_identity_20250901_models.CreateTokenVaultRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.CreateTokenVaultResponse:
        """
        @summary 创建一个凭证库
        
        @param tmp_req: CreateTokenVaultRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: CreateTokenVaultResponse
        """
        UtilClient.validate_model(tmp_req)
        request = agent_identity_20250901_models.CreateTokenVaultShrinkRequest()
        OpenApiUtilClient.convert(tmp_req, request)
        if not UtilClient.is_unset(tmp_req.encryption_config):
            request.encryption_config_shrink = OpenApiUtilClient.array_to_string_with_specified_style(tmp_req.encryption_config, 'EncryptionConfig', 'json')
        body = {}
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.encryption_config_shrink):
            body['EncryptionConfig'] = request.encryption_config_shrink
        if not UtilClient.is_unset(request.role_arn):
            body['RoleArn'] = request.role_arn
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='CreateTokenVault',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.CreateTokenVaultResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def create_token_vault(
        self,
        request: agent_identity_20250901_models.CreateTokenVaultRequest,
    ) -> agent_identity_20250901_models.CreateTokenVaultResponse:
        """
        @summary 创建一个凭证库
        
        @param request: CreateTokenVaultRequest
        @return: CreateTokenVaultResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.create_token_vault_with_options(request, runtime)

    async def create_token_vault_async(
        self,
        request: agent_identity_20250901_models.CreateTokenVaultRequest,
    ) -> agent_identity_20250901_models.CreateTokenVaultResponse:
        """
        @summary 创建一个凭证库
        
        @param request: CreateTokenVaultRequest
        @return: CreateTokenVaultResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.create_token_vault_with_options_async(request, runtime)

    def create_user_pool_with_options(
        self,
        request: agent_identity_20250901_models.CreateUserPoolRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.CreateUserPoolResponse:
        """
        @summary 创建UserPool
        
        @param request: CreateUserPoolRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: CreateUserPoolResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='CreateUserPool',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.CreateUserPoolResponse(),
            self.call_api(params, req, runtime)
        )

    async def create_user_pool_with_options_async(
        self,
        request: agent_identity_20250901_models.CreateUserPoolRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.CreateUserPoolResponse:
        """
        @summary 创建UserPool
        
        @param request: CreateUserPoolRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: CreateUserPoolResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='CreateUserPool',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.CreateUserPoolResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def create_user_pool(
        self,
        request: agent_identity_20250901_models.CreateUserPoolRequest,
    ) -> agent_identity_20250901_models.CreateUserPoolResponse:
        """
        @summary 创建UserPool
        
        @param request: CreateUserPoolRequest
        @return: CreateUserPoolResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.create_user_pool_with_options(request, runtime)

    async def create_user_pool_async(
        self,
        request: agent_identity_20250901_models.CreateUserPoolRequest,
    ) -> agent_identity_20250901_models.CreateUserPoolResponse:
        """
        @summary 创建UserPool
        
        @param request: CreateUserPoolRequest
        @return: CreateUserPoolResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.create_user_pool_with_options_async(request, runtime)

    def create_user_pool_client_with_options(
        self,
        request: agent_identity_20250901_models.CreateUserPoolClientRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.CreateUserPoolClientResponse:
        """
        @summary 创建WorkloadIdentity
        
        @param request: CreateUserPoolClientRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: CreateUserPoolClientResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.access_token_validity):
            body['AccessTokenValidity'] = request.access_token_validity
        if not UtilClient.is_unset(request.client_name):
            body['ClientName'] = request.client_name
        if not UtilClient.is_unset(request.enforce_pkce):
            body['EnforcePKCE'] = request.enforce_pkce
        if not UtilClient.is_unset(request.redirect_uris):
            body['RedirectURIs'] = request.redirect_uris
        if not UtilClient.is_unset(request.refresh_token_validity):
            body['RefreshTokenValidity'] = request.refresh_token_validity
        if not UtilClient.is_unset(request.secret_required):
            body['SecretRequired'] = request.secret_required
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='CreateUserPoolClient',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.CreateUserPoolClientResponse(),
            self.call_api(params, req, runtime)
        )

    async def create_user_pool_client_with_options_async(
        self,
        request: agent_identity_20250901_models.CreateUserPoolClientRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.CreateUserPoolClientResponse:
        """
        @summary 创建WorkloadIdentity
        
        @param request: CreateUserPoolClientRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: CreateUserPoolClientResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.access_token_validity):
            body['AccessTokenValidity'] = request.access_token_validity
        if not UtilClient.is_unset(request.client_name):
            body['ClientName'] = request.client_name
        if not UtilClient.is_unset(request.enforce_pkce):
            body['EnforcePKCE'] = request.enforce_pkce
        if not UtilClient.is_unset(request.redirect_uris):
            body['RedirectURIs'] = request.redirect_uris
        if not UtilClient.is_unset(request.refresh_token_validity):
            body['RefreshTokenValidity'] = request.refresh_token_validity
        if not UtilClient.is_unset(request.secret_required):
            body['SecretRequired'] = request.secret_required
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='CreateUserPoolClient',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.CreateUserPoolClientResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def create_user_pool_client(
        self,
        request: agent_identity_20250901_models.CreateUserPoolClientRequest,
    ) -> agent_identity_20250901_models.CreateUserPoolClientResponse:
        """
        @summary 创建WorkloadIdentity
        
        @param request: CreateUserPoolClientRequest
        @return: CreateUserPoolClientResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.create_user_pool_client_with_options(request, runtime)

    async def create_user_pool_client_async(
        self,
        request: agent_identity_20250901_models.CreateUserPoolClientRequest,
    ) -> agent_identity_20250901_models.CreateUserPoolClientResponse:
        """
        @summary 创建WorkloadIdentity
        
        @param request: CreateUserPoolClientRequest
        @return: CreateUserPoolClientResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.create_user_pool_client_with_options_async(request, runtime)

    def create_workload_identity_with_options(
        self,
        tmp_req: agent_identity_20250901_models.CreateWorkloadIdentityRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.CreateWorkloadIdentityResponse:
        """
        @summary 创建WorkloadIdentity
        
        @param tmp_req: CreateWorkloadIdentityRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: CreateWorkloadIdentityResponse
        """
        UtilClient.validate_model(tmp_req)
        request = agent_identity_20250901_models.CreateWorkloadIdentityShrinkRequest()
        OpenApiUtilClient.convert(tmp_req, request)
        if not UtilClient.is_unset(tmp_req.allowed_resource_oauth_2return_urls):
            request.allowed_resource_oauth_2return_urls_shrink = OpenApiUtilClient.array_to_string_with_specified_style(tmp_req.allowed_resource_oauth_2return_urls, 'AllowedResourceOAuth2ReturnURLs', 'json')
        body = {}
        if not UtilClient.is_unset(request.allowed_resource_oauth_2return_urls_shrink):
            body['AllowedResourceOAuth2ReturnURLs'] = request.allowed_resource_oauth_2return_urls_shrink
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.identity_provider_name):
            body['IdentityProviderName'] = request.identity_provider_name
        if not UtilClient.is_unset(request.role_arn):
            body['RoleArn'] = request.role_arn
        if not UtilClient.is_unset(request.workload_identity_name):
            body['WorkloadIdentityName'] = request.workload_identity_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='CreateWorkloadIdentity',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.CreateWorkloadIdentityResponse(),
            self.call_api(params, req, runtime)
        )

    async def create_workload_identity_with_options_async(
        self,
        tmp_req: agent_identity_20250901_models.CreateWorkloadIdentityRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.CreateWorkloadIdentityResponse:
        """
        @summary 创建WorkloadIdentity
        
        @param tmp_req: CreateWorkloadIdentityRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: CreateWorkloadIdentityResponse
        """
        UtilClient.validate_model(tmp_req)
        request = agent_identity_20250901_models.CreateWorkloadIdentityShrinkRequest()
        OpenApiUtilClient.convert(tmp_req, request)
        if not UtilClient.is_unset(tmp_req.allowed_resource_oauth_2return_urls):
            request.allowed_resource_oauth_2return_urls_shrink = OpenApiUtilClient.array_to_string_with_specified_style(tmp_req.allowed_resource_oauth_2return_urls, 'AllowedResourceOAuth2ReturnURLs', 'json')
        body = {}
        if not UtilClient.is_unset(request.allowed_resource_oauth_2return_urls_shrink):
            body['AllowedResourceOAuth2ReturnURLs'] = request.allowed_resource_oauth_2return_urls_shrink
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.identity_provider_name):
            body['IdentityProviderName'] = request.identity_provider_name
        if not UtilClient.is_unset(request.role_arn):
            body['RoleArn'] = request.role_arn
        if not UtilClient.is_unset(request.workload_identity_name):
            body['WorkloadIdentityName'] = request.workload_identity_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='CreateWorkloadIdentity',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.CreateWorkloadIdentityResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def create_workload_identity(
        self,
        request: agent_identity_20250901_models.CreateWorkloadIdentityRequest,
    ) -> agent_identity_20250901_models.CreateWorkloadIdentityResponse:
        """
        @summary 创建WorkloadIdentity
        
        @param request: CreateWorkloadIdentityRequest
        @return: CreateWorkloadIdentityResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.create_workload_identity_with_options(request, runtime)

    async def create_workload_identity_async(
        self,
        request: agent_identity_20250901_models.CreateWorkloadIdentityRequest,
    ) -> agent_identity_20250901_models.CreateWorkloadIdentityResponse:
        """
        @summary 创建WorkloadIdentity
        
        @param request: CreateWorkloadIdentityRequest
        @return: CreateWorkloadIdentityResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.create_workload_identity_with_options_async(request, runtime)

    def delete_apikey_credential_provider_with_options(
        self,
        request: agent_identity_20250901_models.DeleteAPIKeyCredentialProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeleteAPIKeyCredentialProviderResponse:
        """
        @summary 删除一个 API 密钥凭证提供商
        
        @param request: DeleteAPIKeyCredentialProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeleteAPIKeyCredentialProviderResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.apikey_credential_provider_name):
            body['APIKeyCredentialProviderName'] = request.apikey_credential_provider_name
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeleteAPIKeyCredentialProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeleteAPIKeyCredentialProviderResponse(),
            self.call_api(params, req, runtime)
        )

    async def delete_apikey_credential_provider_with_options_async(
        self,
        request: agent_identity_20250901_models.DeleteAPIKeyCredentialProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeleteAPIKeyCredentialProviderResponse:
        """
        @summary 删除一个 API 密钥凭证提供商
        
        @param request: DeleteAPIKeyCredentialProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeleteAPIKeyCredentialProviderResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.apikey_credential_provider_name):
            body['APIKeyCredentialProviderName'] = request.apikey_credential_provider_name
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeleteAPIKeyCredentialProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeleteAPIKeyCredentialProviderResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def delete_apikey_credential_provider(
        self,
        request: agent_identity_20250901_models.DeleteAPIKeyCredentialProviderRequest,
    ) -> agent_identity_20250901_models.DeleteAPIKeyCredentialProviderResponse:
        """
        @summary 删除一个 API 密钥凭证提供商
        
        @param request: DeleteAPIKeyCredentialProviderRequest
        @return: DeleteAPIKeyCredentialProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.delete_apikey_credential_provider_with_options(request, runtime)

    async def delete_apikey_credential_provider_async(
        self,
        request: agent_identity_20250901_models.DeleteAPIKeyCredentialProviderRequest,
    ) -> agent_identity_20250901_models.DeleteAPIKeyCredentialProviderResponse:
        """
        @summary 删除一个 API 密钥凭证提供商
        
        @param request: DeleteAPIKeyCredentialProviderRequest
        @return: DeleteAPIKeyCredentialProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.delete_apikey_credential_provider_with_options_async(request, runtime)

    def delete_client_secret_with_options(
        self,
        request: agent_identity_20250901_models.DeleteClientSecretRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeleteClientSecretResponse:
        """
        @summary 删除IdentityProvider
        
        @param request: DeleteClientSecretRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeleteClientSecretResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.client_id):
            body['ClientId'] = request.client_id
        if not UtilClient.is_unset(request.client_name):
            body['ClientName'] = request.client_name
        if not UtilClient.is_unset(request.client_secret_id):
            body['ClientSecretId'] = request.client_secret_id
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeleteClientSecret',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeleteClientSecretResponse(),
            self.call_api(params, req, runtime)
        )

    async def delete_client_secret_with_options_async(
        self,
        request: agent_identity_20250901_models.DeleteClientSecretRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeleteClientSecretResponse:
        """
        @summary 删除IdentityProvider
        
        @param request: DeleteClientSecretRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeleteClientSecretResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.client_id):
            body['ClientId'] = request.client_id
        if not UtilClient.is_unset(request.client_name):
            body['ClientName'] = request.client_name
        if not UtilClient.is_unset(request.client_secret_id):
            body['ClientSecretId'] = request.client_secret_id
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeleteClientSecret',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeleteClientSecretResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def delete_client_secret(
        self,
        request: agent_identity_20250901_models.DeleteClientSecretRequest,
    ) -> agent_identity_20250901_models.DeleteClientSecretResponse:
        """
        @summary 删除IdentityProvider
        
        @param request: DeleteClientSecretRequest
        @return: DeleteClientSecretResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.delete_client_secret_with_options(request, runtime)

    async def delete_client_secret_async(
        self,
        request: agent_identity_20250901_models.DeleteClientSecretRequest,
    ) -> agent_identity_20250901_models.DeleteClientSecretResponse:
        """
        @summary 删除IdentityProvider
        
        @param request: DeleteClientSecretRequest
        @return: DeleteClientSecretResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.delete_client_secret_with_options_async(request, runtime)

    def delete_identity_provider_with_options(
        self,
        request: agent_identity_20250901_models.DeleteIdentityProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeleteIdentityProviderResponse:
        """
        @summary 删除IdentityProvider
        
        @param request: DeleteIdentityProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeleteIdentityProviderResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.identity_provider_name):
            body['IdentityProviderName'] = request.identity_provider_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeleteIdentityProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeleteIdentityProviderResponse(),
            self.call_api(params, req, runtime)
        )

    async def delete_identity_provider_with_options_async(
        self,
        request: agent_identity_20250901_models.DeleteIdentityProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeleteIdentityProviderResponse:
        """
        @summary 删除IdentityProvider
        
        @param request: DeleteIdentityProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeleteIdentityProviderResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.identity_provider_name):
            body['IdentityProviderName'] = request.identity_provider_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeleteIdentityProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeleteIdentityProviderResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def delete_identity_provider(
        self,
        request: agent_identity_20250901_models.DeleteIdentityProviderRequest,
    ) -> agent_identity_20250901_models.DeleteIdentityProviderResponse:
        """
        @summary 删除IdentityProvider
        
        @param request: DeleteIdentityProviderRequest
        @return: DeleteIdentityProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.delete_identity_provider_with_options(request, runtime)

    async def delete_identity_provider_async(
        self,
        request: agent_identity_20250901_models.DeleteIdentityProviderRequest,
    ) -> agent_identity_20250901_models.DeleteIdentityProviderResponse:
        """
        @summary 删除IdentityProvider
        
        @param request: DeleteIdentityProviderRequest
        @return: DeleteIdentityProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.delete_identity_provider_with_options_async(request, runtime)

    def delete_oauth_2credential_provider_with_options(
        self,
        request: agent_identity_20250901_models.DeleteOAuth2CredentialProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeleteOAuth2CredentialProviderResponse:
        """
        @summary 删除 OAuth2 凭证提供商
        
        @param request: DeleteOAuth2CredentialProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeleteOAuth2CredentialProviderResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.oauth_2credential_provider_name):
            body['OAuth2CredentialProviderName'] = request.oauth_2credential_provider_name
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeleteOAuth2CredentialProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeleteOAuth2CredentialProviderResponse(),
            self.call_api(params, req, runtime)
        )

    async def delete_oauth_2credential_provider_with_options_async(
        self,
        request: agent_identity_20250901_models.DeleteOAuth2CredentialProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeleteOAuth2CredentialProviderResponse:
        """
        @summary 删除 OAuth2 凭证提供商
        
        @param request: DeleteOAuth2CredentialProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeleteOAuth2CredentialProviderResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.oauth_2credential_provider_name):
            body['OAuth2CredentialProviderName'] = request.oauth_2credential_provider_name
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeleteOAuth2CredentialProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeleteOAuth2CredentialProviderResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def delete_oauth_2credential_provider(
        self,
        request: agent_identity_20250901_models.DeleteOAuth2CredentialProviderRequest,
    ) -> agent_identity_20250901_models.DeleteOAuth2CredentialProviderResponse:
        """
        @summary 删除 OAuth2 凭证提供商
        
        @param request: DeleteOAuth2CredentialProviderRequest
        @return: DeleteOAuth2CredentialProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.delete_oauth_2credential_provider_with_options(request, runtime)

    async def delete_oauth_2credential_provider_async(
        self,
        request: agent_identity_20250901_models.DeleteOAuth2CredentialProviderRequest,
    ) -> agent_identity_20250901_models.DeleteOAuth2CredentialProviderResponse:
        """
        @summary 删除 OAuth2 凭证提供商
        
        @param request: DeleteOAuth2CredentialProviderRequest
        @return: DeleteOAuth2CredentialProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.delete_oauth_2credential_provider_with_options_async(request, runtime)

    def delete_policy_with_options(
        self,
        request: agent_identity_20250901_models.DeletePolicyRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeletePolicyResponse:
        """
        @summary 删除一个权限策略
        
        @param request: DeletePolicyRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeletePolicyResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.policy_name):
            body['PolicyName'] = request.policy_name
        if not UtilClient.is_unset(request.policy_set_name):
            body['PolicySetName'] = request.policy_set_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeletePolicy',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeletePolicyResponse(),
            self.call_api(params, req, runtime)
        )

    async def delete_policy_with_options_async(
        self,
        request: agent_identity_20250901_models.DeletePolicyRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeletePolicyResponse:
        """
        @summary 删除一个权限策略
        
        @param request: DeletePolicyRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeletePolicyResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.policy_name):
            body['PolicyName'] = request.policy_name
        if not UtilClient.is_unset(request.policy_set_name):
            body['PolicySetName'] = request.policy_set_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeletePolicy',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeletePolicyResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def delete_policy(
        self,
        request: agent_identity_20250901_models.DeletePolicyRequest,
    ) -> agent_identity_20250901_models.DeletePolicyResponse:
        """
        @summary 删除一个权限策略
        
        @param request: DeletePolicyRequest
        @return: DeletePolicyResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.delete_policy_with_options(request, runtime)

    async def delete_policy_async(
        self,
        request: agent_identity_20250901_models.DeletePolicyRequest,
    ) -> agent_identity_20250901_models.DeletePolicyResponse:
        """
        @summary 删除一个权限策略
        
        @param request: DeletePolicyRequest
        @return: DeletePolicyResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.delete_policy_with_options_async(request, runtime)

    def delete_policy_set_with_options(
        self,
        request: agent_identity_20250901_models.DeletePolicySetRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeletePolicySetResponse:
        """
        @summary 删除一个权限策略集合
        
        @param request: DeletePolicySetRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeletePolicySetResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.policy_set_name):
            body['PolicySetName'] = request.policy_set_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeletePolicySet',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeletePolicySetResponse(),
            self.call_api(params, req, runtime)
        )

    async def delete_policy_set_with_options_async(
        self,
        request: agent_identity_20250901_models.DeletePolicySetRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeletePolicySetResponse:
        """
        @summary 删除一个权限策略集合
        
        @param request: DeletePolicySetRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeletePolicySetResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.policy_set_name):
            body['PolicySetName'] = request.policy_set_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeletePolicySet',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeletePolicySetResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def delete_policy_set(
        self,
        request: agent_identity_20250901_models.DeletePolicySetRequest,
    ) -> agent_identity_20250901_models.DeletePolicySetResponse:
        """
        @summary 删除一个权限策略集合
        
        @param request: DeletePolicySetRequest
        @return: DeletePolicySetResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.delete_policy_set_with_options(request, runtime)

    async def delete_policy_set_async(
        self,
        request: agent_identity_20250901_models.DeletePolicySetRequest,
    ) -> agent_identity_20250901_models.DeletePolicySetResponse:
        """
        @summary 删除一个权限策略集合
        
        @param request: DeletePolicySetRequest
        @return: DeletePolicySetResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.delete_policy_set_with_options_async(request, runtime)

    def delete_role_with_options(
        self,
        request: agent_identity_20250901_models.DeleteRoleRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeleteRoleResponse:
        """
        @summary 删除Role
        
        @param request: DeleteRoleRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeleteRoleResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.role_name):
            body['RoleName'] = request.role_name
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeleteRole',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeleteRoleResponse(),
            self.call_api(params, req, runtime)
        )

    async def delete_role_with_options_async(
        self,
        request: agent_identity_20250901_models.DeleteRoleRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeleteRoleResponse:
        """
        @summary 删除Role
        
        @param request: DeleteRoleRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeleteRoleResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.role_name):
            body['RoleName'] = request.role_name
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeleteRole',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeleteRoleResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def delete_role(
        self,
        request: agent_identity_20250901_models.DeleteRoleRequest,
    ) -> agent_identity_20250901_models.DeleteRoleResponse:
        """
        @summary 删除Role
        
        @param request: DeleteRoleRequest
        @return: DeleteRoleResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.delete_role_with_options(request, runtime)

    async def delete_role_async(
        self,
        request: agent_identity_20250901_models.DeleteRoleRequest,
    ) -> agent_identity_20250901_models.DeleteRoleResponse:
        """
        @summary 删除Role
        
        @param request: DeleteRoleRequest
        @return: DeleteRoleResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.delete_role_with_options_async(request, runtime)

    def delete_role_assignment_with_options(
        self,
        request: agent_identity_20250901_models.DeleteRoleAssignmentRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeleteRoleAssignmentResponse:
        """
        @summary 网关取消关联策略集
        
        @param request: DeleteRoleAssignmentRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeleteRoleAssignmentResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.principal_name):
            body['PrincipalName'] = request.principal_name
        if not UtilClient.is_unset(request.principal_type):
            body['PrincipalType'] = request.principal_type
        if not UtilClient.is_unset(request.role_name):
            body['RoleName'] = request.role_name
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeleteRoleAssignment',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeleteRoleAssignmentResponse(),
            self.call_api(params, req, runtime)
        )

    async def delete_role_assignment_with_options_async(
        self,
        request: agent_identity_20250901_models.DeleteRoleAssignmentRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeleteRoleAssignmentResponse:
        """
        @summary 网关取消关联策略集
        
        @param request: DeleteRoleAssignmentRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeleteRoleAssignmentResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.principal_name):
            body['PrincipalName'] = request.principal_name
        if not UtilClient.is_unset(request.principal_type):
            body['PrincipalType'] = request.principal_type
        if not UtilClient.is_unset(request.role_name):
            body['RoleName'] = request.role_name
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeleteRoleAssignment',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeleteRoleAssignmentResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def delete_role_assignment(
        self,
        request: agent_identity_20250901_models.DeleteRoleAssignmentRequest,
    ) -> agent_identity_20250901_models.DeleteRoleAssignmentResponse:
        """
        @summary 网关取消关联策略集
        
        @param request: DeleteRoleAssignmentRequest
        @return: DeleteRoleAssignmentResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.delete_role_assignment_with_options(request, runtime)

    async def delete_role_assignment_async(
        self,
        request: agent_identity_20250901_models.DeleteRoleAssignmentRequest,
    ) -> agent_identity_20250901_models.DeleteRoleAssignmentResponse:
        """
        @summary 网关取消关联策略集
        
        @param request: DeleteRoleAssignmentRequest
        @return: DeleteRoleAssignmentResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.delete_role_assignment_with_options_async(request, runtime)

    def delete_samlidentity_provider_certificate_with_options(
        self,
        request: agent_identity_20250901_models.DeleteSAMLIdentityProviderCertificateRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeleteSAMLIdentityProviderCertificateResponse:
        """
        @summary 删除WorkloadIdentity
        
        @param request: DeleteSAMLIdentityProviderCertificateRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeleteSAMLIdentityProviderCertificateResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.certificate_id):
            body['CertificateId'] = request.certificate_id
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeleteSAMLIdentityProviderCertificate',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeleteSAMLIdentityProviderCertificateResponse(),
            self.call_api(params, req, runtime)
        )

    async def delete_samlidentity_provider_certificate_with_options_async(
        self,
        request: agent_identity_20250901_models.DeleteSAMLIdentityProviderCertificateRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeleteSAMLIdentityProviderCertificateResponse:
        """
        @summary 删除WorkloadIdentity
        
        @param request: DeleteSAMLIdentityProviderCertificateRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeleteSAMLIdentityProviderCertificateResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.certificate_id):
            body['CertificateId'] = request.certificate_id
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeleteSAMLIdentityProviderCertificate',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeleteSAMLIdentityProviderCertificateResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def delete_samlidentity_provider_certificate(
        self,
        request: agent_identity_20250901_models.DeleteSAMLIdentityProviderCertificateRequest,
    ) -> agent_identity_20250901_models.DeleteSAMLIdentityProviderCertificateResponse:
        """
        @summary 删除WorkloadIdentity
        
        @param request: DeleteSAMLIdentityProviderCertificateRequest
        @return: DeleteSAMLIdentityProviderCertificateResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.delete_samlidentity_provider_certificate_with_options(request, runtime)

    async def delete_samlidentity_provider_certificate_async(
        self,
        request: agent_identity_20250901_models.DeleteSAMLIdentityProviderCertificateRequest,
    ) -> agent_identity_20250901_models.DeleteSAMLIdentityProviderCertificateResponse:
        """
        @summary 删除WorkloadIdentity
        
        @param request: DeleteSAMLIdentityProviderCertificateRequest
        @return: DeleteSAMLIdentityProviderCertificateResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.delete_samlidentity_provider_certificate_with_options_async(request, runtime)

    def delete_token_vault_with_options(
        self,
        request: agent_identity_20250901_models.DeleteTokenVaultRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeleteTokenVaultResponse:
        """
        @summary 删除一个指定的凭证库。
        
        @param request: DeleteTokenVaultRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeleteTokenVaultResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeleteTokenVault',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeleteTokenVaultResponse(),
            self.call_api(params, req, runtime)
        )

    async def delete_token_vault_with_options_async(
        self,
        request: agent_identity_20250901_models.DeleteTokenVaultRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeleteTokenVaultResponse:
        """
        @summary 删除一个指定的凭证库。
        
        @param request: DeleteTokenVaultRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeleteTokenVaultResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeleteTokenVault',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeleteTokenVaultResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def delete_token_vault(
        self,
        request: agent_identity_20250901_models.DeleteTokenVaultRequest,
    ) -> agent_identity_20250901_models.DeleteTokenVaultResponse:
        """
        @summary 删除一个指定的凭证库。
        
        @param request: DeleteTokenVaultRequest
        @return: DeleteTokenVaultResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.delete_token_vault_with_options(request, runtime)

    async def delete_token_vault_async(
        self,
        request: agent_identity_20250901_models.DeleteTokenVaultRequest,
    ) -> agent_identity_20250901_models.DeleteTokenVaultResponse:
        """
        @summary 删除一个指定的凭证库。
        
        @param request: DeleteTokenVaultRequest
        @return: DeleteTokenVaultResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.delete_token_vault_with_options_async(request, runtime)

    def delete_user_with_options(
        self,
        request: agent_identity_20250901_models.DeleteUserRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeleteUserResponse:
        """
        @summary 删除User
        
        @param request: DeleteUserRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeleteUserResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.user_name):
            body['UserName'] = request.user_name
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeleteUser',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeleteUserResponse(),
            self.call_api(params, req, runtime)
        )

    async def delete_user_with_options_async(
        self,
        request: agent_identity_20250901_models.DeleteUserRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeleteUserResponse:
        """
        @summary 删除User
        
        @param request: DeleteUserRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeleteUserResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.user_name):
            body['UserName'] = request.user_name
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeleteUser',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeleteUserResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def delete_user(
        self,
        request: agent_identity_20250901_models.DeleteUserRequest,
    ) -> agent_identity_20250901_models.DeleteUserResponse:
        """
        @summary 删除User
        
        @param request: DeleteUserRequest
        @return: DeleteUserResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.delete_user_with_options(request, runtime)

    async def delete_user_async(
        self,
        request: agent_identity_20250901_models.DeleteUserRequest,
    ) -> agent_identity_20250901_models.DeleteUserResponse:
        """
        @summary 删除User
        
        @param request: DeleteUserRequest
        @return: DeleteUserResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.delete_user_with_options_async(request, runtime)

    def delete_user_pool_with_options(
        self,
        request: agent_identity_20250901_models.DeleteUserPoolRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeleteUserPoolResponse:
        """
        @summary 删除UserPool
        
        @param request: DeleteUserPoolRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeleteUserPoolResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeleteUserPool',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeleteUserPoolResponse(),
            self.call_api(params, req, runtime)
        )

    async def delete_user_pool_with_options_async(
        self,
        request: agent_identity_20250901_models.DeleteUserPoolRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeleteUserPoolResponse:
        """
        @summary 删除UserPool
        
        @param request: DeleteUserPoolRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeleteUserPoolResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeleteUserPool',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeleteUserPoolResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def delete_user_pool(
        self,
        request: agent_identity_20250901_models.DeleteUserPoolRequest,
    ) -> agent_identity_20250901_models.DeleteUserPoolResponse:
        """
        @summary 删除UserPool
        
        @param request: DeleteUserPoolRequest
        @return: DeleteUserPoolResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.delete_user_pool_with_options(request, runtime)

    async def delete_user_pool_async(
        self,
        request: agent_identity_20250901_models.DeleteUserPoolRequest,
    ) -> agent_identity_20250901_models.DeleteUserPoolResponse:
        """
        @summary 删除UserPool
        
        @param request: DeleteUserPoolRequest
        @return: DeleteUserPoolResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.delete_user_pool_with_options_async(request, runtime)

    def delete_user_pool_client_with_options(
        self,
        request: agent_identity_20250901_models.DeleteUserPoolClientRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeleteUserPoolClientResponse:
        """
        @summary 删除WorkloadIdentity
        
        @param request: DeleteUserPoolClientRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeleteUserPoolClientResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.client_name):
            body['ClientName'] = request.client_name
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeleteUserPoolClient',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeleteUserPoolClientResponse(),
            self.call_api(params, req, runtime)
        )

    async def delete_user_pool_client_with_options_async(
        self,
        request: agent_identity_20250901_models.DeleteUserPoolClientRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeleteUserPoolClientResponse:
        """
        @summary 删除WorkloadIdentity
        
        @param request: DeleteUserPoolClientRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeleteUserPoolClientResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.client_name):
            body['ClientName'] = request.client_name
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeleteUserPoolClient',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeleteUserPoolClientResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def delete_user_pool_client(
        self,
        request: agent_identity_20250901_models.DeleteUserPoolClientRequest,
    ) -> agent_identity_20250901_models.DeleteUserPoolClientResponse:
        """
        @summary 删除WorkloadIdentity
        
        @param request: DeleteUserPoolClientRequest
        @return: DeleteUserPoolClientResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.delete_user_pool_client_with_options(request, runtime)

    async def delete_user_pool_client_async(
        self,
        request: agent_identity_20250901_models.DeleteUserPoolClientRequest,
    ) -> agent_identity_20250901_models.DeleteUserPoolClientResponse:
        """
        @summary 删除WorkloadIdentity
        
        @param request: DeleteUserPoolClientRequest
        @return: DeleteUserPoolClientResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.delete_user_pool_client_with_options_async(request, runtime)

    def delete_workload_identity_with_options(
        self,
        request: agent_identity_20250901_models.DeleteWorkloadIdentityRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeleteWorkloadIdentityResponse:
        """
        @summary 删除WorkloadIdentity
        
        @param request: DeleteWorkloadIdentityRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeleteWorkloadIdentityResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.workload_identity_name):
            body['WorkloadIdentityName'] = request.workload_identity_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeleteWorkloadIdentity',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeleteWorkloadIdentityResponse(),
            self.call_api(params, req, runtime)
        )

    async def delete_workload_identity_with_options_async(
        self,
        request: agent_identity_20250901_models.DeleteWorkloadIdentityRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DeleteWorkloadIdentityResponse:
        """
        @summary 删除WorkloadIdentity
        
        @param request: DeleteWorkloadIdentityRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DeleteWorkloadIdentityResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.workload_identity_name):
            body['WorkloadIdentityName'] = request.workload_identity_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DeleteWorkloadIdentity',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DeleteWorkloadIdentityResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def delete_workload_identity(
        self,
        request: agent_identity_20250901_models.DeleteWorkloadIdentityRequest,
    ) -> agent_identity_20250901_models.DeleteWorkloadIdentityResponse:
        """
        @summary 删除WorkloadIdentity
        
        @param request: DeleteWorkloadIdentityRequest
        @return: DeleteWorkloadIdentityResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.delete_workload_identity_with_options(request, runtime)

    async def delete_workload_identity_async(
        self,
        request: agent_identity_20250901_models.DeleteWorkloadIdentityRequest,
    ) -> agent_identity_20250901_models.DeleteWorkloadIdentityResponse:
        """
        @summary 删除WorkloadIdentity
        
        @param request: DeleteWorkloadIdentityRequest
        @return: DeleteWorkloadIdentityResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.delete_workload_identity_with_options_async(request, runtime)

    def detach_policy_set_from_gateway_with_options(
        self,
        request: agent_identity_20250901_models.DetachPolicySetFromGatewayRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DetachPolicySetFromGatewayResponse:
        """
        @summary 网关取消关联策略集
        
        @param request: DetachPolicySetFromGatewayRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DetachPolicySetFromGatewayResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.gateway_arn):
            body['GatewayArn'] = request.gateway_arn
        if not UtilClient.is_unset(request.policy_set_name):
            body['PolicySetName'] = request.policy_set_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DetachPolicySetFromGateway',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DetachPolicySetFromGatewayResponse(),
            self.call_api(params, req, runtime)
        )

    async def detach_policy_set_from_gateway_with_options_async(
        self,
        request: agent_identity_20250901_models.DetachPolicySetFromGatewayRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.DetachPolicySetFromGatewayResponse:
        """
        @summary 网关取消关联策略集
        
        @param request: DetachPolicySetFromGatewayRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: DetachPolicySetFromGatewayResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.gateway_arn):
            body['GatewayArn'] = request.gateway_arn
        if not UtilClient.is_unset(request.policy_set_name):
            body['PolicySetName'] = request.policy_set_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='DetachPolicySetFromGateway',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.DetachPolicySetFromGatewayResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def detach_policy_set_from_gateway(
        self,
        request: agent_identity_20250901_models.DetachPolicySetFromGatewayRequest,
    ) -> agent_identity_20250901_models.DetachPolicySetFromGatewayResponse:
        """
        @summary 网关取消关联策略集
        
        @param request: DetachPolicySetFromGatewayRequest
        @return: DetachPolicySetFromGatewayResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.detach_policy_set_from_gateway_with_options(request, runtime)

    async def detach_policy_set_from_gateway_async(
        self,
        request: agent_identity_20250901_models.DetachPolicySetFromGatewayRequest,
    ) -> agent_identity_20250901_models.DetachPolicySetFromGatewayResponse:
        """
        @summary 网关取消关联策略集
        
        @param request: DetachPolicySetFromGatewayRequest
        @return: DetachPolicySetFromGatewayResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.detach_policy_set_from_gateway_with_options_async(request, runtime)

    def get_apikey_credential_provider_with_options(
        self,
        request: agent_identity_20250901_models.GetAPIKeyCredentialProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetAPIKeyCredentialProviderResponse:
        """
        @summary 查询一个 API 密钥凭证提供商
        
        @param request: GetAPIKeyCredentialProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetAPIKeyCredentialProviderResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.apikey_credential_provider_name):
            body['APIKeyCredentialProviderName'] = request.apikey_credential_provider_name
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetAPIKeyCredentialProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetAPIKeyCredentialProviderResponse(),
            self.call_api(params, req, runtime)
        )

    async def get_apikey_credential_provider_with_options_async(
        self,
        request: agent_identity_20250901_models.GetAPIKeyCredentialProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetAPIKeyCredentialProviderResponse:
        """
        @summary 查询一个 API 密钥凭证提供商
        
        @param request: GetAPIKeyCredentialProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetAPIKeyCredentialProviderResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.apikey_credential_provider_name):
            body['APIKeyCredentialProviderName'] = request.apikey_credential_provider_name
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetAPIKeyCredentialProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetAPIKeyCredentialProviderResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def get_apikey_credential_provider(
        self,
        request: agent_identity_20250901_models.GetAPIKeyCredentialProviderRequest,
    ) -> agent_identity_20250901_models.GetAPIKeyCredentialProviderResponse:
        """
        @summary 查询一个 API 密钥凭证提供商
        
        @param request: GetAPIKeyCredentialProviderRequest
        @return: GetAPIKeyCredentialProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.get_apikey_credential_provider_with_options(request, runtime)

    async def get_apikey_credential_provider_async(
        self,
        request: agent_identity_20250901_models.GetAPIKeyCredentialProviderRequest,
    ) -> agent_identity_20250901_models.GetAPIKeyCredentialProviderResponse:
        """
        @summary 查询一个 API 密钥凭证提供商
        
        @param request: GetAPIKeyCredentialProviderRequest
        @return: GetAPIKeyCredentialProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.get_apikey_credential_provider_with_options_async(request, runtime)

    def get_gateway_policy_config_with_options(
        self,
        request: agent_identity_20250901_models.GetGatewayPolicyConfigRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetGatewayPolicyConfigResponse:
        """
        @summary 查询网关策略配置
        
        @param request: GetGatewayPolicyConfigRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetGatewayPolicyConfigResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.gateway_arn):
            body['GatewayArn'] = request.gateway_arn
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetGatewayPolicyConfig',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetGatewayPolicyConfigResponse(),
            self.call_api(params, req, runtime)
        )

    async def get_gateway_policy_config_with_options_async(
        self,
        request: agent_identity_20250901_models.GetGatewayPolicyConfigRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetGatewayPolicyConfigResponse:
        """
        @summary 查询网关策略配置
        
        @param request: GetGatewayPolicyConfigRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetGatewayPolicyConfigResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.gateway_arn):
            body['GatewayArn'] = request.gateway_arn
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetGatewayPolicyConfig',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetGatewayPolicyConfigResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def get_gateway_policy_config(
        self,
        request: agent_identity_20250901_models.GetGatewayPolicyConfigRequest,
    ) -> agent_identity_20250901_models.GetGatewayPolicyConfigResponse:
        """
        @summary 查询网关策略配置
        
        @param request: GetGatewayPolicyConfigRequest
        @return: GetGatewayPolicyConfigResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.get_gateway_policy_config_with_options(request, runtime)

    async def get_gateway_policy_config_async(
        self,
        request: agent_identity_20250901_models.GetGatewayPolicyConfigRequest,
    ) -> agent_identity_20250901_models.GetGatewayPolicyConfigResponse:
        """
        @summary 查询网关策略配置
        
        @param request: GetGatewayPolicyConfigRequest
        @return: GetGatewayPolicyConfigResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.get_gateway_policy_config_with_options_async(request, runtime)

    def get_identity_provider_with_options(
        self,
        request: agent_identity_20250901_models.GetIdentityProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetIdentityProviderResponse:
        """
        @summary 创建应用
        
        @param request: GetIdentityProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetIdentityProviderResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.identity_provider_name):
            body['IdentityProviderName'] = request.identity_provider_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetIdentityProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetIdentityProviderResponse(),
            self.call_api(params, req, runtime)
        )

    async def get_identity_provider_with_options_async(
        self,
        request: agent_identity_20250901_models.GetIdentityProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetIdentityProviderResponse:
        """
        @summary 创建应用
        
        @param request: GetIdentityProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetIdentityProviderResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.identity_provider_name):
            body['IdentityProviderName'] = request.identity_provider_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetIdentityProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetIdentityProviderResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def get_identity_provider(
        self,
        request: agent_identity_20250901_models.GetIdentityProviderRequest,
    ) -> agent_identity_20250901_models.GetIdentityProviderResponse:
        """
        @summary 创建应用
        
        @param request: GetIdentityProviderRequest
        @return: GetIdentityProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.get_identity_provider_with_options(request, runtime)

    async def get_identity_provider_async(
        self,
        request: agent_identity_20250901_models.GetIdentityProviderRequest,
    ) -> agent_identity_20250901_models.GetIdentityProviderResponse:
        """
        @summary 创建应用
        
        @param request: GetIdentityProviderRequest
        @return: GetIdentityProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.get_identity_provider_with_options_async(request, runtime)

    def get_oauth_2credential_provider_with_options(
        self,
        request: agent_identity_20250901_models.GetOAuth2CredentialProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetOAuth2CredentialProviderResponse:
        """
        @summary 查询 OAuth2 凭证提供商
        
        @param request: GetOAuth2CredentialProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetOAuth2CredentialProviderResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.oauth_2credential_provider_name):
            body['OAuth2CredentialProviderName'] = request.oauth_2credential_provider_name
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetOAuth2CredentialProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetOAuth2CredentialProviderResponse(),
            self.call_api(params, req, runtime)
        )

    async def get_oauth_2credential_provider_with_options_async(
        self,
        request: agent_identity_20250901_models.GetOAuth2CredentialProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetOAuth2CredentialProviderResponse:
        """
        @summary 查询 OAuth2 凭证提供商
        
        @param request: GetOAuth2CredentialProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetOAuth2CredentialProviderResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.oauth_2credential_provider_name):
            body['OAuth2CredentialProviderName'] = request.oauth_2credential_provider_name
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetOAuth2CredentialProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetOAuth2CredentialProviderResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def get_oauth_2credential_provider(
        self,
        request: agent_identity_20250901_models.GetOAuth2CredentialProviderRequest,
    ) -> agent_identity_20250901_models.GetOAuth2CredentialProviderResponse:
        """
        @summary 查询 OAuth2 凭证提供商
        
        @param request: GetOAuth2CredentialProviderRequest
        @return: GetOAuth2CredentialProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.get_oauth_2credential_provider_with_options(request, runtime)

    async def get_oauth_2credential_provider_async(
        self,
        request: agent_identity_20250901_models.GetOAuth2CredentialProviderRequest,
    ) -> agent_identity_20250901_models.GetOAuth2CredentialProviderResponse:
        """
        @summary 查询 OAuth2 凭证提供商
        
        @param request: GetOAuth2CredentialProviderRequest
        @return: GetOAuth2CredentialProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.get_oauth_2credential_provider_with_options_async(request, runtime)

    def get_policy_with_options(
        self,
        request: agent_identity_20250901_models.GetPolicyRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetPolicyResponse:
        """
        @summary 查询一个 权限策略
        
        @param request: GetPolicyRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetPolicyResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.policy_name):
            body['PolicyName'] = request.policy_name
        if not UtilClient.is_unset(request.policy_set_name):
            body['PolicySetName'] = request.policy_set_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetPolicy',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetPolicyResponse(),
            self.call_api(params, req, runtime)
        )

    async def get_policy_with_options_async(
        self,
        request: agent_identity_20250901_models.GetPolicyRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetPolicyResponse:
        """
        @summary 查询一个 权限策略
        
        @param request: GetPolicyRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetPolicyResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.policy_name):
            body['PolicyName'] = request.policy_name
        if not UtilClient.is_unset(request.policy_set_name):
            body['PolicySetName'] = request.policy_set_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetPolicy',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetPolicyResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def get_policy(
        self,
        request: agent_identity_20250901_models.GetPolicyRequest,
    ) -> agent_identity_20250901_models.GetPolicyResponse:
        """
        @summary 查询一个 权限策略
        
        @param request: GetPolicyRequest
        @return: GetPolicyResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.get_policy_with_options(request, runtime)

    async def get_policy_async(
        self,
        request: agent_identity_20250901_models.GetPolicyRequest,
    ) -> agent_identity_20250901_models.GetPolicyResponse:
        """
        @summary 查询一个 权限策略
        
        @param request: GetPolicyRequest
        @return: GetPolicyResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.get_policy_with_options_async(request, runtime)

    def get_policy_set_with_options(
        self,
        request: agent_identity_20250901_models.GetPolicySetRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetPolicySetResponse:
        """
        @summary 查询一个 权限策略集合
        
        @param request: GetPolicySetRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetPolicySetResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.policy_set_name):
            body['PolicySetName'] = request.policy_set_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetPolicySet',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetPolicySetResponse(),
            self.call_api(params, req, runtime)
        )

    async def get_policy_set_with_options_async(
        self,
        request: agent_identity_20250901_models.GetPolicySetRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetPolicySetResponse:
        """
        @summary 查询一个 权限策略集合
        
        @param request: GetPolicySetRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetPolicySetResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.policy_set_name):
            body['PolicySetName'] = request.policy_set_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetPolicySet',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetPolicySetResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def get_policy_set(
        self,
        request: agent_identity_20250901_models.GetPolicySetRequest,
    ) -> agent_identity_20250901_models.GetPolicySetResponse:
        """
        @summary 查询一个 权限策略集合
        
        @param request: GetPolicySetRequest
        @return: GetPolicySetResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.get_policy_set_with_options(request, runtime)

    async def get_policy_set_async(
        self,
        request: agent_identity_20250901_models.GetPolicySetRequest,
    ) -> agent_identity_20250901_models.GetPolicySetResponse:
        """
        @summary 查询一个 权限策略集合
        
        @param request: GetPolicySetRequest
        @return: GetPolicySetResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.get_policy_set_with_options_async(request, runtime)

    def get_role_with_options(
        self,
        request: agent_identity_20250901_models.GetRoleRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetRoleResponse:
        """
        @summary 获取Role
        
        @param request: GetRoleRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetRoleResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.role_name):
            body['RoleName'] = request.role_name
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetRole',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetRoleResponse(),
            self.call_api(params, req, runtime)
        )

    async def get_role_with_options_async(
        self,
        request: agent_identity_20250901_models.GetRoleRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetRoleResponse:
        """
        @summary 获取Role
        
        @param request: GetRoleRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetRoleResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.role_name):
            body['RoleName'] = request.role_name
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetRole',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetRoleResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def get_role(
        self,
        request: agent_identity_20250901_models.GetRoleRequest,
    ) -> agent_identity_20250901_models.GetRoleResponse:
        """
        @summary 获取Role
        
        @param request: GetRoleRequest
        @return: GetRoleResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.get_role_with_options(request, runtime)

    async def get_role_async(
        self,
        request: agent_identity_20250901_models.GetRoleRequest,
    ) -> agent_identity_20250901_models.GetRoleResponse:
        """
        @summary 获取Role
        
        @param request: GetRoleRequest
        @return: GetRoleResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.get_role_with_options_async(request, runtime)

    def get_samlidentity_provider_with_options(
        self,
        request: agent_identity_20250901_models.GetSAMLIdentityProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetSAMLIdentityProviderResponse:
        """
        @summary 创建应用
        
        @param request: GetSAMLIdentityProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetSAMLIdentityProviderResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetSAMLIdentityProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetSAMLIdentityProviderResponse(),
            self.call_api(params, req, runtime)
        )

    async def get_samlidentity_provider_with_options_async(
        self,
        request: agent_identity_20250901_models.GetSAMLIdentityProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetSAMLIdentityProviderResponse:
        """
        @summary 创建应用
        
        @param request: GetSAMLIdentityProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetSAMLIdentityProviderResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetSAMLIdentityProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetSAMLIdentityProviderResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def get_samlidentity_provider(
        self,
        request: agent_identity_20250901_models.GetSAMLIdentityProviderRequest,
    ) -> agent_identity_20250901_models.GetSAMLIdentityProviderResponse:
        """
        @summary 创建应用
        
        @param request: GetSAMLIdentityProviderRequest
        @return: GetSAMLIdentityProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.get_samlidentity_provider_with_options(request, runtime)

    async def get_samlidentity_provider_async(
        self,
        request: agent_identity_20250901_models.GetSAMLIdentityProviderRequest,
    ) -> agent_identity_20250901_models.GetSAMLIdentityProviderResponse:
        """
        @summary 创建应用
        
        @param request: GetSAMLIdentityProviderRequest
        @return: GetSAMLIdentityProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.get_samlidentity_provider_with_options_async(request, runtime)

    def get_samlservice_provider_info_with_options(
        self,
        request: agent_identity_20250901_models.GetSAMLServiceProviderInfoRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetSAMLServiceProviderInfoResponse:
        """
        @summary 创建应用
        
        @param request: GetSAMLServiceProviderInfoRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetSAMLServiceProviderInfoResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetSAMLServiceProviderInfo',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetSAMLServiceProviderInfoResponse(),
            self.call_api(params, req, runtime)
        )

    async def get_samlservice_provider_info_with_options_async(
        self,
        request: agent_identity_20250901_models.GetSAMLServiceProviderInfoRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetSAMLServiceProviderInfoResponse:
        """
        @summary 创建应用
        
        @param request: GetSAMLServiceProviderInfoRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetSAMLServiceProviderInfoResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetSAMLServiceProviderInfo',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetSAMLServiceProviderInfoResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def get_samlservice_provider_info(
        self,
        request: agent_identity_20250901_models.GetSAMLServiceProviderInfoRequest,
    ) -> agent_identity_20250901_models.GetSAMLServiceProviderInfoResponse:
        """
        @summary 创建应用
        
        @param request: GetSAMLServiceProviderInfoRequest
        @return: GetSAMLServiceProviderInfoResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.get_samlservice_provider_info_with_options(request, runtime)

    async def get_samlservice_provider_info_async(
        self,
        request: agent_identity_20250901_models.GetSAMLServiceProviderInfoRequest,
    ) -> agent_identity_20250901_models.GetSAMLServiceProviderInfoResponse:
        """
        @summary 创建应用
        
        @param request: GetSAMLServiceProviderInfoRequest
        @return: GetSAMLServiceProviderInfoResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.get_samlservice_provider_info_with_options_async(request, runtime)

    def get_token_vault_with_options(
        self,
        request: agent_identity_20250901_models.GetTokenVaultRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetTokenVaultResponse:
        """
        @summary 获取指定凭证库的详细配置。
        
        @param request: GetTokenVaultRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetTokenVaultResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetTokenVault',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetTokenVaultResponse(),
            self.call_api(params, req, runtime)
        )

    async def get_token_vault_with_options_async(
        self,
        request: agent_identity_20250901_models.GetTokenVaultRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetTokenVaultResponse:
        """
        @summary 获取指定凭证库的详细配置。
        
        @param request: GetTokenVaultRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetTokenVaultResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetTokenVault',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetTokenVaultResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def get_token_vault(
        self,
        request: agent_identity_20250901_models.GetTokenVaultRequest,
    ) -> agent_identity_20250901_models.GetTokenVaultResponse:
        """
        @summary 获取指定凭证库的详细配置。
        
        @param request: GetTokenVaultRequest
        @return: GetTokenVaultResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.get_token_vault_with_options(request, runtime)

    async def get_token_vault_async(
        self,
        request: agent_identity_20250901_models.GetTokenVaultRequest,
    ) -> agent_identity_20250901_models.GetTokenVaultResponse:
        """
        @summary 获取指定凭证库的详细配置。
        
        @param request: GetTokenVaultRequest
        @return: GetTokenVaultResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.get_token_vault_with_options_async(request, runtime)

    def get_user_with_options(
        self,
        request: agent_identity_20250901_models.GetUserRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetUserResponse:
        """
        @summary 获取用户
        
        @param request: GetUserRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetUserResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.user_name):
            body['UserName'] = request.user_name
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetUser',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetUserResponse(),
            self.call_api(params, req, runtime)
        )

    async def get_user_with_options_async(
        self,
        request: agent_identity_20250901_models.GetUserRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetUserResponse:
        """
        @summary 获取用户
        
        @param request: GetUserRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetUserResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.user_name):
            body['UserName'] = request.user_name
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetUser',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetUserResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def get_user(
        self,
        request: agent_identity_20250901_models.GetUserRequest,
    ) -> agent_identity_20250901_models.GetUserResponse:
        """
        @summary 获取用户
        
        @param request: GetUserRequest
        @return: GetUserResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.get_user_with_options(request, runtime)

    async def get_user_async(
        self,
        request: agent_identity_20250901_models.GetUserRequest,
    ) -> agent_identity_20250901_models.GetUserResponse:
        """
        @summary 获取用户
        
        @param request: GetUserRequest
        @return: GetUserResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.get_user_with_options_async(request, runtime)

    def get_user_pool_with_options(
        self,
        request: agent_identity_20250901_models.GetUserPoolRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetUserPoolResponse:
        """
        @summary 获取UserPool
        
        @param request: GetUserPoolRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetUserPoolResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetUserPool',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetUserPoolResponse(),
            self.call_api(params, req, runtime)
        )

    async def get_user_pool_with_options_async(
        self,
        request: agent_identity_20250901_models.GetUserPoolRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetUserPoolResponse:
        """
        @summary 获取UserPool
        
        @param request: GetUserPoolRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetUserPoolResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetUserPool',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetUserPoolResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def get_user_pool(
        self,
        request: agent_identity_20250901_models.GetUserPoolRequest,
    ) -> agent_identity_20250901_models.GetUserPoolResponse:
        """
        @summary 获取UserPool
        
        @param request: GetUserPoolRequest
        @return: GetUserPoolResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.get_user_pool_with_options(request, runtime)

    async def get_user_pool_async(
        self,
        request: agent_identity_20250901_models.GetUserPoolRequest,
    ) -> agent_identity_20250901_models.GetUserPoolResponse:
        """
        @summary 获取UserPool
        
        @param request: GetUserPoolRequest
        @return: GetUserPoolResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.get_user_pool_with_options_async(request, runtime)

    def get_user_pool_client_with_options(
        self,
        request: agent_identity_20250901_models.GetUserPoolClientRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetUserPoolClientResponse:
        """
        @summary 创建应用
        
        @param request: GetUserPoolClientRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetUserPoolClientResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.client_name):
            body['ClientName'] = request.client_name
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetUserPoolClient',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetUserPoolClientResponse(),
            self.call_api(params, req, runtime)
        )

    async def get_user_pool_client_with_options_async(
        self,
        request: agent_identity_20250901_models.GetUserPoolClientRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetUserPoolClientResponse:
        """
        @summary 创建应用
        
        @param request: GetUserPoolClientRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetUserPoolClientResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.client_name):
            body['ClientName'] = request.client_name
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetUserPoolClient',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetUserPoolClientResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def get_user_pool_client(
        self,
        request: agent_identity_20250901_models.GetUserPoolClientRequest,
    ) -> agent_identity_20250901_models.GetUserPoolClientResponse:
        """
        @summary 创建应用
        
        @param request: GetUserPoolClientRequest
        @return: GetUserPoolClientResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.get_user_pool_client_with_options(request, runtime)

    async def get_user_pool_client_async(
        self,
        request: agent_identity_20250901_models.GetUserPoolClientRequest,
    ) -> agent_identity_20250901_models.GetUserPoolClientResponse:
        """
        @summary 创建应用
        
        @param request: GetUserPoolClientRequest
        @return: GetUserPoolClientResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.get_user_pool_client_with_options_async(request, runtime)

    def get_workload_identity_with_options(
        self,
        request: agent_identity_20250901_models.GetWorkloadIdentityRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetWorkloadIdentityResponse:
        """
        @summary 创建应用
        
        @param request: GetWorkloadIdentityRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetWorkloadIdentityResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.workload_identity_name):
            body['WorkloadIdentityName'] = request.workload_identity_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetWorkloadIdentity',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetWorkloadIdentityResponse(),
            self.call_api(params, req, runtime)
        )

    async def get_workload_identity_with_options_async(
        self,
        request: agent_identity_20250901_models.GetWorkloadIdentityRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.GetWorkloadIdentityResponse:
        """
        @summary 创建应用
        
        @param request: GetWorkloadIdentityRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: GetWorkloadIdentityResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.workload_identity_name):
            body['WorkloadIdentityName'] = request.workload_identity_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='GetWorkloadIdentity',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.GetWorkloadIdentityResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def get_workload_identity(
        self,
        request: agent_identity_20250901_models.GetWorkloadIdentityRequest,
    ) -> agent_identity_20250901_models.GetWorkloadIdentityResponse:
        """
        @summary 创建应用
        
        @param request: GetWorkloadIdentityRequest
        @return: GetWorkloadIdentityResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.get_workload_identity_with_options(request, runtime)

    async def get_workload_identity_async(
        self,
        request: agent_identity_20250901_models.GetWorkloadIdentityRequest,
    ) -> agent_identity_20250901_models.GetWorkloadIdentityResponse:
        """
        @summary 创建应用
        
        @param request: GetWorkloadIdentityRequest
        @return: GetWorkloadIdentityResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.get_workload_identity_with_options_async(request, runtime)

    def list_apikey_credential_providers_with_options(
        self,
        request: agent_identity_20250901_models.ListAPIKeyCredentialProvidersRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListAPIKeyCredentialProvidersResponse:
        """
        @summary 列出 API 密钥凭证提供商
        
        @param request: ListAPIKeyCredentialProvidersRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListAPIKeyCredentialProvidersResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.max_results):
            body['MaxResults'] = request.max_results
        if not UtilClient.is_unset(request.next_token):
            body['NextToken'] = request.next_token
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListAPIKeyCredentialProviders',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListAPIKeyCredentialProvidersResponse(),
            self.call_api(params, req, runtime)
        )

    async def list_apikey_credential_providers_with_options_async(
        self,
        request: agent_identity_20250901_models.ListAPIKeyCredentialProvidersRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListAPIKeyCredentialProvidersResponse:
        """
        @summary 列出 API 密钥凭证提供商
        
        @param request: ListAPIKeyCredentialProvidersRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListAPIKeyCredentialProvidersResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.max_results):
            body['MaxResults'] = request.max_results
        if not UtilClient.is_unset(request.next_token):
            body['NextToken'] = request.next_token
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListAPIKeyCredentialProviders',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListAPIKeyCredentialProvidersResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def list_apikey_credential_providers(
        self,
        request: agent_identity_20250901_models.ListAPIKeyCredentialProvidersRequest,
    ) -> agent_identity_20250901_models.ListAPIKeyCredentialProvidersResponse:
        """
        @summary 列出 API 密钥凭证提供商
        
        @param request: ListAPIKeyCredentialProvidersRequest
        @return: ListAPIKeyCredentialProvidersResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.list_apikey_credential_providers_with_options(request, runtime)

    async def list_apikey_credential_providers_async(
        self,
        request: agent_identity_20250901_models.ListAPIKeyCredentialProvidersRequest,
    ) -> agent_identity_20250901_models.ListAPIKeyCredentialProvidersResponse:
        """
        @summary 列出 API 密钥凭证提供商
        
        @param request: ListAPIKeyCredentialProvidersRequest
        @return: ListAPIKeyCredentialProvidersResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.list_apikey_credential_providers_with_options_async(request, runtime)

    def list_client_secrets_with_options(
        self,
        request: agent_identity_20250901_models.ListClientSecretsRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListClientSecretsResponse:
        """
        @summary 列出IdentityProvider
        
        @param request: ListClientSecretsRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListClientSecretsResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.client_name):
            body['ClientName'] = request.client_name
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListClientSecrets',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListClientSecretsResponse(),
            self.call_api(params, req, runtime)
        )

    async def list_client_secrets_with_options_async(
        self,
        request: agent_identity_20250901_models.ListClientSecretsRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListClientSecretsResponse:
        """
        @summary 列出IdentityProvider
        
        @param request: ListClientSecretsRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListClientSecretsResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.client_name):
            body['ClientName'] = request.client_name
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListClientSecrets',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListClientSecretsResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def list_client_secrets(
        self,
        request: agent_identity_20250901_models.ListClientSecretsRequest,
    ) -> agent_identity_20250901_models.ListClientSecretsResponse:
        """
        @summary 列出IdentityProvider
        
        @param request: ListClientSecretsRequest
        @return: ListClientSecretsResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.list_client_secrets_with_options(request, runtime)

    async def list_client_secrets_async(
        self,
        request: agent_identity_20250901_models.ListClientSecretsRequest,
    ) -> agent_identity_20250901_models.ListClientSecretsResponse:
        """
        @summary 列出IdentityProvider
        
        @param request: ListClientSecretsRequest
        @return: ListClientSecretsResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.list_client_secrets_with_options_async(request, runtime)

    def list_identity_providers_with_options(
        self,
        request: agent_identity_20250901_models.ListIdentityProvidersRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListIdentityProvidersResponse:
        """
        @summary 列出IdentityProvider
        
        @param request: ListIdentityProvidersRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListIdentityProvidersResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.max_results):
            body['MaxResults'] = request.max_results
        if not UtilClient.is_unset(request.next_token):
            body['NextToken'] = request.next_token
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListIdentityProviders',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListIdentityProvidersResponse(),
            self.call_api(params, req, runtime)
        )

    async def list_identity_providers_with_options_async(
        self,
        request: agent_identity_20250901_models.ListIdentityProvidersRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListIdentityProvidersResponse:
        """
        @summary 列出IdentityProvider
        
        @param request: ListIdentityProvidersRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListIdentityProvidersResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.max_results):
            body['MaxResults'] = request.max_results
        if not UtilClient.is_unset(request.next_token):
            body['NextToken'] = request.next_token
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListIdentityProviders',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListIdentityProvidersResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def list_identity_providers(
        self,
        request: agent_identity_20250901_models.ListIdentityProvidersRequest,
    ) -> agent_identity_20250901_models.ListIdentityProvidersResponse:
        """
        @summary 列出IdentityProvider
        
        @param request: ListIdentityProvidersRequest
        @return: ListIdentityProvidersResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.list_identity_providers_with_options(request, runtime)

    async def list_identity_providers_async(
        self,
        request: agent_identity_20250901_models.ListIdentityProvidersRequest,
    ) -> agent_identity_20250901_models.ListIdentityProvidersResponse:
        """
        @summary 列出IdentityProvider
        
        @param request: ListIdentityProvidersRequest
        @return: ListIdentityProvidersResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.list_identity_providers_with_options_async(request, runtime)

    def list_oauth_2credential_providers_with_options(
        self,
        request: agent_identity_20250901_models.ListOAuth2CredentialProvidersRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListOAuth2CredentialProvidersResponse:
        """
        @summary 列出 OAuth2 凭证提供商
        
        @param request: ListOAuth2CredentialProvidersRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListOAuth2CredentialProvidersResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.max_results):
            body['MaxResults'] = request.max_results
        if not UtilClient.is_unset(request.next_token):
            body['NextToken'] = request.next_token
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListOAuth2CredentialProviders',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListOAuth2CredentialProvidersResponse(),
            self.call_api(params, req, runtime)
        )

    async def list_oauth_2credential_providers_with_options_async(
        self,
        request: agent_identity_20250901_models.ListOAuth2CredentialProvidersRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListOAuth2CredentialProvidersResponse:
        """
        @summary 列出 OAuth2 凭证提供商
        
        @param request: ListOAuth2CredentialProvidersRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListOAuth2CredentialProvidersResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.max_results):
            body['MaxResults'] = request.max_results
        if not UtilClient.is_unset(request.next_token):
            body['NextToken'] = request.next_token
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListOAuth2CredentialProviders',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListOAuth2CredentialProvidersResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def list_oauth_2credential_providers(
        self,
        request: agent_identity_20250901_models.ListOAuth2CredentialProvidersRequest,
    ) -> agent_identity_20250901_models.ListOAuth2CredentialProvidersResponse:
        """
        @summary 列出 OAuth2 凭证提供商
        
        @param request: ListOAuth2CredentialProvidersRequest
        @return: ListOAuth2CredentialProvidersResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.list_oauth_2credential_providers_with_options(request, runtime)

    async def list_oauth_2credential_providers_async(
        self,
        request: agent_identity_20250901_models.ListOAuth2CredentialProvidersRequest,
    ) -> agent_identity_20250901_models.ListOAuth2CredentialProvidersResponse:
        """
        @summary 列出 OAuth2 凭证提供商
        
        @param request: ListOAuth2CredentialProvidersRequest
        @return: ListOAuth2CredentialProvidersResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.list_oauth_2credential_providers_with_options_async(request, runtime)

    def list_policies_with_options(
        self,
        request: agent_identity_20250901_models.ListPoliciesRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListPoliciesResponse:
        """
        @summary 列出权限策略
        
        @param request: ListPoliciesRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListPoliciesResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.max_results):
            body['MaxResults'] = request.max_results
        if not UtilClient.is_unset(request.next_token):
            body['NextToken'] = request.next_token
        if not UtilClient.is_unset(request.policy_set_name):
            body['PolicySetName'] = request.policy_set_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListPolicies',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListPoliciesResponse(),
            self.call_api(params, req, runtime)
        )

    async def list_policies_with_options_async(
        self,
        request: agent_identity_20250901_models.ListPoliciesRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListPoliciesResponse:
        """
        @summary 列出权限策略
        
        @param request: ListPoliciesRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListPoliciesResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.max_results):
            body['MaxResults'] = request.max_results
        if not UtilClient.is_unset(request.next_token):
            body['NextToken'] = request.next_token
        if not UtilClient.is_unset(request.policy_set_name):
            body['PolicySetName'] = request.policy_set_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListPolicies',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListPoliciesResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def list_policies(
        self,
        request: agent_identity_20250901_models.ListPoliciesRequest,
    ) -> agent_identity_20250901_models.ListPoliciesResponse:
        """
        @summary 列出权限策略
        
        @param request: ListPoliciesRequest
        @return: ListPoliciesResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.list_policies_with_options(request, runtime)

    async def list_policies_async(
        self,
        request: agent_identity_20250901_models.ListPoliciesRequest,
    ) -> agent_identity_20250901_models.ListPoliciesResponse:
        """
        @summary 列出权限策略
        
        @param request: ListPoliciesRequest
        @return: ListPoliciesResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.list_policies_with_options_async(request, runtime)

    def list_policy_set_attached_gateways_with_options(
        self,
        request: agent_identity_20250901_models.ListPolicySetAttachedGatewaysRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListPolicySetAttachedGatewaysResponse:
        """
        @summary 列出网关策略配置
        
        @param request: ListPolicySetAttachedGatewaysRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListPolicySetAttachedGatewaysResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.max_results):
            body['MaxResults'] = request.max_results
        if not UtilClient.is_unset(request.next_token):
            body['NextToken'] = request.next_token
        if not UtilClient.is_unset(request.policy_set_name):
            body['PolicySetName'] = request.policy_set_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListPolicySetAttachedGateways',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListPolicySetAttachedGatewaysResponse(),
            self.call_api(params, req, runtime)
        )

    async def list_policy_set_attached_gateways_with_options_async(
        self,
        request: agent_identity_20250901_models.ListPolicySetAttachedGatewaysRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListPolicySetAttachedGatewaysResponse:
        """
        @summary 列出网关策略配置
        
        @param request: ListPolicySetAttachedGatewaysRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListPolicySetAttachedGatewaysResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.max_results):
            body['MaxResults'] = request.max_results
        if not UtilClient.is_unset(request.next_token):
            body['NextToken'] = request.next_token
        if not UtilClient.is_unset(request.policy_set_name):
            body['PolicySetName'] = request.policy_set_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListPolicySetAttachedGateways',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListPolicySetAttachedGatewaysResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def list_policy_set_attached_gateways(
        self,
        request: agent_identity_20250901_models.ListPolicySetAttachedGatewaysRequest,
    ) -> agent_identity_20250901_models.ListPolicySetAttachedGatewaysResponse:
        """
        @summary 列出网关策略配置
        
        @param request: ListPolicySetAttachedGatewaysRequest
        @return: ListPolicySetAttachedGatewaysResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.list_policy_set_attached_gateways_with_options(request, runtime)

    async def list_policy_set_attached_gateways_async(
        self,
        request: agent_identity_20250901_models.ListPolicySetAttachedGatewaysRequest,
    ) -> agent_identity_20250901_models.ListPolicySetAttachedGatewaysResponse:
        """
        @summary 列出网关策略配置
        
        @param request: ListPolicySetAttachedGatewaysRequest
        @return: ListPolicySetAttachedGatewaysResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.list_policy_set_attached_gateways_with_options_async(request, runtime)

    def list_policy_sets_with_options(
        self,
        request: agent_identity_20250901_models.ListPolicySetsRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListPolicySetsResponse:
        """
        @summary 列出权限策略集合
        
        @param request: ListPolicySetsRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListPolicySetsResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.max_results):
            body['MaxResults'] = request.max_results
        if not UtilClient.is_unset(request.next_token):
            body['NextToken'] = request.next_token
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListPolicySets',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListPolicySetsResponse(),
            self.call_api(params, req, runtime)
        )

    async def list_policy_sets_with_options_async(
        self,
        request: agent_identity_20250901_models.ListPolicySetsRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListPolicySetsResponse:
        """
        @summary 列出权限策略集合
        
        @param request: ListPolicySetsRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListPolicySetsResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.max_results):
            body['MaxResults'] = request.max_results
        if not UtilClient.is_unset(request.next_token):
            body['NextToken'] = request.next_token
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListPolicySets',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListPolicySetsResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def list_policy_sets(
        self,
        request: agent_identity_20250901_models.ListPolicySetsRequest,
    ) -> agent_identity_20250901_models.ListPolicySetsResponse:
        """
        @summary 列出权限策略集合
        
        @param request: ListPolicySetsRequest
        @return: ListPolicySetsResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.list_policy_sets_with_options(request, runtime)

    async def list_policy_sets_async(
        self,
        request: agent_identity_20250901_models.ListPolicySetsRequest,
    ) -> agent_identity_20250901_models.ListPolicySetsResponse:
        """
        @summary 列出权限策略集合
        
        @param request: ListPolicySetsRequest
        @return: ListPolicySetsResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.list_policy_sets_with_options_async(request, runtime)

    def list_role_assignments_with_options(
        self,
        request: agent_identity_20250901_models.ListRoleAssignmentsRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListRoleAssignmentsResponse:
        """
        @summary 列出网关策略配置
        
        @param request: ListRoleAssignmentsRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListRoleAssignmentsResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.max_results):
            body['MaxResults'] = request.max_results
        if not UtilClient.is_unset(request.next_token):
            body['NextToken'] = request.next_token
        if not UtilClient.is_unset(request.principal_name):
            body['PrincipalName'] = request.principal_name
        if not UtilClient.is_unset(request.principal_type):
            body['PrincipalType'] = request.principal_type
        if not UtilClient.is_unset(request.role_name):
            body['RoleName'] = request.role_name
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListRoleAssignments',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListRoleAssignmentsResponse(),
            self.call_api(params, req, runtime)
        )

    async def list_role_assignments_with_options_async(
        self,
        request: agent_identity_20250901_models.ListRoleAssignmentsRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListRoleAssignmentsResponse:
        """
        @summary 列出网关策略配置
        
        @param request: ListRoleAssignmentsRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListRoleAssignmentsResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.max_results):
            body['MaxResults'] = request.max_results
        if not UtilClient.is_unset(request.next_token):
            body['NextToken'] = request.next_token
        if not UtilClient.is_unset(request.principal_name):
            body['PrincipalName'] = request.principal_name
        if not UtilClient.is_unset(request.principal_type):
            body['PrincipalType'] = request.principal_type
        if not UtilClient.is_unset(request.role_name):
            body['RoleName'] = request.role_name
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListRoleAssignments',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListRoleAssignmentsResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def list_role_assignments(
        self,
        request: agent_identity_20250901_models.ListRoleAssignmentsRequest,
    ) -> agent_identity_20250901_models.ListRoleAssignmentsResponse:
        """
        @summary 列出网关策略配置
        
        @param request: ListRoleAssignmentsRequest
        @return: ListRoleAssignmentsResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.list_role_assignments_with_options(request, runtime)

    async def list_role_assignments_async(
        self,
        request: agent_identity_20250901_models.ListRoleAssignmentsRequest,
    ) -> agent_identity_20250901_models.ListRoleAssignmentsResponse:
        """
        @summary 列出网关策略配置
        
        @param request: ListRoleAssignmentsRequest
        @return: ListRoleAssignmentsResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.list_role_assignments_with_options_async(request, runtime)

    def list_roles_with_options(
        self,
        request: agent_identity_20250901_models.ListRolesRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListRolesResponse:
        """
        @summary 列出Roles
        
        @param request: ListRolesRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListRolesResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.max_results):
            body['MaxResults'] = request.max_results
        if not UtilClient.is_unset(request.next_token):
            body['NextToken'] = request.next_token
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListRoles',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListRolesResponse(),
            self.call_api(params, req, runtime)
        )

    async def list_roles_with_options_async(
        self,
        request: agent_identity_20250901_models.ListRolesRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListRolesResponse:
        """
        @summary 列出Roles
        
        @param request: ListRolesRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListRolesResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.max_results):
            body['MaxResults'] = request.max_results
        if not UtilClient.is_unset(request.next_token):
            body['NextToken'] = request.next_token
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListRoles',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListRolesResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def list_roles(
        self,
        request: agent_identity_20250901_models.ListRolesRequest,
    ) -> agent_identity_20250901_models.ListRolesResponse:
        """
        @summary 列出Roles
        
        @param request: ListRolesRequest
        @return: ListRolesResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.list_roles_with_options(request, runtime)

    async def list_roles_async(
        self,
        request: agent_identity_20250901_models.ListRolesRequest,
    ) -> agent_identity_20250901_models.ListRolesResponse:
        """
        @summary 列出Roles
        
        @param request: ListRolesRequest
        @return: ListRolesResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.list_roles_with_options_async(request, runtime)

    def list_samlidentity_provider_certificates_with_options(
        self,
        request: agent_identity_20250901_models.ListSAMLIdentityProviderCertificatesRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListSAMLIdentityProviderCertificatesResponse:
        """
        @summary 列出IdentityProvider
        
        @param request: ListSAMLIdentityProviderCertificatesRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListSAMLIdentityProviderCertificatesResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListSAMLIdentityProviderCertificates',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListSAMLIdentityProviderCertificatesResponse(),
            self.call_api(params, req, runtime)
        )

    async def list_samlidentity_provider_certificates_with_options_async(
        self,
        request: agent_identity_20250901_models.ListSAMLIdentityProviderCertificatesRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListSAMLIdentityProviderCertificatesResponse:
        """
        @summary 列出IdentityProvider
        
        @param request: ListSAMLIdentityProviderCertificatesRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListSAMLIdentityProviderCertificatesResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListSAMLIdentityProviderCertificates',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListSAMLIdentityProviderCertificatesResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def list_samlidentity_provider_certificates(
        self,
        request: agent_identity_20250901_models.ListSAMLIdentityProviderCertificatesRequest,
    ) -> agent_identity_20250901_models.ListSAMLIdentityProviderCertificatesResponse:
        """
        @summary 列出IdentityProvider
        
        @param request: ListSAMLIdentityProviderCertificatesRequest
        @return: ListSAMLIdentityProviderCertificatesResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.list_samlidentity_provider_certificates_with_options(request, runtime)

    async def list_samlidentity_provider_certificates_async(
        self,
        request: agent_identity_20250901_models.ListSAMLIdentityProviderCertificatesRequest,
    ) -> agent_identity_20250901_models.ListSAMLIdentityProviderCertificatesResponse:
        """
        @summary 列出IdentityProvider
        
        @param request: ListSAMLIdentityProviderCertificatesRequest
        @return: ListSAMLIdentityProviderCertificatesResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.list_samlidentity_provider_certificates_with_options_async(request, runtime)

    def list_token_vaults_with_options(
        self,
        request: agent_identity_20250901_models.ListTokenVaultsRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListTokenVaultsResponse:
        """
        @summary 分页列出账户下所有的 API 密钥凭证
        
        @param request: ListTokenVaultsRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListTokenVaultsResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.max_results):
            body['MaxResults'] = request.max_results
        if not UtilClient.is_unset(request.next_token):
            body['NextToken'] = request.next_token
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListTokenVaults',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListTokenVaultsResponse(),
            self.call_api(params, req, runtime)
        )

    async def list_token_vaults_with_options_async(
        self,
        request: agent_identity_20250901_models.ListTokenVaultsRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListTokenVaultsResponse:
        """
        @summary 分页列出账户下所有的 API 密钥凭证
        
        @param request: ListTokenVaultsRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListTokenVaultsResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.max_results):
            body['MaxResults'] = request.max_results
        if not UtilClient.is_unset(request.next_token):
            body['NextToken'] = request.next_token
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListTokenVaults',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListTokenVaultsResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def list_token_vaults(
        self,
        request: agent_identity_20250901_models.ListTokenVaultsRequest,
    ) -> agent_identity_20250901_models.ListTokenVaultsResponse:
        """
        @summary 分页列出账户下所有的 API 密钥凭证
        
        @param request: ListTokenVaultsRequest
        @return: ListTokenVaultsResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.list_token_vaults_with_options(request, runtime)

    async def list_token_vaults_async(
        self,
        request: agent_identity_20250901_models.ListTokenVaultsRequest,
    ) -> agent_identity_20250901_models.ListTokenVaultsResponse:
        """
        @summary 分页列出账户下所有的 API 密钥凭证
        
        @param request: ListTokenVaultsRequest
        @return: ListTokenVaultsResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.list_token_vaults_with_options_async(request, runtime)

    def list_user_pool_clients_with_options(
        self,
        request: agent_identity_20250901_models.ListUserPoolClientsRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListUserPoolClientsResponse:
        """
        @summary 列出IdentityProvider
        
        @param request: ListUserPoolClientsRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListUserPoolClientsResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.max_results):
            body['MaxResults'] = request.max_results
        if not UtilClient.is_unset(request.next_token):
            body['NextToken'] = request.next_token
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListUserPoolClients',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListUserPoolClientsResponse(),
            self.call_api(params, req, runtime)
        )

    async def list_user_pool_clients_with_options_async(
        self,
        request: agent_identity_20250901_models.ListUserPoolClientsRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListUserPoolClientsResponse:
        """
        @summary 列出IdentityProvider
        
        @param request: ListUserPoolClientsRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListUserPoolClientsResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.max_results):
            body['MaxResults'] = request.max_results
        if not UtilClient.is_unset(request.next_token):
            body['NextToken'] = request.next_token
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListUserPoolClients',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListUserPoolClientsResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def list_user_pool_clients(
        self,
        request: agent_identity_20250901_models.ListUserPoolClientsRequest,
    ) -> agent_identity_20250901_models.ListUserPoolClientsResponse:
        """
        @summary 列出IdentityProvider
        
        @param request: ListUserPoolClientsRequest
        @return: ListUserPoolClientsResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.list_user_pool_clients_with_options(request, runtime)

    async def list_user_pool_clients_async(
        self,
        request: agent_identity_20250901_models.ListUserPoolClientsRequest,
    ) -> agent_identity_20250901_models.ListUserPoolClientsResponse:
        """
        @summary 列出IdentityProvider
        
        @param request: ListUserPoolClientsRequest
        @return: ListUserPoolClientsResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.list_user_pool_clients_with_options_async(request, runtime)

    def list_user_pools_with_options(
        self,
        request: agent_identity_20250901_models.ListUserPoolsRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListUserPoolsResponse:
        """
        @summary 列出IdentityProvider
        
        @param request: ListUserPoolsRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListUserPoolsResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.max_results):
            body['MaxResults'] = request.max_results
        if not UtilClient.is_unset(request.next_token):
            body['NextToken'] = request.next_token
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListUserPools',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListUserPoolsResponse(),
            self.call_api(params, req, runtime)
        )

    async def list_user_pools_with_options_async(
        self,
        request: agent_identity_20250901_models.ListUserPoolsRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListUserPoolsResponse:
        """
        @summary 列出IdentityProvider
        
        @param request: ListUserPoolsRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListUserPoolsResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.max_results):
            body['MaxResults'] = request.max_results
        if not UtilClient.is_unset(request.next_token):
            body['NextToken'] = request.next_token
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListUserPools',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListUserPoolsResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def list_user_pools(
        self,
        request: agent_identity_20250901_models.ListUserPoolsRequest,
    ) -> agent_identity_20250901_models.ListUserPoolsResponse:
        """
        @summary 列出IdentityProvider
        
        @param request: ListUserPoolsRequest
        @return: ListUserPoolsResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.list_user_pools_with_options(request, runtime)

    async def list_user_pools_async(
        self,
        request: agent_identity_20250901_models.ListUserPoolsRequest,
    ) -> agent_identity_20250901_models.ListUserPoolsResponse:
        """
        @summary 列出IdentityProvider
        
        @param request: ListUserPoolsRequest
        @return: ListUserPoolsResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.list_user_pools_with_options_async(request, runtime)

    def list_users_with_options(
        self,
        request: agent_identity_20250901_models.ListUsersRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListUsersResponse:
        """
        @summary 列出用户
        
        @param request: ListUsersRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListUsersResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.max_results):
            body['MaxResults'] = request.max_results
        if not UtilClient.is_unset(request.next_token):
            body['NextToken'] = request.next_token
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListUsers',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListUsersResponse(),
            self.call_api(params, req, runtime)
        )

    async def list_users_with_options_async(
        self,
        request: agent_identity_20250901_models.ListUsersRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListUsersResponse:
        """
        @summary 列出用户
        
        @param request: ListUsersRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListUsersResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.max_results):
            body['MaxResults'] = request.max_results
        if not UtilClient.is_unset(request.next_token):
            body['NextToken'] = request.next_token
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListUsers',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListUsersResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def list_users(
        self,
        request: agent_identity_20250901_models.ListUsersRequest,
    ) -> agent_identity_20250901_models.ListUsersResponse:
        """
        @summary 列出用户
        
        @param request: ListUsersRequest
        @return: ListUsersResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.list_users_with_options(request, runtime)

    async def list_users_async(
        self,
        request: agent_identity_20250901_models.ListUsersRequest,
    ) -> agent_identity_20250901_models.ListUsersResponse:
        """
        @summary 列出用户
        
        @param request: ListUsersRequest
        @return: ListUsersResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.list_users_with_options_async(request, runtime)

    def list_workload_identities_with_options(
        self,
        request: agent_identity_20250901_models.ListWorkloadIdentitiesRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListWorkloadIdentitiesResponse:
        """
        @summary 列出IdentityProvider
        
        @param request: ListWorkloadIdentitiesRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListWorkloadIdentitiesResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.max_results):
            body['MaxResults'] = request.max_results
        if not UtilClient.is_unset(request.next_token):
            body['NextToken'] = request.next_token
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListWorkloadIdentities',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListWorkloadIdentitiesResponse(),
            self.call_api(params, req, runtime)
        )

    async def list_workload_identities_with_options_async(
        self,
        request: agent_identity_20250901_models.ListWorkloadIdentitiesRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.ListWorkloadIdentitiesResponse:
        """
        @summary 列出IdentityProvider
        
        @param request: ListWorkloadIdentitiesRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: ListWorkloadIdentitiesResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.max_results):
            body['MaxResults'] = request.max_results
        if not UtilClient.is_unset(request.next_token):
            body['NextToken'] = request.next_token
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='ListWorkloadIdentities',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.ListWorkloadIdentitiesResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def list_workload_identities(
        self,
        request: agent_identity_20250901_models.ListWorkloadIdentitiesRequest,
    ) -> agent_identity_20250901_models.ListWorkloadIdentitiesResponse:
        """
        @summary 列出IdentityProvider
        
        @param request: ListWorkloadIdentitiesRequest
        @return: ListWorkloadIdentitiesResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.list_workload_identities_with_options(request, runtime)

    async def list_workload_identities_async(
        self,
        request: agent_identity_20250901_models.ListWorkloadIdentitiesRequest,
    ) -> agent_identity_20250901_models.ListWorkloadIdentitiesResponse:
        """
        @summary 列出IdentityProvider
        
        @param request: ListWorkloadIdentitiesRequest
        @return: ListWorkloadIdentitiesResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.list_workload_identities_with_options_async(request, runtime)

    def set_samlidentity_provider_with_options(
        self,
        tmp_req: agent_identity_20250901_models.SetSAMLIdentityProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.SetSAMLIdentityProviderResponse:
        """
        @summary 创建WorkloadIdentity
        
        @param tmp_req: SetSAMLIdentityProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: SetSAMLIdentityProviderResponse
        """
        UtilClient.validate_model(tmp_req)
        request = agent_identity_20250901_models.SetSAMLIdentityProviderShrinkRequest()
        OpenApiUtilClient.convert(tmp_req, request)
        if not UtilClient.is_unset(tmp_req.x_509certificates):
            request.x_509certificates_shrink = OpenApiUtilClient.array_to_string_with_specified_style(tmp_req.x_509certificates, 'X509Certificates', 'json')
        body = {}
        if not UtilClient.is_unset(request.entity_id):
            body['EntityId'] = request.entity_id
        if not UtilClient.is_unset(request.jitprovision_status):
            body['JITProvisionStatus'] = request.jitprovision_status
        if not UtilClient.is_unset(request.jitupdate_status):
            body['JITUpdateStatus'] = request.jitupdate_status
        if not UtilClient.is_unset(request.login_url):
            body['LoginUrl'] = request.login_url
        if not UtilClient.is_unset(request.ssostatus):
            body['SSOStatus'] = request.ssostatus
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        if not UtilClient.is_unset(request.x_509certificates_shrink):
            body['X509Certificates'] = request.x_509certificates_shrink
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='SetSAMLIdentityProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.SetSAMLIdentityProviderResponse(),
            self.call_api(params, req, runtime)
        )

    async def set_samlidentity_provider_with_options_async(
        self,
        tmp_req: agent_identity_20250901_models.SetSAMLIdentityProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.SetSAMLIdentityProviderResponse:
        """
        @summary 创建WorkloadIdentity
        
        @param tmp_req: SetSAMLIdentityProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: SetSAMLIdentityProviderResponse
        """
        UtilClient.validate_model(tmp_req)
        request = agent_identity_20250901_models.SetSAMLIdentityProviderShrinkRequest()
        OpenApiUtilClient.convert(tmp_req, request)
        if not UtilClient.is_unset(tmp_req.x_509certificates):
            request.x_509certificates_shrink = OpenApiUtilClient.array_to_string_with_specified_style(tmp_req.x_509certificates, 'X509Certificates', 'json')
        body = {}
        if not UtilClient.is_unset(request.entity_id):
            body['EntityId'] = request.entity_id
        if not UtilClient.is_unset(request.jitprovision_status):
            body['JITProvisionStatus'] = request.jitprovision_status
        if not UtilClient.is_unset(request.jitupdate_status):
            body['JITUpdateStatus'] = request.jitupdate_status
        if not UtilClient.is_unset(request.login_url):
            body['LoginUrl'] = request.login_url
        if not UtilClient.is_unset(request.ssostatus):
            body['SSOStatus'] = request.ssostatus
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        if not UtilClient.is_unset(request.x_509certificates_shrink):
            body['X509Certificates'] = request.x_509certificates_shrink
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='SetSAMLIdentityProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.SetSAMLIdentityProviderResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def set_samlidentity_provider(
        self,
        request: agent_identity_20250901_models.SetSAMLIdentityProviderRequest,
    ) -> agent_identity_20250901_models.SetSAMLIdentityProviderResponse:
        """
        @summary 创建WorkloadIdentity
        
        @param request: SetSAMLIdentityProviderRequest
        @return: SetSAMLIdentityProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.set_samlidentity_provider_with_options(request, runtime)

    async def set_samlidentity_provider_async(
        self,
        request: agent_identity_20250901_models.SetSAMLIdentityProviderRequest,
    ) -> agent_identity_20250901_models.SetSAMLIdentityProviderResponse:
        """
        @summary 创建WorkloadIdentity
        
        @param request: SetSAMLIdentityProviderRequest
        @return: SetSAMLIdentityProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.set_samlidentity_provider_with_options_async(request, runtime)

    def update_apikey_credential_provider_with_options(
        self,
        request: agent_identity_20250901_models.UpdateAPIKeyCredentialProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.UpdateAPIKeyCredentialProviderResponse:
        """
        @summary 更新一个 API 密钥凭证提供商
        
        @param request: UpdateAPIKeyCredentialProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: UpdateAPIKeyCredentialProviderResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.apikey):
            body['APIKey'] = request.apikey
        if not UtilClient.is_unset(request.apikey_credential_provider_name):
            body['APIKeyCredentialProviderName'] = request.apikey_credential_provider_name
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='UpdateAPIKeyCredentialProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.UpdateAPIKeyCredentialProviderResponse(),
            self.call_api(params, req, runtime)
        )

    async def update_apikey_credential_provider_with_options_async(
        self,
        request: agent_identity_20250901_models.UpdateAPIKeyCredentialProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.UpdateAPIKeyCredentialProviderResponse:
        """
        @summary 更新一个 API 密钥凭证提供商
        
        @param request: UpdateAPIKeyCredentialProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: UpdateAPIKeyCredentialProviderResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.apikey):
            body['APIKey'] = request.apikey
        if not UtilClient.is_unset(request.apikey_credential_provider_name):
            body['APIKeyCredentialProviderName'] = request.apikey_credential_provider_name
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='UpdateAPIKeyCredentialProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.UpdateAPIKeyCredentialProviderResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def update_apikey_credential_provider(
        self,
        request: agent_identity_20250901_models.UpdateAPIKeyCredentialProviderRequest,
    ) -> agent_identity_20250901_models.UpdateAPIKeyCredentialProviderResponse:
        """
        @summary 更新一个 API 密钥凭证提供商
        
        @param request: UpdateAPIKeyCredentialProviderRequest
        @return: UpdateAPIKeyCredentialProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.update_apikey_credential_provider_with_options(request, runtime)

    async def update_apikey_credential_provider_async(
        self,
        request: agent_identity_20250901_models.UpdateAPIKeyCredentialProviderRequest,
    ) -> agent_identity_20250901_models.UpdateAPIKeyCredentialProviderResponse:
        """
        @summary 更新一个 API 密钥凭证提供商
        
        @param request: UpdateAPIKeyCredentialProviderRequest
        @return: UpdateAPIKeyCredentialProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.update_apikey_credential_provider_with_options_async(request, runtime)

    def update_gateway_policy_config_with_options(
        self,
        request: agent_identity_20250901_models.UpdateGatewayPolicyConfigRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.UpdateGatewayPolicyConfigResponse:
        """
        @summary 查询网关策略配置
        
        @param request: UpdateGatewayPolicyConfigRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: UpdateGatewayPolicyConfigResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.enforcement_mode):
            body['EnforcementMode'] = request.enforcement_mode
        if not UtilClient.is_unset(request.gateway_arn):
            body['GatewayArn'] = request.gateway_arn
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='UpdateGatewayPolicyConfig',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.UpdateGatewayPolicyConfigResponse(),
            self.call_api(params, req, runtime)
        )

    async def update_gateway_policy_config_with_options_async(
        self,
        request: agent_identity_20250901_models.UpdateGatewayPolicyConfigRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.UpdateGatewayPolicyConfigResponse:
        """
        @summary 查询网关策略配置
        
        @param request: UpdateGatewayPolicyConfigRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: UpdateGatewayPolicyConfigResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.enforcement_mode):
            body['EnforcementMode'] = request.enforcement_mode
        if not UtilClient.is_unset(request.gateway_arn):
            body['GatewayArn'] = request.gateway_arn
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='UpdateGatewayPolicyConfig',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.UpdateGatewayPolicyConfigResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def update_gateway_policy_config(
        self,
        request: agent_identity_20250901_models.UpdateGatewayPolicyConfigRequest,
    ) -> agent_identity_20250901_models.UpdateGatewayPolicyConfigResponse:
        """
        @summary 查询网关策略配置
        
        @param request: UpdateGatewayPolicyConfigRequest
        @return: UpdateGatewayPolicyConfigResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.update_gateway_policy_config_with_options(request, runtime)

    async def update_gateway_policy_config_async(
        self,
        request: agent_identity_20250901_models.UpdateGatewayPolicyConfigRequest,
    ) -> agent_identity_20250901_models.UpdateGatewayPolicyConfigResponse:
        """
        @summary 查询网关策略配置
        
        @param request: UpdateGatewayPolicyConfigRequest
        @return: UpdateGatewayPolicyConfigResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.update_gateway_policy_config_with_options_async(request, runtime)

    def update_identity_provider_with_options(
        self,
        tmp_req: agent_identity_20250901_models.UpdateIdentityProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.UpdateIdentityProviderResponse:
        """
        @summary 更新IdentityProvider
        
        @param tmp_req: UpdateIdentityProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: UpdateIdentityProviderResponse
        """
        UtilClient.validate_model(tmp_req)
        request = agent_identity_20250901_models.UpdateIdentityProviderShrinkRequest()
        OpenApiUtilClient.convert(tmp_req, request)
        if not UtilClient.is_unset(tmp_req.allowed_audience):
            request.allowed_audience_shrink = OpenApiUtilClient.array_to_string_with_specified_style(tmp_req.allowed_audience, 'AllowedAudience', 'json')
        body = {}
        if not UtilClient.is_unset(request.allowed_audience_shrink):
            body['AllowedAudience'] = request.allowed_audience_shrink
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.discovery_url):
            body['DiscoveryURL'] = request.discovery_url
        if not UtilClient.is_unset(request.identity_provider_name):
            body['IdentityProviderName'] = request.identity_provider_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='UpdateIdentityProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.UpdateIdentityProviderResponse(),
            self.call_api(params, req, runtime)
        )

    async def update_identity_provider_with_options_async(
        self,
        tmp_req: agent_identity_20250901_models.UpdateIdentityProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.UpdateIdentityProviderResponse:
        """
        @summary 更新IdentityProvider
        
        @param tmp_req: UpdateIdentityProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: UpdateIdentityProviderResponse
        """
        UtilClient.validate_model(tmp_req)
        request = agent_identity_20250901_models.UpdateIdentityProviderShrinkRequest()
        OpenApiUtilClient.convert(tmp_req, request)
        if not UtilClient.is_unset(tmp_req.allowed_audience):
            request.allowed_audience_shrink = OpenApiUtilClient.array_to_string_with_specified_style(tmp_req.allowed_audience, 'AllowedAudience', 'json')
        body = {}
        if not UtilClient.is_unset(request.allowed_audience_shrink):
            body['AllowedAudience'] = request.allowed_audience_shrink
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.discovery_url):
            body['DiscoveryURL'] = request.discovery_url
        if not UtilClient.is_unset(request.identity_provider_name):
            body['IdentityProviderName'] = request.identity_provider_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='UpdateIdentityProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.UpdateIdentityProviderResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def update_identity_provider(
        self,
        request: agent_identity_20250901_models.UpdateIdentityProviderRequest,
    ) -> agent_identity_20250901_models.UpdateIdentityProviderResponse:
        """
        @summary 更新IdentityProvider
        
        @param request: UpdateIdentityProviderRequest
        @return: UpdateIdentityProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.update_identity_provider_with_options(request, runtime)

    async def update_identity_provider_async(
        self,
        request: agent_identity_20250901_models.UpdateIdentityProviderRequest,
    ) -> agent_identity_20250901_models.UpdateIdentityProviderResponse:
        """
        @summary 更新IdentityProvider
        
        @param request: UpdateIdentityProviderRequest
        @return: UpdateIdentityProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.update_identity_provider_with_options_async(request, runtime)

    def update_oauth_2credential_provider_with_options(
        self,
        tmp_req: agent_identity_20250901_models.UpdateOAuth2CredentialProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.UpdateOAuth2CredentialProviderResponse:
        """
        @summary 修改 OAuth2 凭证提供商
        
        @param tmp_req: UpdateOAuth2CredentialProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: UpdateOAuth2CredentialProviderResponse
        """
        UtilClient.validate_model(tmp_req)
        request = agent_identity_20250901_models.UpdateOAuth2CredentialProviderShrinkRequest()
        OpenApiUtilClient.convert(tmp_req, request)
        if not UtilClient.is_unset(tmp_req.oauth_2provider_config):
            request.oauth_2provider_config_shrink = OpenApiUtilClient.array_to_string_with_specified_style(tmp_req.oauth_2provider_config, 'OAuth2ProviderConfig', 'json')
        body = {}
        if not UtilClient.is_unset(request.callback_url):
            body['CallbackURL'] = request.callback_url
        if not UtilClient.is_unset(request.credential_provider_vendor):
            body['CredentialProviderVendor'] = request.credential_provider_vendor
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.oauth_2credential_provider_name):
            body['OAuth2CredentialProviderName'] = request.oauth_2credential_provider_name
        if not UtilClient.is_unset(request.oauth_2provider_config_shrink):
            body['OAuth2ProviderConfig'] = request.oauth_2provider_config_shrink
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='UpdateOAuth2CredentialProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.UpdateOAuth2CredentialProviderResponse(),
            self.call_api(params, req, runtime)
        )

    async def update_oauth_2credential_provider_with_options_async(
        self,
        tmp_req: agent_identity_20250901_models.UpdateOAuth2CredentialProviderRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.UpdateOAuth2CredentialProviderResponse:
        """
        @summary 修改 OAuth2 凭证提供商
        
        @param tmp_req: UpdateOAuth2CredentialProviderRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: UpdateOAuth2CredentialProviderResponse
        """
        UtilClient.validate_model(tmp_req)
        request = agent_identity_20250901_models.UpdateOAuth2CredentialProviderShrinkRequest()
        OpenApiUtilClient.convert(tmp_req, request)
        if not UtilClient.is_unset(tmp_req.oauth_2provider_config):
            request.oauth_2provider_config_shrink = OpenApiUtilClient.array_to_string_with_specified_style(tmp_req.oauth_2provider_config, 'OAuth2ProviderConfig', 'json')
        body = {}
        if not UtilClient.is_unset(request.callback_url):
            body['CallbackURL'] = request.callback_url
        if not UtilClient.is_unset(request.credential_provider_vendor):
            body['CredentialProviderVendor'] = request.credential_provider_vendor
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.oauth_2credential_provider_name):
            body['OAuth2CredentialProviderName'] = request.oauth_2credential_provider_name
        if not UtilClient.is_unset(request.oauth_2provider_config_shrink):
            body['OAuth2ProviderConfig'] = request.oauth_2provider_config_shrink
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='UpdateOAuth2CredentialProvider',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.UpdateOAuth2CredentialProviderResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def update_oauth_2credential_provider(
        self,
        request: agent_identity_20250901_models.UpdateOAuth2CredentialProviderRequest,
    ) -> agent_identity_20250901_models.UpdateOAuth2CredentialProviderResponse:
        """
        @summary 修改 OAuth2 凭证提供商
        
        @param request: UpdateOAuth2CredentialProviderRequest
        @return: UpdateOAuth2CredentialProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.update_oauth_2credential_provider_with_options(request, runtime)

    async def update_oauth_2credential_provider_async(
        self,
        request: agent_identity_20250901_models.UpdateOAuth2CredentialProviderRequest,
    ) -> agent_identity_20250901_models.UpdateOAuth2CredentialProviderResponse:
        """
        @summary 修改 OAuth2 凭证提供商
        
        @param request: UpdateOAuth2CredentialProviderRequest
        @return: UpdateOAuth2CredentialProviderResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.update_oauth_2credential_provider_with_options_async(request, runtime)

    def update_policy_with_options(
        self,
        tmp_req: agent_identity_20250901_models.UpdatePolicyRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.UpdatePolicyResponse:
        """
        @summary 更新一个权限策略
        
        @param tmp_req: UpdatePolicyRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: UpdatePolicyResponse
        """
        UtilClient.validate_model(tmp_req)
        request = agent_identity_20250901_models.UpdatePolicyShrinkRequest()
        OpenApiUtilClient.convert(tmp_req, request)
        if not UtilClient.is_unset(tmp_req.definition):
            request.definition_shrink = OpenApiUtilClient.array_to_string_with_specified_style(tmp_req.definition, 'Definition', 'json')
        body = {}
        if not UtilClient.is_unset(request.definition_shrink):
            body['Definition'] = request.definition_shrink
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.policy_name):
            body['PolicyName'] = request.policy_name
        if not UtilClient.is_unset(request.policy_set_name):
            body['PolicySetName'] = request.policy_set_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='UpdatePolicy',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.UpdatePolicyResponse(),
            self.call_api(params, req, runtime)
        )

    async def update_policy_with_options_async(
        self,
        tmp_req: agent_identity_20250901_models.UpdatePolicyRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.UpdatePolicyResponse:
        """
        @summary 更新一个权限策略
        
        @param tmp_req: UpdatePolicyRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: UpdatePolicyResponse
        """
        UtilClient.validate_model(tmp_req)
        request = agent_identity_20250901_models.UpdatePolicyShrinkRequest()
        OpenApiUtilClient.convert(tmp_req, request)
        if not UtilClient.is_unset(tmp_req.definition):
            request.definition_shrink = OpenApiUtilClient.array_to_string_with_specified_style(tmp_req.definition, 'Definition', 'json')
        body = {}
        if not UtilClient.is_unset(request.definition_shrink):
            body['Definition'] = request.definition_shrink
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.policy_name):
            body['PolicyName'] = request.policy_name
        if not UtilClient.is_unset(request.policy_set_name):
            body['PolicySetName'] = request.policy_set_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='UpdatePolicy',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.UpdatePolicyResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def update_policy(
        self,
        request: agent_identity_20250901_models.UpdatePolicyRequest,
    ) -> agent_identity_20250901_models.UpdatePolicyResponse:
        """
        @summary 更新一个权限策略
        
        @param request: UpdatePolicyRequest
        @return: UpdatePolicyResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.update_policy_with_options(request, runtime)

    async def update_policy_async(
        self,
        request: agent_identity_20250901_models.UpdatePolicyRequest,
    ) -> agent_identity_20250901_models.UpdatePolicyResponse:
        """
        @summary 更新一个权限策略
        
        @param request: UpdatePolicyRequest
        @return: UpdatePolicyResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.update_policy_with_options_async(request, runtime)

    def update_policy_set_with_options(
        self,
        request: agent_identity_20250901_models.UpdatePolicySetRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.UpdatePolicySetResponse:
        """
        @summary 更新一个权限策略集合
        
        @param request: UpdatePolicySetRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: UpdatePolicySetResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.policy_set_name):
            body['PolicySetName'] = request.policy_set_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='UpdatePolicySet',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.UpdatePolicySetResponse(),
            self.call_api(params, req, runtime)
        )

    async def update_policy_set_with_options_async(
        self,
        request: agent_identity_20250901_models.UpdatePolicySetRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.UpdatePolicySetResponse:
        """
        @summary 更新一个权限策略集合
        
        @param request: UpdatePolicySetRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: UpdatePolicySetResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.policy_set_name):
            body['PolicySetName'] = request.policy_set_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='UpdatePolicySet',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.UpdatePolicySetResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def update_policy_set(
        self,
        request: agent_identity_20250901_models.UpdatePolicySetRequest,
    ) -> agent_identity_20250901_models.UpdatePolicySetResponse:
        """
        @summary 更新一个权限策略集合
        
        @param request: UpdatePolicySetRequest
        @return: UpdatePolicySetResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.update_policy_set_with_options(request, runtime)

    async def update_policy_set_async(
        self,
        request: agent_identity_20250901_models.UpdatePolicySetRequest,
    ) -> agent_identity_20250901_models.UpdatePolicySetResponse:
        """
        @summary 更新一个权限策略集合
        
        @param request: UpdatePolicySetRequest
        @return: UpdatePolicySetResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.update_policy_set_with_options_async(request, runtime)

    def update_role_with_options(
        self,
        request: agent_identity_20250901_models.UpdateRoleRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.UpdateRoleResponse:
        """
        @summary 更新Role
        
        @param request: UpdateRoleRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: UpdateRoleResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.role_name):
            body['RoleName'] = request.role_name
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='UpdateRole',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.UpdateRoleResponse(),
            self.call_api(params, req, runtime)
        )

    async def update_role_with_options_async(
        self,
        request: agent_identity_20250901_models.UpdateRoleRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.UpdateRoleResponse:
        """
        @summary 更新Role
        
        @param request: UpdateRoleRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: UpdateRoleResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.role_name):
            body['RoleName'] = request.role_name
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='UpdateRole',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.UpdateRoleResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def update_role(
        self,
        request: agent_identity_20250901_models.UpdateRoleRequest,
    ) -> agent_identity_20250901_models.UpdateRoleResponse:
        """
        @summary 更新Role
        
        @param request: UpdateRoleRequest
        @return: UpdateRoleResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.update_role_with_options(request, runtime)

    async def update_role_async(
        self,
        request: agent_identity_20250901_models.UpdateRoleRequest,
    ) -> agent_identity_20250901_models.UpdateRoleResponse:
        """
        @summary 更新Role
        
        @param request: UpdateRoleRequest
        @return: UpdateRoleResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.update_role_with_options_async(request, runtime)

    def update_token_vault_with_options(
        self,
        request: agent_identity_20250901_models.UpdateTokenVaultRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.UpdateTokenVaultResponse:
        """
        @summary 更新凭证库。
        
        @param request: UpdateTokenVaultRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: UpdateTokenVaultResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.role_arn):
            body['RoleArn'] = request.role_arn
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='UpdateTokenVault',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.UpdateTokenVaultResponse(),
            self.call_api(params, req, runtime)
        )

    async def update_token_vault_with_options_async(
        self,
        request: agent_identity_20250901_models.UpdateTokenVaultRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.UpdateTokenVaultResponse:
        """
        @summary 更新凭证库。
        
        @param request: UpdateTokenVaultRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: UpdateTokenVaultResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.role_arn):
            body['RoleArn'] = request.role_arn
        if not UtilClient.is_unset(request.token_vault_name):
            body['TokenVaultName'] = request.token_vault_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='UpdateTokenVault',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.UpdateTokenVaultResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def update_token_vault(
        self,
        request: agent_identity_20250901_models.UpdateTokenVaultRequest,
    ) -> agent_identity_20250901_models.UpdateTokenVaultResponse:
        """
        @summary 更新凭证库。
        
        @param request: UpdateTokenVaultRequest
        @return: UpdateTokenVaultResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.update_token_vault_with_options(request, runtime)

    async def update_token_vault_async(
        self,
        request: agent_identity_20250901_models.UpdateTokenVaultRequest,
    ) -> agent_identity_20250901_models.UpdateTokenVaultResponse:
        """
        @summary 更新凭证库。
        
        @param request: UpdateTokenVaultRequest
        @return: UpdateTokenVaultResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.update_token_vault_with_options_async(request, runtime)

    def update_user_pool_with_options(
        self,
        request: agent_identity_20250901_models.UpdateUserPoolRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.UpdateUserPoolResponse:
        """
        @summary 更新IdentityProvider
        
        @param request: UpdateUserPoolRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: UpdateUserPoolResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='UpdateUserPool',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.UpdateUserPoolResponse(),
            self.call_api(params, req, runtime)
        )

    async def update_user_pool_with_options_async(
        self,
        request: agent_identity_20250901_models.UpdateUserPoolRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.UpdateUserPoolResponse:
        """
        @summary 更新IdentityProvider
        
        @param request: UpdateUserPoolRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: UpdateUserPoolResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='UpdateUserPool',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.UpdateUserPoolResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def update_user_pool(
        self,
        request: agent_identity_20250901_models.UpdateUserPoolRequest,
    ) -> agent_identity_20250901_models.UpdateUserPoolResponse:
        """
        @summary 更新IdentityProvider
        
        @param request: UpdateUserPoolRequest
        @return: UpdateUserPoolResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.update_user_pool_with_options(request, runtime)

    async def update_user_pool_async(
        self,
        request: agent_identity_20250901_models.UpdateUserPoolRequest,
    ) -> agent_identity_20250901_models.UpdateUserPoolResponse:
        """
        @summary 更新IdentityProvider
        
        @param request: UpdateUserPoolRequest
        @return: UpdateUserPoolResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.update_user_pool_with_options_async(request, runtime)

    def update_user_pool_client_with_options(
        self,
        request: agent_identity_20250901_models.UpdateUserPoolClientRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.UpdateUserPoolClientResponse:
        """
        @summary 创建应用
        
        @param request: UpdateUserPoolClientRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: UpdateUserPoolClientResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.access_token_validity):
            body['AccessTokenValidity'] = request.access_token_validity
        if not UtilClient.is_unset(request.client_name):
            body['ClientName'] = request.client_name
        if not UtilClient.is_unset(request.enforce_pkce):
            body['EnforcePKCE'] = request.enforce_pkce
        if not UtilClient.is_unset(request.redirect_uris):
            body['RedirectURIs'] = request.redirect_uris
        if not UtilClient.is_unset(request.refresh_token_validity):
            body['RefreshTokenValidity'] = request.refresh_token_validity
        if not UtilClient.is_unset(request.secret_required):
            body['SecretRequired'] = request.secret_required
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='UpdateUserPoolClient',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.UpdateUserPoolClientResponse(),
            self.call_api(params, req, runtime)
        )

    async def update_user_pool_client_with_options_async(
        self,
        request: agent_identity_20250901_models.UpdateUserPoolClientRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.UpdateUserPoolClientResponse:
        """
        @summary 创建应用
        
        @param request: UpdateUserPoolClientRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: UpdateUserPoolClientResponse
        """
        UtilClient.validate_model(request)
        body = {}
        if not UtilClient.is_unset(request.access_token_validity):
            body['AccessTokenValidity'] = request.access_token_validity
        if not UtilClient.is_unset(request.client_name):
            body['ClientName'] = request.client_name
        if not UtilClient.is_unset(request.enforce_pkce):
            body['EnforcePKCE'] = request.enforce_pkce
        if not UtilClient.is_unset(request.redirect_uris):
            body['RedirectURIs'] = request.redirect_uris
        if not UtilClient.is_unset(request.refresh_token_validity):
            body['RefreshTokenValidity'] = request.refresh_token_validity
        if not UtilClient.is_unset(request.secret_required):
            body['SecretRequired'] = request.secret_required
        if not UtilClient.is_unset(request.user_pool_name):
            body['UserPoolName'] = request.user_pool_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='UpdateUserPoolClient',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.UpdateUserPoolClientResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def update_user_pool_client(
        self,
        request: agent_identity_20250901_models.UpdateUserPoolClientRequest,
    ) -> agent_identity_20250901_models.UpdateUserPoolClientResponse:
        """
        @summary 创建应用
        
        @param request: UpdateUserPoolClientRequest
        @return: UpdateUserPoolClientResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.update_user_pool_client_with_options(request, runtime)

    async def update_user_pool_client_async(
        self,
        request: agent_identity_20250901_models.UpdateUserPoolClientRequest,
    ) -> agent_identity_20250901_models.UpdateUserPoolClientResponse:
        """
        @summary 创建应用
        
        @param request: UpdateUserPoolClientRequest
        @return: UpdateUserPoolClientResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.update_user_pool_client_with_options_async(request, runtime)

    def update_workload_identity_with_options(
        self,
        tmp_req: agent_identity_20250901_models.UpdateWorkloadIdentityRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.UpdateWorkloadIdentityResponse:
        """
        @summary 创建应用
        
        @param tmp_req: UpdateWorkloadIdentityRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: UpdateWorkloadIdentityResponse
        """
        UtilClient.validate_model(tmp_req)
        request = agent_identity_20250901_models.UpdateWorkloadIdentityShrinkRequest()
        OpenApiUtilClient.convert(tmp_req, request)
        if not UtilClient.is_unset(tmp_req.allowed_resource_oauth_2return_urls):
            request.allowed_resource_oauth_2return_urls_shrink = OpenApiUtilClient.array_to_string_with_specified_style(tmp_req.allowed_resource_oauth_2return_urls, 'AllowedResourceOAuth2ReturnURLs', 'json')
        body = {}
        if not UtilClient.is_unset(request.allowed_resource_oauth_2return_urls_shrink):
            body['AllowedResourceOAuth2ReturnURLs'] = request.allowed_resource_oauth_2return_urls_shrink
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.identity_provider_name):
            body['IdentityProviderName'] = request.identity_provider_name
        if not UtilClient.is_unset(request.role_arn):
            body['RoleArn'] = request.role_arn
        if not UtilClient.is_unset(request.workload_identity_name):
            body['WorkloadIdentityName'] = request.workload_identity_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='UpdateWorkloadIdentity',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.UpdateWorkloadIdentityResponse(),
            self.call_api(params, req, runtime)
        )

    async def update_workload_identity_with_options_async(
        self,
        tmp_req: agent_identity_20250901_models.UpdateWorkloadIdentityRequest,
        runtime: util_models.RuntimeOptions,
    ) -> agent_identity_20250901_models.UpdateWorkloadIdentityResponse:
        """
        @summary 创建应用
        
        @param tmp_req: UpdateWorkloadIdentityRequest
        @param runtime: runtime options for this request RuntimeOptions
        @return: UpdateWorkloadIdentityResponse
        """
        UtilClient.validate_model(tmp_req)
        request = agent_identity_20250901_models.UpdateWorkloadIdentityShrinkRequest()
        OpenApiUtilClient.convert(tmp_req, request)
        if not UtilClient.is_unset(tmp_req.allowed_resource_oauth_2return_urls):
            request.allowed_resource_oauth_2return_urls_shrink = OpenApiUtilClient.array_to_string_with_specified_style(tmp_req.allowed_resource_oauth_2return_urls, 'AllowedResourceOAuth2ReturnURLs', 'json')
        body = {}
        if not UtilClient.is_unset(request.allowed_resource_oauth_2return_urls_shrink):
            body['AllowedResourceOAuth2ReturnURLs'] = request.allowed_resource_oauth_2return_urls_shrink
        if not UtilClient.is_unset(request.description):
            body['Description'] = request.description
        if not UtilClient.is_unset(request.identity_provider_name):
            body['IdentityProviderName'] = request.identity_provider_name
        if not UtilClient.is_unset(request.role_arn):
            body['RoleArn'] = request.role_arn
        if not UtilClient.is_unset(request.workload_identity_name):
            body['WorkloadIdentityName'] = request.workload_identity_name
        req = open_api_models.OpenApiRequest(
            body=OpenApiUtilClient.parse_to_map(body)
        )
        params = open_api_models.Params(
            action='UpdateWorkloadIdentity',
            version='2025-09-01',
            protocol='HTTPS',
            pathname='/',
            method='POST',
            auth_type='AK',
            style='RPC',
            req_body_type='formData',
            body_type='json'
        )
        return TeaCore.from_map(
            agent_identity_20250901_models.UpdateWorkloadIdentityResponse(),
            await self.call_api_async(params, req, runtime)
        )

    def update_workload_identity(
        self,
        request: agent_identity_20250901_models.UpdateWorkloadIdentityRequest,
    ) -> agent_identity_20250901_models.UpdateWorkloadIdentityResponse:
        """
        @summary 创建应用
        
        @param request: UpdateWorkloadIdentityRequest
        @return: UpdateWorkloadIdentityResponse
        """
        runtime = util_models.RuntimeOptions()
        return self.update_workload_identity_with_options(request, runtime)

    async def update_workload_identity_async(
        self,
        request: agent_identity_20250901_models.UpdateWorkloadIdentityRequest,
    ) -> agent_identity_20250901_models.UpdateWorkloadIdentityResponse:
        """
        @summary 创建应用
        
        @param request: UpdateWorkloadIdentityRequest
        @return: UpdateWorkloadIdentityResponse
        """
        runtime = util_models.RuntimeOptions()
        return await self.update_workload_identity_with_options_async(request, runtime)
