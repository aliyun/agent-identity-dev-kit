# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
from Tea.model import TeaModel
from typing import Dict, List


class AuthorizationRequest(TeaModel):
    def __init__(
        self,
        endpoint: str = None,
    ):
        self.endpoint = endpoint

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.endpoint is not None:
            result['Endpoint'] = self.endpoint
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Endpoint') is not None:
            self.endpoint = m.get('Endpoint')
        return self


class PKCE(TeaModel):
    def __init__(
        self,
        enabled: bool = None,
    ):
        self.enabled = enabled

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.enabled is not None:
            result['Enabled'] = self.enabled
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Enabled') is not None:
            self.enabled = m.get('Enabled')
        return self


class TokenReqeust(TeaModel):
    def __init__(
        self,
        endpoint: str = None,
    ):
        self.endpoint = endpoint

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.endpoint is not None:
            result['Endpoint'] = self.endpoint
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Endpoint') is not None:
            self.endpoint = m.get('Endpoint')
        return self


class AuthorizationServerMetadata(TeaModel):
    def __init__(
        self,
        authorization_request: AuthorizationRequest = None,
        issuer: str = None,
        pkce: PKCE = None,
        token_request: TokenReqeust = None,
    ):
        self.authorization_request = authorization_request
        self.issuer = issuer
        self.pkce = pkce
        self.token_request = token_request

    def validate(self):
        if self.authorization_request:
            self.authorization_request.validate()
        if self.pkce:
            self.pkce.validate()
        if self.token_request:
            self.token_request.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.authorization_request is not None:
            result['AuthorizationRequest'] = self.authorization_request.to_map()
        if self.issuer is not None:
            result['Issuer'] = self.issuer
        if self.pkce is not None:
            result['PKCE'] = self.pkce.to_map()
        if self.token_request is not None:
            result['TokenRequest'] = self.token_request.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AuthorizationRequest') is not None:
            temp_model = AuthorizationRequest()
            self.authorization_request = temp_model.from_map(m['AuthorizationRequest'])
        if m.get('Issuer') is not None:
            self.issuer = m.get('Issuer')
        if m.get('PKCE') is not None:
            temp_model = PKCE()
            self.pkce = temp_model.from_map(m['PKCE'])
        if m.get('TokenRequest') is not None:
            temp_model = TokenReqeust()
            self.token_request = temp_model.from_map(m['TokenRequest'])
        return self


class OAuth2Discovery(TeaModel):
    def __init__(
        self,
        authorization_server_metadata: AuthorizationServerMetadata = None,
        discovery_url: str = None,
    ):
        self.authorization_server_metadata = authorization_server_metadata
        self.discovery_url = discovery_url

    def validate(self):
        if self.authorization_server_metadata:
            self.authorization_server_metadata.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.authorization_server_metadata is not None:
            result['AuthorizationServerMetadata'] = self.authorization_server_metadata.to_map()
        if self.discovery_url is not None:
            result['DiscoveryURL'] = self.discovery_url
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AuthorizationServerMetadata') is not None:
            temp_model = AuthorizationServerMetadata()
            self.authorization_server_metadata = temp_model.from_map(m['AuthorizationServerMetadata'])
        if m.get('DiscoveryURL') is not None:
            self.discovery_url = m.get('DiscoveryURL')
        return self


class CustomOAuth2ProviderConfig(TeaModel):
    def __init__(
        self,
        client_id: str = None,
        client_secret: str = None,
        oauth_2discovery: OAuth2Discovery = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.oauth_2discovery = oauth_2discovery

    def validate(self):
        if self.oauth_2discovery:
            self.oauth_2discovery.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.client_id is not None:
            result['ClientId'] = self.client_id
        if self.client_secret is not None:
            result['ClientSecret'] = self.client_secret
        if self.oauth_2discovery is not None:
            result['OAuth2Discovery'] = self.oauth_2discovery.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('ClientId') is not None:
            self.client_id = m.get('ClientId')
        if m.get('ClientSecret') is not None:
            self.client_secret = m.get('ClientSecret')
        if m.get('OAuth2Discovery') is not None:
            temp_model = OAuth2Discovery()
            self.oauth_2discovery = temp_model.from_map(m['OAuth2Discovery'])
        return self


class DefinitionCedar(TeaModel):
    def __init__(
        self,
        statement: str = None,
    ):
        self.statement = statement

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.statement is not None:
            result['Statement'] = self.statement
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Statement') is not None:
            self.statement = m.get('Statement')
        return self


class Definition(TeaModel):
    def __init__(
        self,
        cedar: DefinitionCedar = None,
    ):
        self.cedar = cedar

    def validate(self):
        if self.cedar:
            self.cedar.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.cedar is not None:
            result['Cedar'] = self.cedar.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Cedar') is not None:
            temp_model = DefinitionCedar()
            self.cedar = temp_model.from_map(m['Cedar'])
        return self


class EncryptionConfig(TeaModel):
    def __init__(
        self,
        key_type: str = None,
        kms_key_arn: str = None,
    ):
        self.key_type = key_type
        self.kms_key_arn = kms_key_arn

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.key_type is not None:
            result['KeyType'] = self.key_type
        if self.kms_key_arn is not None:
            result['KmsKeyArn'] = self.kms_key_arn
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('KeyType') is not None:
            self.key_type = m.get('KeyType')
        if m.get('KmsKeyArn') is not None:
            self.kms_key_arn = m.get('KmsKeyArn')
        return self


class IncludedOAuth2ProviderConfig(TeaModel):
    def __init__(
        self,
        authorization_endpoint: str = None,
        client_id: str = None,
        client_secret: str = None,
        token_endpoint: str = None,
    ):
        self.authorization_endpoint = authorization_endpoint
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_endpoint = token_endpoint

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.authorization_endpoint is not None:
            result['AuthorizationEndpoint'] = self.authorization_endpoint
        if self.client_id is not None:
            result['ClientId'] = self.client_id
        if self.client_secret is not None:
            result['ClientSecret'] = self.client_secret
        if self.token_endpoint is not None:
            result['TokenEndpoint'] = self.token_endpoint
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AuthorizationEndpoint') is not None:
            self.authorization_endpoint = m.get('AuthorizationEndpoint')
        if m.get('ClientId') is not None:
            self.client_id = m.get('ClientId')
        if m.get('ClientSecret') is not None:
            self.client_secret = m.get('ClientSecret')
        if m.get('TokenEndpoint') is not None:
            self.token_endpoint = m.get('TokenEndpoint')
        return self


class OAuth2ProviderConfig(TeaModel):
    def __init__(
        self,
        custom_oauth_2provider_config: CustomOAuth2ProviderConfig = None,
        included_oauth_2provider_config: IncludedOAuth2ProviderConfig = None,
    ):
        self.custom_oauth_2provider_config = custom_oauth_2provider_config
        self.included_oauth_2provider_config = included_oauth_2provider_config

    def validate(self):
        if self.custom_oauth_2provider_config:
            self.custom_oauth_2provider_config.validate()
        if self.included_oauth_2provider_config:
            self.included_oauth_2provider_config.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.custom_oauth_2provider_config is not None:
            result['CustomOAuth2ProviderConfig'] = self.custom_oauth_2provider_config.to_map()
        if self.included_oauth_2provider_config is not None:
            result['IncludedOAuth2ProviderConfig'] = self.included_oauth_2provider_config.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CustomOAuth2ProviderConfig') is not None:
            temp_model = CustomOAuth2ProviderConfig()
            self.custom_oauth_2provider_config = temp_model.from_map(m['CustomOAuth2ProviderConfig'])
        if m.get('IncludedOAuth2ProviderConfig') is not None:
            temp_model = IncludedOAuth2ProviderConfig()
            self.included_oauth_2provider_config = temp_model.from_map(m['IncludedOAuth2ProviderConfig'])
        return self


class AddSAMLIdentityProviderCertificateRequest(TeaModel):
    def __init__(
        self,
        user_pool_name: str = None,
        x_509certificate: str = None,
    ):
        self.user_pool_name = user_pool_name
        self.x_509certificate = x_509certificate

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        if self.x_509certificate is not None:
            result['X509Certificate'] = self.x_509certificate
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        if m.get('X509Certificate') is not None:
            self.x_509certificate = m.get('X509Certificate')
        return self


class AddSAMLIdentityProviderCertificateResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
    ):
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class AddSAMLIdentityProviderCertificateResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: AddSAMLIdentityProviderCertificateResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = AddSAMLIdentityProviderCertificateResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class AttachPolicySetToGatewayRequest(TeaModel):
    def __init__(
        self,
        enforcement_mode: str = None,
        gateway_arn: str = None,
        policy_set_name: str = None,
    ):
        self.enforcement_mode = enforcement_mode
        self.gateway_arn = gateway_arn
        self.policy_set_name = policy_set_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.enforcement_mode is not None:
            result['EnforcementMode'] = self.enforcement_mode
        if self.gateway_arn is not None:
            result['GatewayArn'] = self.gateway_arn
        if self.policy_set_name is not None:
            result['PolicySetName'] = self.policy_set_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('EnforcementMode') is not None:
            self.enforcement_mode = m.get('EnforcementMode')
        if m.get('GatewayArn') is not None:
            self.gateway_arn = m.get('GatewayArn')
        if m.get('PolicySetName') is not None:
            self.policy_set_name = m.get('PolicySetName')
        return self


class AttachPolicySetToGatewayResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
    ):
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class AttachPolicySetToGatewayResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: AttachPolicySetToGatewayResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = AttachPolicySetToGatewayResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class CreateAPIKeyCredentialProviderRequest(TeaModel):
    def __init__(
        self,
        apikey: str = None,
        apikey_credential_provider_name: str = None,
        description: str = None,
        token_vault_name: str = None,
    ):
        self.apikey = apikey
        self.apikey_credential_provider_name = apikey_credential_provider_name
        self.description = description
        self.token_vault_name = token_vault_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.apikey is not None:
            result['APIKey'] = self.apikey
        if self.apikey_credential_provider_name is not None:
            result['APIKeyCredentialProviderName'] = self.apikey_credential_provider_name
        if self.description is not None:
            result['Description'] = self.description
        if self.token_vault_name is not None:
            result['TokenVaultName'] = self.token_vault_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('APIKey') is not None:
            self.apikey = m.get('APIKey')
        if m.get('APIKeyCredentialProviderName') is not None:
            self.apikey_credential_provider_name = m.get('APIKeyCredentialProviderName')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('TokenVaultName') is not None:
            self.token_vault_name = m.get('TokenVaultName')
        return self


class CreateAPIKeyCredentialProviderResponseBodyAPIKeyCredentialProvider(TeaModel):
    def __init__(
        self,
        apikey_credential_provider_name: str = None,
        create_time: str = None,
        credential_provider_arn: str = None,
        description: str = None,
        token_vault_name: str = None,
    ):
        self.apikey_credential_provider_name = apikey_credential_provider_name
        self.create_time = create_time
        self.credential_provider_arn = credential_provider_arn
        self.description = description
        self.token_vault_name = token_vault_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.apikey_credential_provider_name is not None:
            result['APIKeyCredentialProviderName'] = self.apikey_credential_provider_name
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.credential_provider_arn is not None:
            result['CredentialProviderArn'] = self.credential_provider_arn
        if self.description is not None:
            result['Description'] = self.description
        if self.token_vault_name is not None:
            result['TokenVaultName'] = self.token_vault_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('APIKeyCredentialProviderName') is not None:
            self.apikey_credential_provider_name = m.get('APIKeyCredentialProviderName')
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('CredentialProviderArn') is not None:
            self.credential_provider_arn = m.get('CredentialProviderArn')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('TokenVaultName') is not None:
            self.token_vault_name = m.get('TokenVaultName')
        return self


class CreateAPIKeyCredentialProviderResponseBody(TeaModel):
    def __init__(
        self,
        apikey_credential_provider: CreateAPIKeyCredentialProviderResponseBodyAPIKeyCredentialProvider = None,
        request_id: str = None,
    ):
        self.apikey_credential_provider = apikey_credential_provider
        self.request_id = request_id

    def validate(self):
        if self.apikey_credential_provider:
            self.apikey_credential_provider.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.apikey_credential_provider is not None:
            result['APIKeyCredentialProvider'] = self.apikey_credential_provider.to_map()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('APIKeyCredentialProvider') is not None:
            temp_model = CreateAPIKeyCredentialProviderResponseBodyAPIKeyCredentialProvider()
            self.apikey_credential_provider = temp_model.from_map(m['APIKeyCredentialProvider'])
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class CreateAPIKeyCredentialProviderResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: CreateAPIKeyCredentialProviderResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = CreateAPIKeyCredentialProviderResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class CreateClientSecretRequest(TeaModel):
    def __init__(
        self,
        client_id: str = None,
        client_name: str = None,
        user_pool_name: str = None,
    ):
        self.client_id = client_id
        self.client_name = client_name
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.client_id is not None:
            result['ClientId'] = self.client_id
        if self.client_name is not None:
            result['ClientName'] = self.client_name
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('ClientId') is not None:
            self.client_id = m.get('ClientId')
        if m.get('ClientName') is not None:
            self.client_name = m.get('ClientName')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class CreateClientSecretResponseBodyClientSecret(TeaModel):
    def __init__(
        self,
        client_secret_id: str = None,
        client_secret_value: str = None,
        create_time: str = None,
    ):
        self.client_secret_id = client_secret_id
        self.client_secret_value = client_secret_value
        self.create_time = create_time

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.client_secret_id is not None:
            result['ClientSecretId'] = self.client_secret_id
        if self.client_secret_value is not None:
            result['ClientSecretValue'] = self.client_secret_value
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('ClientSecretId') is not None:
            self.client_secret_id = m.get('ClientSecretId')
        if m.get('ClientSecretValue') is not None:
            self.client_secret_value = m.get('ClientSecretValue')
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        return self


class CreateClientSecretResponseBody(TeaModel):
    def __init__(
        self,
        client_id: str = None,
        client_secret: CreateClientSecretResponseBodyClientSecret = None,
        request_id: str = None,
        user_pool_name: str = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.request_id = request_id
        self.user_pool_name = user_pool_name

    def validate(self):
        if self.client_secret:
            self.client_secret.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.client_id is not None:
            result['ClientId'] = self.client_id
        if self.client_secret is not None:
            result['ClientSecret'] = self.client_secret.to_map()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('ClientId') is not None:
            self.client_id = m.get('ClientId')
        if m.get('ClientSecret') is not None:
            temp_model = CreateClientSecretResponseBodyClientSecret()
            self.client_secret = temp_model.from_map(m['ClientSecret'])
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class CreateClientSecretResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: CreateClientSecretResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = CreateClientSecretResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class CreateIdentityProviderRequest(TeaModel):
    def __init__(
        self,
        allowed_audience: List[str] = None,
        description: str = None,
        discovery_url: str = None,
        identity_provider_name: str = None,
    ):
        self.allowed_audience = allowed_audience
        self.description = description
        self.discovery_url = discovery_url
        self.identity_provider_name = identity_provider_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.allowed_audience is not None:
            result['AllowedAudience'] = self.allowed_audience
        if self.description is not None:
            result['Description'] = self.description
        if self.discovery_url is not None:
            result['DiscoveryURL'] = self.discovery_url
        if self.identity_provider_name is not None:
            result['IdentityProviderName'] = self.identity_provider_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AllowedAudience') is not None:
            self.allowed_audience = m.get('AllowedAudience')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('DiscoveryURL') is not None:
            self.discovery_url = m.get('DiscoveryURL')
        if m.get('IdentityProviderName') is not None:
            self.identity_provider_name = m.get('IdentityProviderName')
        return self


class CreateIdentityProviderShrinkRequest(TeaModel):
    def __init__(
        self,
        allowed_audience_shrink: str = None,
        description: str = None,
        discovery_url: str = None,
        identity_provider_name: str = None,
    ):
        self.allowed_audience_shrink = allowed_audience_shrink
        self.description = description
        self.discovery_url = discovery_url
        self.identity_provider_name = identity_provider_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.allowed_audience_shrink is not None:
            result['AllowedAudience'] = self.allowed_audience_shrink
        if self.description is not None:
            result['Description'] = self.description
        if self.discovery_url is not None:
            result['DiscoveryURL'] = self.discovery_url
        if self.identity_provider_name is not None:
            result['IdentityProviderName'] = self.identity_provider_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AllowedAudience') is not None:
            self.allowed_audience_shrink = m.get('AllowedAudience')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('DiscoveryURL') is not None:
            self.discovery_url = m.get('DiscoveryURL')
        if m.get('IdentityProviderName') is not None:
            self.identity_provider_name = m.get('IdentityProviderName')
        return self


class CreateIdentityProviderResponseBodyIdentityProvider(TeaModel):
    def __init__(
        self,
        allowed_audience: List[str] = None,
        create_time: str = None,
        description: str = None,
        discovery_url: str = None,
        identity_provider_arn: str = None,
        identity_provider_name: str = None,
        update_time: str = None,
    ):
        self.allowed_audience = allowed_audience
        self.create_time = create_time
        self.description = description
        self.discovery_url = discovery_url
        self.identity_provider_arn = identity_provider_arn
        self.identity_provider_name = identity_provider_name
        self.update_time = update_time

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.allowed_audience is not None:
            result['AllowedAudience'] = self.allowed_audience
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.description is not None:
            result['Description'] = self.description
        if self.discovery_url is not None:
            result['DiscoveryURL'] = self.discovery_url
        if self.identity_provider_arn is not None:
            result['IdentityProviderArn'] = self.identity_provider_arn
        if self.identity_provider_name is not None:
            result['IdentityProviderName'] = self.identity_provider_name
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AllowedAudience') is not None:
            self.allowed_audience = m.get('AllowedAudience')
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('DiscoveryURL') is not None:
            self.discovery_url = m.get('DiscoveryURL')
        if m.get('IdentityProviderArn') is not None:
            self.identity_provider_arn = m.get('IdentityProviderArn')
        if m.get('IdentityProviderName') is not None:
            self.identity_provider_name = m.get('IdentityProviderName')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        return self


class CreateIdentityProviderResponseBody(TeaModel):
    def __init__(
        self,
        identity_provider: CreateIdentityProviderResponseBodyIdentityProvider = None,
        request_id: str = None,
    ):
        self.identity_provider = identity_provider
        self.request_id = request_id

    def validate(self):
        if self.identity_provider:
            self.identity_provider.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.identity_provider is not None:
            result['IdentityProvider'] = self.identity_provider.to_map()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('IdentityProvider') is not None:
            temp_model = CreateIdentityProviderResponseBodyIdentityProvider()
            self.identity_provider = temp_model.from_map(m['IdentityProvider'])
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class CreateIdentityProviderResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: CreateIdentityProviderResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = CreateIdentityProviderResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class CreateOAuth2CredentialProviderRequest(TeaModel):
    def __init__(
        self,
        callback_url: str = None,
        credential_provider_vendor: str = None,
        description: str = None,
        oauth_2credential_provider_name: str = None,
        oauth_2provider_config: OAuth2ProviderConfig = None,
        token_vault_name: str = None,
    ):
        self.callback_url = callback_url
        self.credential_provider_vendor = credential_provider_vendor
        self.description = description
        self.oauth_2credential_provider_name = oauth_2credential_provider_name
        self.oauth_2provider_config = oauth_2provider_config
        self.token_vault_name = token_vault_name

    def validate(self):
        if self.oauth_2provider_config:
            self.oauth_2provider_config.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.callback_url is not None:
            result['CallbackURL'] = self.callback_url
        if self.credential_provider_vendor is not None:
            result['CredentialProviderVendor'] = self.credential_provider_vendor
        if self.description is not None:
            result['Description'] = self.description
        if self.oauth_2credential_provider_name is not None:
            result['OAuth2CredentialProviderName'] = self.oauth_2credential_provider_name
        if self.oauth_2provider_config is not None:
            result['OAuth2ProviderConfig'] = self.oauth_2provider_config.to_map()
        if self.token_vault_name is not None:
            result['TokenVaultName'] = self.token_vault_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CallbackURL') is not None:
            self.callback_url = m.get('CallbackURL')
        if m.get('CredentialProviderVendor') is not None:
            self.credential_provider_vendor = m.get('CredentialProviderVendor')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('OAuth2CredentialProviderName') is not None:
            self.oauth_2credential_provider_name = m.get('OAuth2CredentialProviderName')
        if m.get('OAuth2ProviderConfig') is not None:
            temp_model = OAuth2ProviderConfig()
            self.oauth_2provider_config = temp_model.from_map(m['OAuth2ProviderConfig'])
        if m.get('TokenVaultName') is not None:
            self.token_vault_name = m.get('TokenVaultName')
        return self


class CreateOAuth2CredentialProviderShrinkRequest(TeaModel):
    def __init__(
        self,
        callback_url: str = None,
        credential_provider_vendor: str = None,
        description: str = None,
        oauth_2credential_provider_name: str = None,
        oauth_2provider_config_shrink: str = None,
        token_vault_name: str = None,
    ):
        self.callback_url = callback_url
        self.credential_provider_vendor = credential_provider_vendor
        self.description = description
        self.oauth_2credential_provider_name = oauth_2credential_provider_name
        self.oauth_2provider_config_shrink = oauth_2provider_config_shrink
        self.token_vault_name = token_vault_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.callback_url is not None:
            result['CallbackURL'] = self.callback_url
        if self.credential_provider_vendor is not None:
            result['CredentialProviderVendor'] = self.credential_provider_vendor
        if self.description is not None:
            result['Description'] = self.description
        if self.oauth_2credential_provider_name is not None:
            result['OAuth2CredentialProviderName'] = self.oauth_2credential_provider_name
        if self.oauth_2provider_config_shrink is not None:
            result['OAuth2ProviderConfig'] = self.oauth_2provider_config_shrink
        if self.token_vault_name is not None:
            result['TokenVaultName'] = self.token_vault_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CallbackURL') is not None:
            self.callback_url = m.get('CallbackURL')
        if m.get('CredentialProviderVendor') is not None:
            self.credential_provider_vendor = m.get('CredentialProviderVendor')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('OAuth2CredentialProviderName') is not None:
            self.oauth_2credential_provider_name = m.get('OAuth2CredentialProviderName')
        if m.get('OAuth2ProviderConfig') is not None:
            self.oauth_2provider_config_shrink = m.get('OAuth2ProviderConfig')
        if m.get('TokenVaultName') is not None:
            self.token_vault_name = m.get('TokenVaultName')
        return self


class CreateOAuth2CredentialProviderResponseBodyOAuth2CredentialProvider(TeaModel):
    def __init__(
        self,
        callback_url: str = None,
        create_time: str = None,
        credential_provider_arn: str = None,
        credential_provider_vendor: str = None,
        description: str = None,
        oauth_2credential_provider_name: str = None,
        oauth_2provider_config: OAuth2ProviderConfig = None,
        token_vault_name: str = None,
        update_time: str = None,
    ):
        self.callback_url = callback_url
        self.create_time = create_time
        self.credential_provider_arn = credential_provider_arn
        self.credential_provider_vendor = credential_provider_vendor
        self.description = description
        self.oauth_2credential_provider_name = oauth_2credential_provider_name
        self.oauth_2provider_config = oauth_2provider_config
        self.token_vault_name = token_vault_name
        self.update_time = update_time

    def validate(self):
        if self.oauth_2provider_config:
            self.oauth_2provider_config.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.callback_url is not None:
            result['CallbackURL'] = self.callback_url
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.credential_provider_arn is not None:
            result['CredentialProviderArn'] = self.credential_provider_arn
        if self.credential_provider_vendor is not None:
            result['CredentialProviderVendor'] = self.credential_provider_vendor
        if self.description is not None:
            result['Description'] = self.description
        if self.oauth_2credential_provider_name is not None:
            result['OAuth2CredentialProviderName'] = self.oauth_2credential_provider_name
        if self.oauth_2provider_config is not None:
            result['OAuth2ProviderConfig'] = self.oauth_2provider_config.to_map()
        if self.token_vault_name is not None:
            result['TokenVaultName'] = self.token_vault_name
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CallbackURL') is not None:
            self.callback_url = m.get('CallbackURL')
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('CredentialProviderArn') is not None:
            self.credential_provider_arn = m.get('CredentialProviderArn')
        if m.get('CredentialProviderVendor') is not None:
            self.credential_provider_vendor = m.get('CredentialProviderVendor')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('OAuth2CredentialProviderName') is not None:
            self.oauth_2credential_provider_name = m.get('OAuth2CredentialProviderName')
        if m.get('OAuth2ProviderConfig') is not None:
            temp_model = OAuth2ProviderConfig()
            self.oauth_2provider_config = temp_model.from_map(m['OAuth2ProviderConfig'])
        if m.get('TokenVaultName') is not None:
            self.token_vault_name = m.get('TokenVaultName')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        return self


class CreateOAuth2CredentialProviderResponseBody(TeaModel):
    def __init__(
        self,
        oauth_2credential_provider: CreateOAuth2CredentialProviderResponseBodyOAuth2CredentialProvider = None,
        request_id: str = None,
    ):
        self.oauth_2credential_provider = oauth_2credential_provider
        self.request_id = request_id

    def validate(self):
        if self.oauth_2credential_provider:
            self.oauth_2credential_provider.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.oauth_2credential_provider is not None:
            result['OAuth2CredentialProvider'] = self.oauth_2credential_provider.to_map()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('OAuth2CredentialProvider') is not None:
            temp_model = CreateOAuth2CredentialProviderResponseBodyOAuth2CredentialProvider()
            self.oauth_2credential_provider = temp_model.from_map(m['OAuth2CredentialProvider'])
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class CreateOAuth2CredentialProviderResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: CreateOAuth2CredentialProviderResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = CreateOAuth2CredentialProviderResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class CreatePolicyRequest(TeaModel):
    def __init__(
        self,
        definition: Definition = None,
        description: str = None,
        policy_name: str = None,
        policy_set_name: str = None,
    ):
        self.definition = definition
        self.description = description
        self.policy_name = policy_name
        self.policy_set_name = policy_set_name

    def validate(self):
        if self.definition:
            self.definition.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.definition is not None:
            result['Definition'] = self.definition.to_map()
        if self.description is not None:
            result['Description'] = self.description
        if self.policy_name is not None:
            result['PolicyName'] = self.policy_name
        if self.policy_set_name is not None:
            result['PolicySetName'] = self.policy_set_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Definition') is not None:
            temp_model = Definition()
            self.definition = temp_model.from_map(m['Definition'])
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('PolicyName') is not None:
            self.policy_name = m.get('PolicyName')
        if m.get('PolicySetName') is not None:
            self.policy_set_name = m.get('PolicySetName')
        return self


class CreatePolicyShrinkRequest(TeaModel):
    def __init__(
        self,
        definition_shrink: str = None,
        description: str = None,
        policy_name: str = None,
        policy_set_name: str = None,
    ):
        self.definition_shrink = definition_shrink
        self.description = description
        self.policy_name = policy_name
        self.policy_set_name = policy_set_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.definition_shrink is not None:
            result['Definition'] = self.definition_shrink
        if self.description is not None:
            result['Description'] = self.description
        if self.policy_name is not None:
            result['PolicyName'] = self.policy_name
        if self.policy_set_name is not None:
            result['PolicySetName'] = self.policy_set_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Definition') is not None:
            self.definition_shrink = m.get('Definition')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('PolicyName') is not None:
            self.policy_name = m.get('PolicyName')
        if m.get('PolicySetName') is not None:
            self.policy_set_name = m.get('PolicySetName')
        return self


class CreatePolicyResponseBodyPolicy(TeaModel):
    def __init__(
        self,
        create_time: str = None,
        definition: Definition = None,
        description: str = None,
        policy_arn: str = None,
        policy_name: str = None,
        policy_set_name: str = None,
    ):
        self.create_time = create_time
        self.definition = definition
        self.description = description
        self.policy_arn = policy_arn
        self.policy_name = policy_name
        self.policy_set_name = policy_set_name

    def validate(self):
        if self.definition:
            self.definition.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.definition is not None:
            result['Definition'] = self.definition.to_map()
        if self.description is not None:
            result['Description'] = self.description
        if self.policy_arn is not None:
            result['PolicyArn'] = self.policy_arn
        if self.policy_name is not None:
            result['PolicyName'] = self.policy_name
        if self.policy_set_name is not None:
            result['PolicySetName'] = self.policy_set_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('Definition') is not None:
            temp_model = Definition()
            self.definition = temp_model.from_map(m['Definition'])
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('PolicyArn') is not None:
            self.policy_arn = m.get('PolicyArn')
        if m.get('PolicyName') is not None:
            self.policy_name = m.get('PolicyName')
        if m.get('PolicySetName') is not None:
            self.policy_set_name = m.get('PolicySetName')
        return self


class CreatePolicyResponseBody(TeaModel):
    def __init__(
        self,
        policy: CreatePolicyResponseBodyPolicy = None,
        request_id: str = None,
    ):
        self.policy = policy
        self.request_id = request_id

    def validate(self):
        if self.policy:
            self.policy.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.policy is not None:
            result['Policy'] = self.policy.to_map()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Policy') is not None:
            temp_model = CreatePolicyResponseBodyPolicy()
            self.policy = temp_model.from_map(m['Policy'])
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class CreatePolicyResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: CreatePolicyResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = CreatePolicyResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class CreatePolicySetRequest(TeaModel):
    def __init__(
        self,
        description: str = None,
        policy_set_name: str = None,
    ):
        self.description = description
        self.policy_set_name = policy_set_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.description is not None:
            result['Description'] = self.description
        if self.policy_set_name is not None:
            result['PolicySetName'] = self.policy_set_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('PolicySetName') is not None:
            self.policy_set_name = m.get('PolicySetName')
        return self


class CreatePolicySetResponseBodyPolicySet(TeaModel):
    def __init__(
        self,
        create_time: str = None,
        description: str = None,
        policy_set_arn: str = None,
        policy_set_name: str = None,
    ):
        self.create_time = create_time
        self.description = description
        self.policy_set_arn = policy_set_arn
        self.policy_set_name = policy_set_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.description is not None:
            result['Description'] = self.description
        if self.policy_set_arn is not None:
            result['PolicySetArn'] = self.policy_set_arn
        if self.policy_set_name is not None:
            result['PolicySetName'] = self.policy_set_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('PolicySetArn') is not None:
            self.policy_set_arn = m.get('PolicySetArn')
        if m.get('PolicySetName') is not None:
            self.policy_set_name = m.get('PolicySetName')
        return self


class CreatePolicySetResponseBody(TeaModel):
    def __init__(
        self,
        policy_set: CreatePolicySetResponseBodyPolicySet = None,
        request_id: str = None,
    ):
        self.policy_set = policy_set
        self.request_id = request_id

    def validate(self):
        if self.policy_set:
            self.policy_set.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.policy_set is not None:
            result['PolicySet'] = self.policy_set.to_map()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('PolicySet') is not None:
            temp_model = CreatePolicySetResponseBodyPolicySet()
            self.policy_set = temp_model.from_map(m['PolicySet'])
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class CreatePolicySetResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: CreatePolicySetResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = CreatePolicySetResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class CreateRoleRequest(TeaModel):
    def __init__(
        self,
        description: str = None,
        role_name: str = None,
        user_pool_name: str = None,
    ):
        self.description = description
        self.role_name = role_name
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.description is not None:
            result['Description'] = self.description
        if self.role_name is not None:
            result['RoleName'] = self.role_name
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('RoleName') is not None:
            self.role_name = m.get('RoleName')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class CreateRoleResponseBodyRole(TeaModel):
    def __init__(
        self,
        create_time: str = None,
        description: str = None,
        role_id: str = None,
        role_name: str = None,
        type: str = None,
        update_time: str = None,
    ):
        self.create_time = create_time
        self.description = description
        self.role_id = role_id
        self.role_name = role_name
        self.type = type
        self.update_time = update_time

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.description is not None:
            result['Description'] = self.description
        if self.role_id is not None:
            result['RoleId'] = self.role_id
        if self.role_name is not None:
            result['RoleName'] = self.role_name
        if self.type is not None:
            result['Type'] = self.type
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('RoleId') is not None:
            self.role_id = m.get('RoleId')
        if m.get('RoleName') is not None:
            self.role_name = m.get('RoleName')
        if m.get('Type') is not None:
            self.type = m.get('Type')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        return self


class CreateRoleResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
        role: CreateRoleResponseBodyRole = None,
    ):
        self.request_id = request_id
        self.role = role

    def validate(self):
        if self.role:
            self.role.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.role is not None:
            result['Role'] = self.role.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('Role') is not None:
            temp_model = CreateRoleResponseBodyRole()
            self.role = temp_model.from_map(m['Role'])
        return self


class CreateRoleResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: CreateRoleResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = CreateRoleResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class CreateRoleAssignmentRequest(TeaModel):
    def __init__(
        self,
        principal_name: str = None,
        principal_type: str = None,
        role_name: str = None,
        user_pool_name: str = None,
    ):
        self.principal_name = principal_name
        self.principal_type = principal_type
        self.role_name = role_name
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.principal_name is not None:
            result['PrincipalName'] = self.principal_name
        if self.principal_type is not None:
            result['PrincipalType'] = self.principal_type
        if self.role_name is not None:
            result['RoleName'] = self.role_name
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('PrincipalName') is not None:
            self.principal_name = m.get('PrincipalName')
        if m.get('PrincipalType') is not None:
            self.principal_type = m.get('PrincipalType')
        if m.get('RoleName') is not None:
            self.role_name = m.get('RoleName')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class CreateRoleAssignmentResponseBodyRoleAssignment(TeaModel):
    def __init__(
        self,
        create_time: str = None,
        principal_id: str = None,
        principal_name: str = None,
        principal_type: str = None,
        role_id: str = None,
        role_name: str = None,
        user_pool_id: str = None,
    ):
        self.create_time = create_time
        self.principal_id = principal_id
        self.principal_name = principal_name
        self.principal_type = principal_type
        self.role_id = role_id
        self.role_name = role_name
        self.user_pool_id = user_pool_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.principal_id is not None:
            result['PrincipalId'] = self.principal_id
        if self.principal_name is not None:
            result['PrincipalName'] = self.principal_name
        if self.principal_type is not None:
            result['PrincipalType'] = self.principal_type
        if self.role_id is not None:
            result['RoleId'] = self.role_id
        if self.role_name is not None:
            result['RoleName'] = self.role_name
        if self.user_pool_id is not None:
            result['UserPoolId'] = self.user_pool_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('PrincipalId') is not None:
            self.principal_id = m.get('PrincipalId')
        if m.get('PrincipalName') is not None:
            self.principal_name = m.get('PrincipalName')
        if m.get('PrincipalType') is not None:
            self.principal_type = m.get('PrincipalType')
        if m.get('RoleId') is not None:
            self.role_id = m.get('RoleId')
        if m.get('RoleName') is not None:
            self.role_name = m.get('RoleName')
        if m.get('UserPoolId') is not None:
            self.user_pool_id = m.get('UserPoolId')
        return self


class CreateRoleAssignmentResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
        role_assignment: CreateRoleAssignmentResponseBodyRoleAssignment = None,
    ):
        self.request_id = request_id
        self.role_assignment = role_assignment

    def validate(self):
        if self.role_assignment:
            self.role_assignment.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.role_assignment is not None:
            result['RoleAssignment'] = self.role_assignment.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('RoleAssignment') is not None:
            temp_model = CreateRoleAssignmentResponseBodyRoleAssignment()
            self.role_assignment = temp_model.from_map(m['RoleAssignment'])
        return self


class CreateRoleAssignmentResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: CreateRoleAssignmentResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = CreateRoleAssignmentResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class CreateTokenVaultRequest(TeaModel):
    def __init__(
        self,
        description: str = None,
        encryption_config: EncryptionConfig = None,
        role_arn: str = None,
        token_vault_name: str = None,
    ):
        self.description = description
        self.encryption_config = encryption_config
        self.role_arn = role_arn
        self.token_vault_name = token_vault_name

    def validate(self):
        if self.encryption_config:
            self.encryption_config.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.description is not None:
            result['Description'] = self.description
        if self.encryption_config is not None:
            result['EncryptionConfig'] = self.encryption_config.to_map()
        if self.role_arn is not None:
            result['RoleArn'] = self.role_arn
        if self.token_vault_name is not None:
            result['TokenVaultName'] = self.token_vault_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('EncryptionConfig') is not None:
            temp_model = EncryptionConfig()
            self.encryption_config = temp_model.from_map(m['EncryptionConfig'])
        if m.get('RoleArn') is not None:
            self.role_arn = m.get('RoleArn')
        if m.get('TokenVaultName') is not None:
            self.token_vault_name = m.get('TokenVaultName')
        return self


class CreateTokenVaultShrinkRequest(TeaModel):
    def __init__(
        self,
        description: str = None,
        encryption_config_shrink: str = None,
        role_arn: str = None,
        token_vault_name: str = None,
    ):
        self.description = description
        self.encryption_config_shrink = encryption_config_shrink
        self.role_arn = role_arn
        self.token_vault_name = token_vault_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.description is not None:
            result['Description'] = self.description
        if self.encryption_config_shrink is not None:
            result['EncryptionConfig'] = self.encryption_config_shrink
        if self.role_arn is not None:
            result['RoleArn'] = self.role_arn
        if self.token_vault_name is not None:
            result['TokenVaultName'] = self.token_vault_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('EncryptionConfig') is not None:
            self.encryption_config_shrink = m.get('EncryptionConfig')
        if m.get('RoleArn') is not None:
            self.role_arn = m.get('RoleArn')
        if m.get('TokenVaultName') is not None:
            self.token_vault_name = m.get('TokenVaultName')
        return self


class CreateTokenVaultResponseBodyTokenVaultEncryptionConfig(TeaModel):
    def __init__(
        self,
        key_type: str = None,
        kms_key_arn: str = None,
    ):
        self.key_type = key_type
        self.kms_key_arn = kms_key_arn

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.key_type is not None:
            result['KeyType'] = self.key_type
        if self.kms_key_arn is not None:
            result['KmsKeyArn'] = self.kms_key_arn
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('KeyType') is not None:
            self.key_type = m.get('KeyType')
        if m.get('KmsKeyArn') is not None:
            self.kms_key_arn = m.get('KmsKeyArn')
        return self


class CreateTokenVaultResponseBodyTokenVault(TeaModel):
    def __init__(
        self,
        create_time: str = None,
        description: str = None,
        encryption_config: CreateTokenVaultResponseBodyTokenVaultEncryptionConfig = None,
        role_arn: str = None,
        token_vault_arn: str = None,
        token_vault_name: str = None,
    ):
        self.create_time = create_time
        self.description = description
        self.encryption_config = encryption_config
        self.role_arn = role_arn
        self.token_vault_arn = token_vault_arn
        self.token_vault_name = token_vault_name

    def validate(self):
        if self.encryption_config:
            self.encryption_config.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.description is not None:
            result['Description'] = self.description
        if self.encryption_config is not None:
            result['EncryptionConfig'] = self.encryption_config.to_map()
        if self.role_arn is not None:
            result['RoleArn'] = self.role_arn
        if self.token_vault_arn is not None:
            result['TokenVaultArn'] = self.token_vault_arn
        if self.token_vault_name is not None:
            result['TokenVaultName'] = self.token_vault_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('EncryptionConfig') is not None:
            temp_model = CreateTokenVaultResponseBodyTokenVaultEncryptionConfig()
            self.encryption_config = temp_model.from_map(m['EncryptionConfig'])
        if m.get('RoleArn') is not None:
            self.role_arn = m.get('RoleArn')
        if m.get('TokenVaultArn') is not None:
            self.token_vault_arn = m.get('TokenVaultArn')
        if m.get('TokenVaultName') is not None:
            self.token_vault_name = m.get('TokenVaultName')
        return self


class CreateTokenVaultResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
        token_vault: CreateTokenVaultResponseBodyTokenVault = None,
    ):
        self.request_id = request_id
        self.token_vault = token_vault

    def validate(self):
        if self.token_vault:
            self.token_vault.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.token_vault is not None:
            result['TokenVault'] = self.token_vault.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('TokenVault') is not None:
            temp_model = CreateTokenVaultResponseBodyTokenVault()
            self.token_vault = temp_model.from_map(m['TokenVault'])
        return self


class CreateTokenVaultResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: CreateTokenVaultResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = CreateTokenVaultResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class CreateUserPoolRequest(TeaModel):
    def __init__(
        self,
        description: str = None,
        user_pool_name: str = None,
    ):
        self.description = description
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.description is not None:
            result['Description'] = self.description
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class CreateUserPoolResponseBodyUserPool(TeaModel):
    def __init__(
        self,
        create_time: str = None,
        description: str = None,
        update_time: str = None,
        user_pool_arn: str = None,
        user_pool_id: str = None,
        user_pool_name: str = None,
    ):
        self.create_time = create_time
        self.description = description
        self.update_time = update_time
        self.user_pool_arn = user_pool_arn
        self.user_pool_id = user_pool_id
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.description is not None:
            result['Description'] = self.description
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        if self.user_pool_arn is not None:
            result['UserPoolArn'] = self.user_pool_arn
        if self.user_pool_id is not None:
            result['UserPoolId'] = self.user_pool_id
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        if m.get('UserPoolArn') is not None:
            self.user_pool_arn = m.get('UserPoolArn')
        if m.get('UserPoolId') is not None:
            self.user_pool_id = m.get('UserPoolId')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class CreateUserPoolResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
        user_pool: CreateUserPoolResponseBodyUserPool = None,
    ):
        self.request_id = request_id
        self.user_pool = user_pool

    def validate(self):
        if self.user_pool:
            self.user_pool.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.user_pool is not None:
            result['UserPool'] = self.user_pool.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('UserPool') is not None:
            temp_model = CreateUserPoolResponseBodyUserPool()
            self.user_pool = temp_model.from_map(m['UserPool'])
        return self


class CreateUserPoolResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: CreateUserPoolResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = CreateUserPoolResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class CreateUserPoolClientRequest(TeaModel):
    def __init__(
        self,
        access_token_validity: str = None,
        client_name: str = None,
        enforce_pkce: bool = None,
        redirect_uris: str = None,
        refresh_token_validity: str = None,
        secret_required: bool = None,
        user_pool_name: str = None,
    ):
        self.access_token_validity = access_token_validity
        self.client_name = client_name
        self.enforce_pkce = enforce_pkce
        self.redirect_uris = redirect_uris
        self.refresh_token_validity = refresh_token_validity
        self.secret_required = secret_required
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.access_token_validity is not None:
            result['AccessTokenValidity'] = self.access_token_validity
        if self.client_name is not None:
            result['ClientName'] = self.client_name
        if self.enforce_pkce is not None:
            result['EnforcePKCE'] = self.enforce_pkce
        if self.redirect_uris is not None:
            result['RedirectURIs'] = self.redirect_uris
        if self.refresh_token_validity is not None:
            result['RefreshTokenValidity'] = self.refresh_token_validity
        if self.secret_required is not None:
            result['SecretRequired'] = self.secret_required
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AccessTokenValidity') is not None:
            self.access_token_validity = m.get('AccessTokenValidity')
        if m.get('ClientName') is not None:
            self.client_name = m.get('ClientName')
        if m.get('EnforcePKCE') is not None:
            self.enforce_pkce = m.get('EnforcePKCE')
        if m.get('RedirectURIs') is not None:
            self.redirect_uris = m.get('RedirectURIs')
        if m.get('RefreshTokenValidity') is not None:
            self.refresh_token_validity = m.get('RefreshTokenValidity')
        if m.get('SecretRequired') is not None:
            self.secret_required = m.get('SecretRequired')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class CreateUserPoolClientResponseBodyClientClientScopes(TeaModel):
    def __init__(
        self,
        description: str = None,
        scope_name: str = None,
    ):
        self.description = description
        self.scope_name = scope_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.description is not None:
            result['Description'] = self.description
        if self.scope_name is not None:
            result['ScopeName'] = self.scope_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('ScopeName') is not None:
            self.scope_name = m.get('ScopeName')
        return self


class CreateUserPoolClientResponseBodyClient(TeaModel):
    def __init__(
        self,
        access_token_validity: str = None,
        client_id: str = None,
        client_name: str = None,
        client_scopes: List[CreateUserPoolClientResponseBodyClientClientScopes] = None,
        create_time: str = None,
        enforce_pkce: bool = None,
        redirect_uris: List[str] = None,
        refresh_token_validity: str = None,
        secret_required: bool = None,
        update_time: str = None,
        user_pool_name: str = None,
    ):
        self.access_token_validity = access_token_validity
        self.client_id = client_id
        self.client_name = client_name
        self.client_scopes = client_scopes
        self.create_time = create_time
        self.enforce_pkce = enforce_pkce
        self.redirect_uris = redirect_uris
        self.refresh_token_validity = refresh_token_validity
        self.secret_required = secret_required
        self.update_time = update_time
        self.user_pool_name = user_pool_name

    def validate(self):
        if self.client_scopes:
            for k in self.client_scopes:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.access_token_validity is not None:
            result['AccessTokenValidity'] = self.access_token_validity
        if self.client_id is not None:
            result['ClientId'] = self.client_id
        if self.client_name is not None:
            result['ClientName'] = self.client_name
        result['ClientScopes'] = []
        if self.client_scopes is not None:
            for k in self.client_scopes:
                result['ClientScopes'].append(k.to_map() if k else None)
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.enforce_pkce is not None:
            result['EnforcePKCE'] = self.enforce_pkce
        if self.redirect_uris is not None:
            result['RedirectURIs'] = self.redirect_uris
        if self.refresh_token_validity is not None:
            result['RefreshTokenValidity'] = self.refresh_token_validity
        if self.secret_required is not None:
            result['SecretRequired'] = self.secret_required
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AccessTokenValidity') is not None:
            self.access_token_validity = m.get('AccessTokenValidity')
        if m.get('ClientId') is not None:
            self.client_id = m.get('ClientId')
        if m.get('ClientName') is not None:
            self.client_name = m.get('ClientName')
        self.client_scopes = []
        if m.get('ClientScopes') is not None:
            for k in m.get('ClientScopes'):
                temp_model = CreateUserPoolClientResponseBodyClientClientScopes()
                self.client_scopes.append(temp_model.from_map(k))
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('EnforcePKCE') is not None:
            self.enforce_pkce = m.get('EnforcePKCE')
        if m.get('RedirectURIs') is not None:
            self.redirect_uris = m.get('RedirectURIs')
        if m.get('RefreshTokenValidity') is not None:
            self.refresh_token_validity = m.get('RefreshTokenValidity')
        if m.get('SecretRequired') is not None:
            self.secret_required = m.get('SecretRequired')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class CreateUserPoolClientResponseBody(TeaModel):
    def __init__(
        self,
        client: CreateUserPoolClientResponseBodyClient = None,
        request_id: str = None,
    ):
        self.client = client
        self.request_id = request_id

    def validate(self):
        if self.client:
            self.client.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.client is not None:
            result['Client'] = self.client.to_map()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Client') is not None:
            temp_model = CreateUserPoolClientResponseBodyClient()
            self.client = temp_model.from_map(m['Client'])
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class CreateUserPoolClientResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: CreateUserPoolClientResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = CreateUserPoolClientResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class CreateWorkloadIdentityRequest(TeaModel):
    def __init__(
        self,
        allowed_resource_oauth_2return_urls: List[str] = None,
        description: str = None,
        identity_provider_name: str = None,
        role_arn: str = None,
        workload_identity_name: str = None,
    ):
        self.allowed_resource_oauth_2return_urls = allowed_resource_oauth_2return_urls
        self.description = description
        self.identity_provider_name = identity_provider_name
        self.role_arn = role_arn
        self.workload_identity_name = workload_identity_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.allowed_resource_oauth_2return_urls is not None:
            result['AllowedResourceOAuth2ReturnURLs'] = self.allowed_resource_oauth_2return_urls
        if self.description is not None:
            result['Description'] = self.description
        if self.identity_provider_name is not None:
            result['IdentityProviderName'] = self.identity_provider_name
        if self.role_arn is not None:
            result['RoleArn'] = self.role_arn
        if self.workload_identity_name is not None:
            result['WorkloadIdentityName'] = self.workload_identity_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AllowedResourceOAuth2ReturnURLs') is not None:
            self.allowed_resource_oauth_2return_urls = m.get('AllowedResourceOAuth2ReturnURLs')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('IdentityProviderName') is not None:
            self.identity_provider_name = m.get('IdentityProviderName')
        if m.get('RoleArn') is not None:
            self.role_arn = m.get('RoleArn')
        if m.get('WorkloadIdentityName') is not None:
            self.workload_identity_name = m.get('WorkloadIdentityName')
        return self


class CreateWorkloadIdentityShrinkRequest(TeaModel):
    def __init__(
        self,
        allowed_resource_oauth_2return_urls_shrink: str = None,
        description: str = None,
        identity_provider_name: str = None,
        role_arn: str = None,
        workload_identity_name: str = None,
    ):
        self.allowed_resource_oauth_2return_urls_shrink = allowed_resource_oauth_2return_urls_shrink
        self.description = description
        self.identity_provider_name = identity_provider_name
        self.role_arn = role_arn
        self.workload_identity_name = workload_identity_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.allowed_resource_oauth_2return_urls_shrink is not None:
            result['AllowedResourceOAuth2ReturnURLs'] = self.allowed_resource_oauth_2return_urls_shrink
        if self.description is not None:
            result['Description'] = self.description
        if self.identity_provider_name is not None:
            result['IdentityProviderName'] = self.identity_provider_name
        if self.role_arn is not None:
            result['RoleArn'] = self.role_arn
        if self.workload_identity_name is not None:
            result['WorkloadIdentityName'] = self.workload_identity_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AllowedResourceOAuth2ReturnURLs') is not None:
            self.allowed_resource_oauth_2return_urls_shrink = m.get('AllowedResourceOAuth2ReturnURLs')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('IdentityProviderName') is not None:
            self.identity_provider_name = m.get('IdentityProviderName')
        if m.get('RoleArn') is not None:
            self.role_arn = m.get('RoleArn')
        if m.get('WorkloadIdentityName') is not None:
            self.workload_identity_name = m.get('WorkloadIdentityName')
        return self


class CreateWorkloadIdentityResponseBodyWorkloadIdentity(TeaModel):
    def __init__(
        self,
        allowed_resource_oauth_2return_urls: List[str] = None,
        create_time: str = None,
        description: str = None,
        identity_provider_name: str = None,
        role_arn: str = None,
        update_time: str = None,
        workload_identity_arn: str = None,
        workload_identity_name: str = None,
    ):
        self.allowed_resource_oauth_2return_urls = allowed_resource_oauth_2return_urls
        self.create_time = create_time
        self.description = description
        self.identity_provider_name = identity_provider_name
        self.role_arn = role_arn
        self.update_time = update_time
        self.workload_identity_arn = workload_identity_arn
        self.workload_identity_name = workload_identity_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.allowed_resource_oauth_2return_urls is not None:
            result['AllowedResourceOAuth2ReturnURLs'] = self.allowed_resource_oauth_2return_urls
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.description is not None:
            result['Description'] = self.description
        if self.identity_provider_name is not None:
            result['IdentityProviderName'] = self.identity_provider_name
        if self.role_arn is not None:
            result['RoleArn'] = self.role_arn
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        if self.workload_identity_arn is not None:
            result['WorkloadIdentityArn'] = self.workload_identity_arn
        if self.workload_identity_name is not None:
            result['WorkloadIdentityName'] = self.workload_identity_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AllowedResourceOAuth2ReturnURLs') is not None:
            self.allowed_resource_oauth_2return_urls = m.get('AllowedResourceOAuth2ReturnURLs')
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('IdentityProviderName') is not None:
            self.identity_provider_name = m.get('IdentityProviderName')
        if m.get('RoleArn') is not None:
            self.role_arn = m.get('RoleArn')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        if m.get('WorkloadIdentityArn') is not None:
            self.workload_identity_arn = m.get('WorkloadIdentityArn')
        if m.get('WorkloadIdentityName') is not None:
            self.workload_identity_name = m.get('WorkloadIdentityName')
        return self


class CreateWorkloadIdentityResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
        workload_identity: CreateWorkloadIdentityResponseBodyWorkloadIdentity = None,
    ):
        self.request_id = request_id
        self.workload_identity = workload_identity

    def validate(self):
        if self.workload_identity:
            self.workload_identity.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.workload_identity is not None:
            result['WorkloadIdentity'] = self.workload_identity.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('WorkloadIdentity') is not None:
            temp_model = CreateWorkloadIdentityResponseBodyWorkloadIdentity()
            self.workload_identity = temp_model.from_map(m['WorkloadIdentity'])
        return self


class CreateWorkloadIdentityResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: CreateWorkloadIdentityResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = CreateWorkloadIdentityResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class DeleteAPIKeyCredentialProviderRequest(TeaModel):
    def __init__(
        self,
        apikey_credential_provider_name: str = None,
        token_vault_name: str = None,
    ):
        self.apikey_credential_provider_name = apikey_credential_provider_name
        self.token_vault_name = token_vault_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.apikey_credential_provider_name is not None:
            result['APIKeyCredentialProviderName'] = self.apikey_credential_provider_name
        if self.token_vault_name is not None:
            result['TokenVaultName'] = self.token_vault_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('APIKeyCredentialProviderName') is not None:
            self.apikey_credential_provider_name = m.get('APIKeyCredentialProviderName')
        if m.get('TokenVaultName') is not None:
            self.token_vault_name = m.get('TokenVaultName')
        return self


class DeleteAPIKeyCredentialProviderResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
    ):
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class DeleteAPIKeyCredentialProviderResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: DeleteAPIKeyCredentialProviderResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = DeleteAPIKeyCredentialProviderResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class DeleteClientSecretRequest(TeaModel):
    def __init__(
        self,
        client_id: str = None,
        client_name: str = None,
        client_secret_id: str = None,
        user_pool_name: str = None,
    ):
        self.client_id = client_id
        self.client_name = client_name
        self.client_secret_id = client_secret_id
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.client_id is not None:
            result['ClientId'] = self.client_id
        if self.client_name is not None:
            result['ClientName'] = self.client_name
        if self.client_secret_id is not None:
            result['ClientSecretId'] = self.client_secret_id
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('ClientId') is not None:
            self.client_id = m.get('ClientId')
        if m.get('ClientName') is not None:
            self.client_name = m.get('ClientName')
        if m.get('ClientSecretId') is not None:
            self.client_secret_id = m.get('ClientSecretId')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class DeleteClientSecretResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
    ):
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class DeleteClientSecretResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: DeleteClientSecretResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = DeleteClientSecretResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class DeleteIdentityProviderRequest(TeaModel):
    def __init__(
        self,
        identity_provider_name: str = None,
    ):
        self.identity_provider_name = identity_provider_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.identity_provider_name is not None:
            result['IdentityProviderName'] = self.identity_provider_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('IdentityProviderName') is not None:
            self.identity_provider_name = m.get('IdentityProviderName')
        return self


class DeleteIdentityProviderResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
    ):
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class DeleteIdentityProviderResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: DeleteIdentityProviderResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = DeleteIdentityProviderResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class DeleteOAuth2CredentialProviderRequest(TeaModel):
    def __init__(
        self,
        oauth_2credential_provider_name: str = None,
        token_vault_name: str = None,
    ):
        self.oauth_2credential_provider_name = oauth_2credential_provider_name
        self.token_vault_name = token_vault_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.oauth_2credential_provider_name is not None:
            result['OAuth2CredentialProviderName'] = self.oauth_2credential_provider_name
        if self.token_vault_name is not None:
            result['TokenVaultName'] = self.token_vault_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('OAuth2CredentialProviderName') is not None:
            self.oauth_2credential_provider_name = m.get('OAuth2CredentialProviderName')
        if m.get('TokenVaultName') is not None:
            self.token_vault_name = m.get('TokenVaultName')
        return self


class DeleteOAuth2CredentialProviderResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
    ):
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class DeleteOAuth2CredentialProviderResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: DeleteOAuth2CredentialProviderResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = DeleteOAuth2CredentialProviderResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class DeletePolicyRequest(TeaModel):
    def __init__(
        self,
        policy_name: str = None,
        policy_set_name: str = None,
    ):
        self.policy_name = policy_name
        self.policy_set_name = policy_set_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.policy_name is not None:
            result['PolicyName'] = self.policy_name
        if self.policy_set_name is not None:
            result['PolicySetName'] = self.policy_set_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('PolicyName') is not None:
            self.policy_name = m.get('PolicyName')
        if m.get('PolicySetName') is not None:
            self.policy_set_name = m.get('PolicySetName')
        return self


class DeletePolicyResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
    ):
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class DeletePolicyResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: DeletePolicyResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = DeletePolicyResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class DeletePolicySetRequest(TeaModel):
    def __init__(
        self,
        policy_set_name: str = None,
    ):
        self.policy_set_name = policy_set_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.policy_set_name is not None:
            result['PolicySetName'] = self.policy_set_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('PolicySetName') is not None:
            self.policy_set_name = m.get('PolicySetName')
        return self


class DeletePolicySetResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
    ):
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class DeletePolicySetResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: DeletePolicySetResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = DeletePolicySetResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class DeleteRoleRequest(TeaModel):
    def __init__(
        self,
        role_name: str = None,
        user_pool_name: str = None,
    ):
        self.role_name = role_name
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.role_name is not None:
            result['RoleName'] = self.role_name
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RoleName') is not None:
            self.role_name = m.get('RoleName')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class DeleteRoleResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
    ):
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class DeleteRoleResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: DeleteRoleResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = DeleteRoleResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class DeleteRoleAssignmentRequest(TeaModel):
    def __init__(
        self,
        principal_name: str = None,
        principal_type: str = None,
        role_name: str = None,
        user_pool_name: str = None,
    ):
        self.principal_name = principal_name
        self.principal_type = principal_type
        self.role_name = role_name
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.principal_name is not None:
            result['PrincipalName'] = self.principal_name
        if self.principal_type is not None:
            result['PrincipalType'] = self.principal_type
        if self.role_name is not None:
            result['RoleName'] = self.role_name
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('PrincipalName') is not None:
            self.principal_name = m.get('PrincipalName')
        if m.get('PrincipalType') is not None:
            self.principal_type = m.get('PrincipalType')
        if m.get('RoleName') is not None:
            self.role_name = m.get('RoleName')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class DeleteRoleAssignmentResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
    ):
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class DeleteRoleAssignmentResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: DeleteRoleAssignmentResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = DeleteRoleAssignmentResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class DeleteSAMLIdentityProviderCertificateRequest(TeaModel):
    def __init__(
        self,
        certificate_id: str = None,
        user_pool_name: str = None,
    ):
        self.certificate_id = certificate_id
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.certificate_id is not None:
            result['CertificateId'] = self.certificate_id
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CertificateId') is not None:
            self.certificate_id = m.get('CertificateId')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class DeleteSAMLIdentityProviderCertificateResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
    ):
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class DeleteSAMLIdentityProviderCertificateResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: DeleteSAMLIdentityProviderCertificateResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = DeleteSAMLIdentityProviderCertificateResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class DeleteTokenVaultRequest(TeaModel):
    def __init__(
        self,
        token_vault_name: str = None,
    ):
        self.token_vault_name = token_vault_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.token_vault_name is not None:
            result['TokenVaultName'] = self.token_vault_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('TokenVaultName') is not None:
            self.token_vault_name = m.get('TokenVaultName')
        return self


class DeleteTokenVaultResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
    ):
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class DeleteTokenVaultResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: DeleteTokenVaultResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = DeleteTokenVaultResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class DeleteUserRequest(TeaModel):
    def __init__(
        self,
        user_name: str = None,
        user_pool_name: str = None,
    ):
        self.user_name = user_name
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.user_name is not None:
            result['UserName'] = self.user_name
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('UserName') is not None:
            self.user_name = m.get('UserName')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class DeleteUserResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
    ):
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class DeleteUserResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: DeleteUserResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = DeleteUserResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class DeleteUserPoolRequest(TeaModel):
    def __init__(
        self,
        user_pool_name: str = None,
    ):
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class DeleteUserPoolResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
    ):
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class DeleteUserPoolResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: DeleteUserPoolResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = DeleteUserPoolResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class DeleteUserPoolClientRequest(TeaModel):
    def __init__(
        self,
        client_name: str = None,
        user_pool_name: str = None,
    ):
        self.client_name = client_name
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.client_name is not None:
            result['ClientName'] = self.client_name
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('ClientName') is not None:
            self.client_name = m.get('ClientName')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class DeleteUserPoolClientResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
    ):
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class DeleteUserPoolClientResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: DeleteUserPoolClientResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = DeleteUserPoolClientResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class DeleteWorkloadIdentityRequest(TeaModel):
    def __init__(
        self,
        workload_identity_name: str = None,
    ):
        self.workload_identity_name = workload_identity_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.workload_identity_name is not None:
            result['WorkloadIdentityName'] = self.workload_identity_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('WorkloadIdentityName') is not None:
            self.workload_identity_name = m.get('WorkloadIdentityName')
        return self


class DeleteWorkloadIdentityResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
    ):
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class DeleteWorkloadIdentityResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: DeleteWorkloadIdentityResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = DeleteWorkloadIdentityResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class DetachPolicySetFromGatewayRequest(TeaModel):
    def __init__(
        self,
        gateway_arn: str = None,
        policy_set_name: str = None,
    ):
        self.gateway_arn = gateway_arn
        self.policy_set_name = policy_set_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.gateway_arn is not None:
            result['GatewayArn'] = self.gateway_arn
        if self.policy_set_name is not None:
            result['PolicySetName'] = self.policy_set_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('GatewayArn') is not None:
            self.gateway_arn = m.get('GatewayArn')
        if m.get('PolicySetName') is not None:
            self.policy_set_name = m.get('PolicySetName')
        return self


class DetachPolicySetFromGatewayResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
    ):
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class DetachPolicySetFromGatewayResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: DetachPolicySetFromGatewayResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = DetachPolicySetFromGatewayResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class GetAPIKeyCredentialProviderRequest(TeaModel):
    def __init__(
        self,
        apikey_credential_provider_name: str = None,
        token_vault_name: str = None,
    ):
        self.apikey_credential_provider_name = apikey_credential_provider_name
        self.token_vault_name = token_vault_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.apikey_credential_provider_name is not None:
            result['APIKeyCredentialProviderName'] = self.apikey_credential_provider_name
        if self.token_vault_name is not None:
            result['TokenVaultName'] = self.token_vault_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('APIKeyCredentialProviderName') is not None:
            self.apikey_credential_provider_name = m.get('APIKeyCredentialProviderName')
        if m.get('TokenVaultName') is not None:
            self.token_vault_name = m.get('TokenVaultName')
        return self


class GetAPIKeyCredentialProviderResponseBodyAPIKeyCredentialProvider(TeaModel):
    def __init__(
        self,
        apikey_credential_provider_name: str = None,
        create_time: str = None,
        credential_provider_arn: str = None,
        description: str = None,
        token_vault_name: str = None,
        update_time: str = None,
    ):
        self.apikey_credential_provider_name = apikey_credential_provider_name
        self.create_time = create_time
        self.credential_provider_arn = credential_provider_arn
        self.description = description
        self.token_vault_name = token_vault_name
        self.update_time = update_time

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.apikey_credential_provider_name is not None:
            result['APIKeyCredentialProviderName'] = self.apikey_credential_provider_name
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.credential_provider_arn is not None:
            result['CredentialProviderArn'] = self.credential_provider_arn
        if self.description is not None:
            result['Description'] = self.description
        if self.token_vault_name is not None:
            result['TokenVaultName'] = self.token_vault_name
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('APIKeyCredentialProviderName') is not None:
            self.apikey_credential_provider_name = m.get('APIKeyCredentialProviderName')
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('CredentialProviderArn') is not None:
            self.credential_provider_arn = m.get('CredentialProviderArn')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('TokenVaultName') is not None:
            self.token_vault_name = m.get('TokenVaultName')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        return self


class GetAPIKeyCredentialProviderResponseBody(TeaModel):
    def __init__(
        self,
        apikey_credential_provider: GetAPIKeyCredentialProviderResponseBodyAPIKeyCredentialProvider = None,
        request_id: str = None,
    ):
        self.apikey_credential_provider = apikey_credential_provider
        self.request_id = request_id

    def validate(self):
        if self.apikey_credential_provider:
            self.apikey_credential_provider.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.apikey_credential_provider is not None:
            result['APIKeyCredentialProvider'] = self.apikey_credential_provider.to_map()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('APIKeyCredentialProvider') is not None:
            temp_model = GetAPIKeyCredentialProviderResponseBodyAPIKeyCredentialProvider()
            self.apikey_credential_provider = temp_model.from_map(m['APIKeyCredentialProvider'])
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class GetAPIKeyCredentialProviderResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: GetAPIKeyCredentialProviderResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = GetAPIKeyCredentialProviderResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class GetGatewayPolicyConfigRequest(TeaModel):
    def __init__(
        self,
        gateway_arn: str = None,
    ):
        self.gateway_arn = gateway_arn

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.gateway_arn is not None:
            result['GatewayArn'] = self.gateway_arn
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('GatewayArn') is not None:
            self.gateway_arn = m.get('GatewayArn')
        return self


class GetGatewayPolicyConfigResponseBodyGatewayPolicyConfig(TeaModel):
    def __init__(
        self,
        enforcement_mode: str = None,
        policy_set_arn: str = None,
    ):
        self.enforcement_mode = enforcement_mode
        self.policy_set_arn = policy_set_arn

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.enforcement_mode is not None:
            result['EnforcementMode'] = self.enforcement_mode
        if self.policy_set_arn is not None:
            result['PolicySetArn'] = self.policy_set_arn
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('EnforcementMode') is not None:
            self.enforcement_mode = m.get('EnforcementMode')
        if m.get('PolicySetArn') is not None:
            self.policy_set_arn = m.get('PolicySetArn')
        return self


class GetGatewayPolicyConfigResponseBody(TeaModel):
    def __init__(
        self,
        gateway_policy_config: GetGatewayPolicyConfigResponseBodyGatewayPolicyConfig = None,
        request_id: str = None,
    ):
        self.gateway_policy_config = gateway_policy_config
        self.request_id = request_id

    def validate(self):
        if self.gateway_policy_config:
            self.gateway_policy_config.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.gateway_policy_config is not None:
            result['GatewayPolicyConfig'] = self.gateway_policy_config.to_map()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('GatewayPolicyConfig') is not None:
            temp_model = GetGatewayPolicyConfigResponseBodyGatewayPolicyConfig()
            self.gateway_policy_config = temp_model.from_map(m['GatewayPolicyConfig'])
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class GetGatewayPolicyConfigResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: GetGatewayPolicyConfigResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = GetGatewayPolicyConfigResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class GetIdentityProviderRequest(TeaModel):
    def __init__(
        self,
        identity_provider_name: str = None,
    ):
        self.identity_provider_name = identity_provider_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.identity_provider_name is not None:
            result['IdentityProviderName'] = self.identity_provider_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('IdentityProviderName') is not None:
            self.identity_provider_name = m.get('IdentityProviderName')
        return self


class GetIdentityProviderResponseBodyIdentityProvider(TeaModel):
    def __init__(
        self,
        allowed_audience: List[str] = None,
        create_time: str = None,
        description: str = None,
        discovery_url: str = None,
        identity_provider_arn: str = None,
        identity_provider_name: str = None,
        update_time: str = None,
    ):
        self.allowed_audience = allowed_audience
        self.create_time = create_time
        self.description = description
        self.discovery_url = discovery_url
        self.identity_provider_arn = identity_provider_arn
        self.identity_provider_name = identity_provider_name
        self.update_time = update_time

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.allowed_audience is not None:
            result['AllowedAudience'] = self.allowed_audience
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.description is not None:
            result['Description'] = self.description
        if self.discovery_url is not None:
            result['DiscoveryURL'] = self.discovery_url
        if self.identity_provider_arn is not None:
            result['IdentityProviderArn'] = self.identity_provider_arn
        if self.identity_provider_name is not None:
            result['IdentityProviderName'] = self.identity_provider_name
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AllowedAudience') is not None:
            self.allowed_audience = m.get('AllowedAudience')
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('DiscoveryURL') is not None:
            self.discovery_url = m.get('DiscoveryURL')
        if m.get('IdentityProviderArn') is not None:
            self.identity_provider_arn = m.get('IdentityProviderArn')
        if m.get('IdentityProviderName') is not None:
            self.identity_provider_name = m.get('IdentityProviderName')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        return self


class GetIdentityProviderResponseBody(TeaModel):
    def __init__(
        self,
        identity_provider: GetIdentityProviderResponseBodyIdentityProvider = None,
        request_id: str = None,
    ):
        self.identity_provider = identity_provider
        self.request_id = request_id

    def validate(self):
        if self.identity_provider:
            self.identity_provider.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.identity_provider is not None:
            result['IdentityProvider'] = self.identity_provider.to_map()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('IdentityProvider') is not None:
            temp_model = GetIdentityProviderResponseBodyIdentityProvider()
            self.identity_provider = temp_model.from_map(m['IdentityProvider'])
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class GetIdentityProviderResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: GetIdentityProviderResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = GetIdentityProviderResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class GetOAuth2CredentialProviderRequest(TeaModel):
    def __init__(
        self,
        oauth_2credential_provider_name: str = None,
        token_vault_name: str = None,
    ):
        self.oauth_2credential_provider_name = oauth_2credential_provider_name
        self.token_vault_name = token_vault_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.oauth_2credential_provider_name is not None:
            result['OAuth2CredentialProviderName'] = self.oauth_2credential_provider_name
        if self.token_vault_name is not None:
            result['TokenVaultName'] = self.token_vault_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('OAuth2CredentialProviderName') is not None:
            self.oauth_2credential_provider_name = m.get('OAuth2CredentialProviderName')
        if m.get('TokenVaultName') is not None:
            self.token_vault_name = m.get('TokenVaultName')
        return self


class GetOAuth2CredentialProviderResponseBodyOAuth2CredentialProvider(TeaModel):
    def __init__(
        self,
        callback_url: str = None,
        create_time: str = None,
        credential_provider_arn: str = None,
        credential_provider_vendor: str = None,
        description: str = None,
        oauth_2credential_provider_name: str = None,
        oauth_2provider_config: OAuth2ProviderConfig = None,
        token_vault_name: str = None,
        update_time: str = None,
    ):
        self.callback_url = callback_url
        self.create_time = create_time
        self.credential_provider_arn = credential_provider_arn
        self.credential_provider_vendor = credential_provider_vendor
        self.description = description
        self.oauth_2credential_provider_name = oauth_2credential_provider_name
        self.oauth_2provider_config = oauth_2provider_config
        self.token_vault_name = token_vault_name
        self.update_time = update_time

    def validate(self):
        if self.oauth_2provider_config:
            self.oauth_2provider_config.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.callback_url is not None:
            result['CallbackURL'] = self.callback_url
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.credential_provider_arn is not None:
            result['CredentialProviderArn'] = self.credential_provider_arn
        if self.credential_provider_vendor is not None:
            result['CredentialProviderVendor'] = self.credential_provider_vendor
        if self.description is not None:
            result['Description'] = self.description
        if self.oauth_2credential_provider_name is not None:
            result['OAuth2CredentialProviderName'] = self.oauth_2credential_provider_name
        if self.oauth_2provider_config is not None:
            result['OAuth2ProviderConfig'] = self.oauth_2provider_config.to_map()
        if self.token_vault_name is not None:
            result['TokenVaultName'] = self.token_vault_name
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CallbackURL') is not None:
            self.callback_url = m.get('CallbackURL')
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('CredentialProviderArn') is not None:
            self.credential_provider_arn = m.get('CredentialProviderArn')
        if m.get('CredentialProviderVendor') is not None:
            self.credential_provider_vendor = m.get('CredentialProviderVendor')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('OAuth2CredentialProviderName') is not None:
            self.oauth_2credential_provider_name = m.get('OAuth2CredentialProviderName')
        if m.get('OAuth2ProviderConfig') is not None:
            temp_model = OAuth2ProviderConfig()
            self.oauth_2provider_config = temp_model.from_map(m['OAuth2ProviderConfig'])
        if m.get('TokenVaultName') is not None:
            self.token_vault_name = m.get('TokenVaultName')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        return self


class GetOAuth2CredentialProviderResponseBody(TeaModel):
    def __init__(
        self,
        oauth_2credential_provider: GetOAuth2CredentialProviderResponseBodyOAuth2CredentialProvider = None,
        request_id: str = None,
    ):
        self.oauth_2credential_provider = oauth_2credential_provider
        self.request_id = request_id

    def validate(self):
        if self.oauth_2credential_provider:
            self.oauth_2credential_provider.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.oauth_2credential_provider is not None:
            result['OAuth2CredentialProvider'] = self.oauth_2credential_provider.to_map()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('OAuth2CredentialProvider') is not None:
            temp_model = GetOAuth2CredentialProviderResponseBodyOAuth2CredentialProvider()
            self.oauth_2credential_provider = temp_model.from_map(m['OAuth2CredentialProvider'])
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class GetOAuth2CredentialProviderResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: GetOAuth2CredentialProviderResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = GetOAuth2CredentialProviderResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class GetPolicyRequest(TeaModel):
    def __init__(
        self,
        policy_name: str = None,
        policy_set_name: str = None,
    ):
        self.policy_name = policy_name
        self.policy_set_name = policy_set_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.policy_name is not None:
            result['PolicyName'] = self.policy_name
        if self.policy_set_name is not None:
            result['PolicySetName'] = self.policy_set_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('PolicyName') is not None:
            self.policy_name = m.get('PolicyName')
        if m.get('PolicySetName') is not None:
            self.policy_set_name = m.get('PolicySetName')
        return self


class GetPolicyResponseBodyPolicy(TeaModel):
    def __init__(
        self,
        create_time: str = None,
        definition: Definition = None,
        description: str = None,
        policy_arn: str = None,
        policy_name: str = None,
        policy_set_name: str = None,
        update_time: str = None,
    ):
        self.create_time = create_time
        self.definition = definition
        self.description = description
        self.policy_arn = policy_arn
        self.policy_name = policy_name
        self.policy_set_name = policy_set_name
        self.update_time = update_time

    def validate(self):
        if self.definition:
            self.definition.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.definition is not None:
            result['Definition'] = self.definition.to_map()
        if self.description is not None:
            result['Description'] = self.description
        if self.policy_arn is not None:
            result['PolicyArn'] = self.policy_arn
        if self.policy_name is not None:
            result['PolicyName'] = self.policy_name
        if self.policy_set_name is not None:
            result['PolicySetName'] = self.policy_set_name
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('Definition') is not None:
            temp_model = Definition()
            self.definition = temp_model.from_map(m['Definition'])
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('PolicyArn') is not None:
            self.policy_arn = m.get('PolicyArn')
        if m.get('PolicyName') is not None:
            self.policy_name = m.get('PolicyName')
        if m.get('PolicySetName') is not None:
            self.policy_set_name = m.get('PolicySetName')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        return self


class GetPolicyResponseBody(TeaModel):
    def __init__(
        self,
        policy: GetPolicyResponseBodyPolicy = None,
        request_id: str = None,
    ):
        self.policy = policy
        self.request_id = request_id

    def validate(self):
        if self.policy:
            self.policy.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.policy is not None:
            result['Policy'] = self.policy.to_map()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Policy') is not None:
            temp_model = GetPolicyResponseBodyPolicy()
            self.policy = temp_model.from_map(m['Policy'])
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class GetPolicyResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: GetPolicyResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = GetPolicyResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class GetPolicySetRequest(TeaModel):
    def __init__(
        self,
        policy_set_name: str = None,
    ):
        self.policy_set_name = policy_set_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.policy_set_name is not None:
            result['PolicySetName'] = self.policy_set_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('PolicySetName') is not None:
            self.policy_set_name = m.get('PolicySetName')
        return self


class GetPolicySetResponseBodyPolicySet(TeaModel):
    def __init__(
        self,
        create_time: str = None,
        description: str = None,
        policy_set_arn: str = None,
        policy_set_name: str = None,
        update_time: str = None,
    ):
        self.create_time = create_time
        self.description = description
        self.policy_set_arn = policy_set_arn
        self.policy_set_name = policy_set_name
        self.update_time = update_time

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.description is not None:
            result['Description'] = self.description
        if self.policy_set_arn is not None:
            result['PolicySetArn'] = self.policy_set_arn
        if self.policy_set_name is not None:
            result['PolicySetName'] = self.policy_set_name
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('PolicySetArn') is not None:
            self.policy_set_arn = m.get('PolicySetArn')
        if m.get('PolicySetName') is not None:
            self.policy_set_name = m.get('PolicySetName')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        return self


class GetPolicySetResponseBody(TeaModel):
    def __init__(
        self,
        policy_set: GetPolicySetResponseBodyPolicySet = None,
        request_id: str = None,
    ):
        self.policy_set = policy_set
        self.request_id = request_id

    def validate(self):
        if self.policy_set:
            self.policy_set.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.policy_set is not None:
            result['PolicySet'] = self.policy_set.to_map()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('PolicySet') is not None:
            temp_model = GetPolicySetResponseBodyPolicySet()
            self.policy_set = temp_model.from_map(m['PolicySet'])
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class GetPolicySetResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: GetPolicySetResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = GetPolicySetResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class GetRoleRequest(TeaModel):
    def __init__(
        self,
        role_name: str = None,
        user_pool_name: str = None,
    ):
        self.role_name = role_name
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.role_name is not None:
            result['RoleName'] = self.role_name
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RoleName') is not None:
            self.role_name = m.get('RoleName')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class GetRoleResponseBodyRole(TeaModel):
    def __init__(
        self,
        create_time: str = None,
        description: str = None,
        role_id: str = None,
        role_name: str = None,
        type: str = None,
        update_time: str = None,
    ):
        self.create_time = create_time
        self.description = description
        self.role_id = role_id
        self.role_name = role_name
        self.type = type
        self.update_time = update_time

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.description is not None:
            result['Description'] = self.description
        if self.role_id is not None:
            result['RoleId'] = self.role_id
        if self.role_name is not None:
            result['RoleName'] = self.role_name
        if self.type is not None:
            result['Type'] = self.type
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('RoleId') is not None:
            self.role_id = m.get('RoleId')
        if m.get('RoleName') is not None:
            self.role_name = m.get('RoleName')
        if m.get('Type') is not None:
            self.type = m.get('Type')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        return self


class GetRoleResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
        role: GetRoleResponseBodyRole = None,
    ):
        self.request_id = request_id
        self.role = role

    def validate(self):
        if self.role:
            self.role.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.role is not None:
            result['Role'] = self.role.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('Role') is not None:
            temp_model = GetRoleResponseBodyRole()
            self.role = temp_model.from_map(m['Role'])
        return self


class GetRoleResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: GetRoleResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = GetRoleResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class GetSAMLIdentityProviderRequest(TeaModel):
    def __init__(
        self,
        user_pool_name: str = None,
    ):
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class GetSAMLIdentityProviderResponseBodySSOIdentityProviderConfigurationX509Certificates(TeaModel):
    def __init__(
        self,
        certificate_id: str = None,
        x_509certificate: str = None,
    ):
        self.certificate_id = certificate_id
        self.x_509certificate = x_509certificate

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.certificate_id is not None:
            result['CertificateId'] = self.certificate_id
        if self.x_509certificate is not None:
            result['X509Certificate'] = self.x_509certificate
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CertificateId') is not None:
            self.certificate_id = m.get('CertificateId')
        if m.get('X509Certificate') is not None:
            self.x_509certificate = m.get('X509Certificate')
        return self


class GetSAMLIdentityProviderResponseBodySSOIdentityProviderConfiguration(TeaModel):
    def __init__(
        self,
        entity_id: str = None,
        jitprovision_status: str = None,
        jitupdate_status: str = None,
        login_url: str = None,
        samlbinding_type: str = None,
        ssostatus: str = None,
        x_509certificates: List[GetSAMLIdentityProviderResponseBodySSOIdentityProviderConfigurationX509Certificates] = None,
    ):
        self.entity_id = entity_id
        self.jitprovision_status = jitprovision_status
        self.jitupdate_status = jitupdate_status
        self.login_url = login_url
        self.samlbinding_type = samlbinding_type
        self.ssostatus = ssostatus
        self.x_509certificates = x_509certificates

    def validate(self):
        if self.x_509certificates:
            for k in self.x_509certificates:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.entity_id is not None:
            result['EntityId'] = self.entity_id
        if self.jitprovision_status is not None:
            result['JITProvisionStatus'] = self.jitprovision_status
        if self.jitupdate_status is not None:
            result['JITUpdateStatus'] = self.jitupdate_status
        if self.login_url is not None:
            result['LoginUrl'] = self.login_url
        if self.samlbinding_type is not None:
            result['SAMLBindingType'] = self.samlbinding_type
        if self.ssostatus is not None:
            result['SSOStatus'] = self.ssostatus
        result['X509Certificates'] = []
        if self.x_509certificates is not None:
            for k in self.x_509certificates:
                result['X509Certificates'].append(k.to_map() if k else None)
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('EntityId') is not None:
            self.entity_id = m.get('EntityId')
        if m.get('JITProvisionStatus') is not None:
            self.jitprovision_status = m.get('JITProvisionStatus')
        if m.get('JITUpdateStatus') is not None:
            self.jitupdate_status = m.get('JITUpdateStatus')
        if m.get('LoginUrl') is not None:
            self.login_url = m.get('LoginUrl')
        if m.get('SAMLBindingType') is not None:
            self.samlbinding_type = m.get('SAMLBindingType')
        if m.get('SSOStatus') is not None:
            self.ssostatus = m.get('SSOStatus')
        self.x_509certificates = []
        if m.get('X509Certificates') is not None:
            for k in m.get('X509Certificates'):
                temp_model = GetSAMLIdentityProviderResponseBodySSOIdentityProviderConfigurationX509Certificates()
                self.x_509certificates.append(temp_model.from_map(k))
        return self


class GetSAMLIdentityProviderResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
        ssoidentity_provider_configuration: GetSAMLIdentityProviderResponseBodySSOIdentityProviderConfiguration = None,
    ):
        self.request_id = request_id
        self.ssoidentity_provider_configuration = ssoidentity_provider_configuration

    def validate(self):
        if self.ssoidentity_provider_configuration:
            self.ssoidentity_provider_configuration.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.ssoidentity_provider_configuration is not None:
            result['SSOIdentityProviderConfiguration'] = self.ssoidentity_provider_configuration.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('SSOIdentityProviderConfiguration') is not None:
            temp_model = GetSAMLIdentityProviderResponseBodySSOIdentityProviderConfiguration()
            self.ssoidentity_provider_configuration = temp_model.from_map(m['SSOIdentityProviderConfiguration'])
        return self


class GetSAMLIdentityProviderResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: GetSAMLIdentityProviderResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = GetSAMLIdentityProviderResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class GetSAMLServiceProviderInfoRequest(TeaModel):
    def __init__(
        self,
        user_pool_name: str = None,
    ):
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class GetSAMLServiceProviderInfoResponseBodySAMLServiceProviderInfo(TeaModel):
    def __init__(
        self,
        acsurl: str = None,
        entity_id: str = None,
        spmetadata_document: str = None,
        user_pool_id: str = None,
    ):
        self.acsurl = acsurl
        self.entity_id = entity_id
        self.spmetadata_document = spmetadata_document
        self.user_pool_id = user_pool_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.acsurl is not None:
            result['ACSUrl'] = self.acsurl
        if self.entity_id is not None:
            result['EntityId'] = self.entity_id
        if self.spmetadata_document is not None:
            result['SPMetadataDocument'] = self.spmetadata_document
        if self.user_pool_id is not None:
            result['UserPoolId'] = self.user_pool_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('ACSUrl') is not None:
            self.acsurl = m.get('ACSUrl')
        if m.get('EntityId') is not None:
            self.entity_id = m.get('EntityId')
        if m.get('SPMetadataDocument') is not None:
            self.spmetadata_document = m.get('SPMetadataDocument')
        if m.get('UserPoolId') is not None:
            self.user_pool_id = m.get('UserPoolId')
        return self


class GetSAMLServiceProviderInfoResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
        samlservice_provider_info: GetSAMLServiceProviderInfoResponseBodySAMLServiceProviderInfo = None,
    ):
        self.request_id = request_id
        self.samlservice_provider_info = samlservice_provider_info

    def validate(self):
        if self.samlservice_provider_info:
            self.samlservice_provider_info.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.samlservice_provider_info is not None:
            result['SAMLServiceProviderInfo'] = self.samlservice_provider_info.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('SAMLServiceProviderInfo') is not None:
            temp_model = GetSAMLServiceProviderInfoResponseBodySAMLServiceProviderInfo()
            self.samlservice_provider_info = temp_model.from_map(m['SAMLServiceProviderInfo'])
        return self


class GetSAMLServiceProviderInfoResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: GetSAMLServiceProviderInfoResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = GetSAMLServiceProviderInfoResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class GetTokenVaultRequest(TeaModel):
    def __init__(
        self,
        token_vault_name: str = None,
    ):
        self.token_vault_name = token_vault_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.token_vault_name is not None:
            result['TokenVaultName'] = self.token_vault_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('TokenVaultName') is not None:
            self.token_vault_name = m.get('TokenVaultName')
        return self


class GetTokenVaultResponseBodyTokenVaultEncryptionConfig(TeaModel):
    def __init__(
        self,
        key_type: str = None,
        kms_key_arn: str = None,
    ):
        self.key_type = key_type
        self.kms_key_arn = kms_key_arn

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.key_type is not None:
            result['KeyType'] = self.key_type
        if self.kms_key_arn is not None:
            result['KmsKeyArn'] = self.kms_key_arn
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('KeyType') is not None:
            self.key_type = m.get('KeyType')
        if m.get('KmsKeyArn') is not None:
            self.kms_key_arn = m.get('KmsKeyArn')
        return self


class GetTokenVaultResponseBodyTokenVault(TeaModel):
    def __init__(
        self,
        create_time: str = None,
        description: str = None,
        encryption_config: GetTokenVaultResponseBodyTokenVaultEncryptionConfig = None,
        role_arn: str = None,
        token_vault_arn: str = None,
        token_vault_name: str = None,
        update_time: str = None,
    ):
        self.create_time = create_time
        self.description = description
        self.encryption_config = encryption_config
        self.role_arn = role_arn
        self.token_vault_arn = token_vault_arn
        self.token_vault_name = token_vault_name
        self.update_time = update_time

    def validate(self):
        if self.encryption_config:
            self.encryption_config.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.description is not None:
            result['Description'] = self.description
        if self.encryption_config is not None:
            result['EncryptionConfig'] = self.encryption_config.to_map()
        if self.role_arn is not None:
            result['RoleArn'] = self.role_arn
        if self.token_vault_arn is not None:
            result['TokenVaultArn'] = self.token_vault_arn
        if self.token_vault_name is not None:
            result['TokenVaultName'] = self.token_vault_name
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('EncryptionConfig') is not None:
            temp_model = GetTokenVaultResponseBodyTokenVaultEncryptionConfig()
            self.encryption_config = temp_model.from_map(m['EncryptionConfig'])
        if m.get('RoleArn') is not None:
            self.role_arn = m.get('RoleArn')
        if m.get('TokenVaultArn') is not None:
            self.token_vault_arn = m.get('TokenVaultArn')
        if m.get('TokenVaultName') is not None:
            self.token_vault_name = m.get('TokenVaultName')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        return self


class GetTokenVaultResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
        token_vault: GetTokenVaultResponseBodyTokenVault = None,
    ):
        self.request_id = request_id
        self.token_vault = token_vault

    def validate(self):
        if self.token_vault:
            self.token_vault.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.token_vault is not None:
            result['TokenVault'] = self.token_vault.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('TokenVault') is not None:
            temp_model = GetTokenVaultResponseBodyTokenVault()
            self.token_vault = temp_model.from_map(m['TokenVault'])
        return self


class GetTokenVaultResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: GetTokenVaultResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = GetTokenVaultResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class GetUserRequest(TeaModel):
    def __init__(
        self,
        user_name: str = None,
        user_pool_name: str = None,
    ):
        self.user_name = user_name
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.user_name is not None:
            result['UserName'] = self.user_name
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('UserName') is not None:
            self.user_name = m.get('UserName')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class GetUserResponseBodyUser(TeaModel):
    def __init__(
        self,
        create_time: str = None,
        description: str = None,
        display_name: str = None,
        update_time: str = None,
        user_id: str = None,
        user_name: str = None,
    ):
        self.create_time = create_time
        self.description = description
        self.display_name = display_name
        self.update_time = update_time
        self.user_id = user_id
        self.user_name = user_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.description is not None:
            result['Description'] = self.description
        if self.display_name is not None:
            result['DisplayName'] = self.display_name
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        if self.user_id is not None:
            result['UserId'] = self.user_id
        if self.user_name is not None:
            result['UserName'] = self.user_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('DisplayName') is not None:
            self.display_name = m.get('DisplayName')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        if m.get('UserId') is not None:
            self.user_id = m.get('UserId')
        if m.get('UserName') is not None:
            self.user_name = m.get('UserName')
        return self


class GetUserResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
        user: GetUserResponseBodyUser = None,
    ):
        self.request_id = request_id
        self.user = user

    def validate(self):
        if self.user:
            self.user.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.user is not None:
            result['User'] = self.user.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('User') is not None:
            temp_model = GetUserResponseBodyUser()
            self.user = temp_model.from_map(m['User'])
        return self


class GetUserResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: GetUserResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = GetUserResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class GetUserPoolRequest(TeaModel):
    def __init__(
        self,
        user_pool_name: str = None,
    ):
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class GetUserPoolResponseBodyUserPool(TeaModel):
    def __init__(
        self,
        create_time: str = None,
        description: str = None,
        update_time: str = None,
        user_pool_arn: str = None,
        user_pool_id: str = None,
        user_pool_name: str = None,
    ):
        self.create_time = create_time
        self.description = description
        self.update_time = update_time
        self.user_pool_arn = user_pool_arn
        self.user_pool_id = user_pool_id
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.description is not None:
            result['Description'] = self.description
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        if self.user_pool_arn is not None:
            result['UserPoolArn'] = self.user_pool_arn
        if self.user_pool_id is not None:
            result['UserPoolId'] = self.user_pool_id
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        if m.get('UserPoolArn') is not None:
            self.user_pool_arn = m.get('UserPoolArn')
        if m.get('UserPoolId') is not None:
            self.user_pool_id = m.get('UserPoolId')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class GetUserPoolResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
        user_pool: GetUserPoolResponseBodyUserPool = None,
    ):
        self.request_id = request_id
        self.user_pool = user_pool

    def validate(self):
        if self.user_pool:
            self.user_pool.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.user_pool is not None:
            result['UserPool'] = self.user_pool.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('UserPool') is not None:
            temp_model = GetUserPoolResponseBodyUserPool()
            self.user_pool = temp_model.from_map(m['UserPool'])
        return self


class GetUserPoolResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: GetUserPoolResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = GetUserPoolResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class GetUserPoolClientRequest(TeaModel):
    def __init__(
        self,
        client_name: str = None,
        user_pool_name: str = None,
    ):
        self.client_name = client_name
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.client_name is not None:
            result['ClientName'] = self.client_name
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('ClientName') is not None:
            self.client_name = m.get('ClientName')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class GetUserPoolClientResponseBodyClientClientScopes(TeaModel):
    def __init__(
        self,
        description: str = None,
        scope_name: str = None,
    ):
        self.description = description
        self.scope_name = scope_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.description is not None:
            result['Description'] = self.description
        if self.scope_name is not None:
            result['ScopeName'] = self.scope_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('ScopeName') is not None:
            self.scope_name = m.get('ScopeName')
        return self


class GetUserPoolClientResponseBodyClient(TeaModel):
    def __init__(
        self,
        access_token_validity: str = None,
        client_id: str = None,
        client_name: str = None,
        client_scopes: List[GetUserPoolClientResponseBodyClientClientScopes] = None,
        create_time: str = None,
        enforce_pkce: bool = None,
        redirect_uris: List[str] = None,
        refresh_token_validity: str = None,
        secret_required: bool = None,
        update_time: str = None,
        user_pool_name: str = None,
    ):
        self.access_token_validity = access_token_validity
        self.client_id = client_id
        self.client_name = client_name
        self.client_scopes = client_scopes
        self.create_time = create_time
        self.enforce_pkce = enforce_pkce
        self.redirect_uris = redirect_uris
        self.refresh_token_validity = refresh_token_validity
        self.secret_required = secret_required
        self.update_time = update_time
        self.user_pool_name = user_pool_name

    def validate(self):
        if self.client_scopes:
            for k in self.client_scopes:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.access_token_validity is not None:
            result['AccessTokenValidity'] = self.access_token_validity
        if self.client_id is not None:
            result['ClientId'] = self.client_id
        if self.client_name is not None:
            result['ClientName'] = self.client_name
        result['ClientScopes'] = []
        if self.client_scopes is not None:
            for k in self.client_scopes:
                result['ClientScopes'].append(k.to_map() if k else None)
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.enforce_pkce is not None:
            result['EnforcePKCE'] = self.enforce_pkce
        if self.redirect_uris is not None:
            result['RedirectURIs'] = self.redirect_uris
        if self.refresh_token_validity is not None:
            result['RefreshTokenValidity'] = self.refresh_token_validity
        if self.secret_required is not None:
            result['SecretRequired'] = self.secret_required
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AccessTokenValidity') is not None:
            self.access_token_validity = m.get('AccessTokenValidity')
        if m.get('ClientId') is not None:
            self.client_id = m.get('ClientId')
        if m.get('ClientName') is not None:
            self.client_name = m.get('ClientName')
        self.client_scopes = []
        if m.get('ClientScopes') is not None:
            for k in m.get('ClientScopes'):
                temp_model = GetUserPoolClientResponseBodyClientClientScopes()
                self.client_scopes.append(temp_model.from_map(k))
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('EnforcePKCE') is not None:
            self.enforce_pkce = m.get('EnforcePKCE')
        if m.get('RedirectURIs') is not None:
            self.redirect_uris = m.get('RedirectURIs')
        if m.get('RefreshTokenValidity') is not None:
            self.refresh_token_validity = m.get('RefreshTokenValidity')
        if m.get('SecretRequired') is not None:
            self.secret_required = m.get('SecretRequired')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class GetUserPoolClientResponseBody(TeaModel):
    def __init__(
        self,
        client: GetUserPoolClientResponseBodyClient = None,
        request_id: str = None,
    ):
        self.client = client
        self.request_id = request_id

    def validate(self):
        if self.client:
            self.client.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.client is not None:
            result['Client'] = self.client.to_map()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Client') is not None:
            temp_model = GetUserPoolClientResponseBodyClient()
            self.client = temp_model.from_map(m['Client'])
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class GetUserPoolClientResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: GetUserPoolClientResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = GetUserPoolClientResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class GetWorkloadIdentityRequest(TeaModel):
    def __init__(
        self,
        workload_identity_name: str = None,
    ):
        self.workload_identity_name = workload_identity_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.workload_identity_name is not None:
            result['WorkloadIdentityName'] = self.workload_identity_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('WorkloadIdentityName') is not None:
            self.workload_identity_name = m.get('WorkloadIdentityName')
        return self


class GetWorkloadIdentityResponseBodyWorkloadIdentity(TeaModel):
    def __init__(
        self,
        allowed_resource_oauth_2return_urls: List[str] = None,
        create_time: str = None,
        description: str = None,
        identity_provider_name: str = None,
        role_arn: str = None,
        update_time: str = None,
        workload_identity_arn: str = None,
        workload_identity_name: str = None,
    ):
        self.allowed_resource_oauth_2return_urls = allowed_resource_oauth_2return_urls
        self.create_time = create_time
        self.description = description
        self.identity_provider_name = identity_provider_name
        self.role_arn = role_arn
        self.update_time = update_time
        self.workload_identity_arn = workload_identity_arn
        self.workload_identity_name = workload_identity_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.allowed_resource_oauth_2return_urls is not None:
            result['AllowedResourceOAuth2ReturnURLs'] = self.allowed_resource_oauth_2return_urls
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.description is not None:
            result['Description'] = self.description
        if self.identity_provider_name is not None:
            result['IdentityProviderName'] = self.identity_provider_name
        if self.role_arn is not None:
            result['RoleArn'] = self.role_arn
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        if self.workload_identity_arn is not None:
            result['WorkloadIdentityArn'] = self.workload_identity_arn
        if self.workload_identity_name is not None:
            result['WorkloadIdentityName'] = self.workload_identity_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AllowedResourceOAuth2ReturnURLs') is not None:
            self.allowed_resource_oauth_2return_urls = m.get('AllowedResourceOAuth2ReturnURLs')
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('IdentityProviderName') is not None:
            self.identity_provider_name = m.get('IdentityProviderName')
        if m.get('RoleArn') is not None:
            self.role_arn = m.get('RoleArn')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        if m.get('WorkloadIdentityArn') is not None:
            self.workload_identity_arn = m.get('WorkloadIdentityArn')
        if m.get('WorkloadIdentityName') is not None:
            self.workload_identity_name = m.get('WorkloadIdentityName')
        return self


class GetWorkloadIdentityResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
        workload_identity: GetWorkloadIdentityResponseBodyWorkloadIdentity = None,
    ):
        self.request_id = request_id
        self.workload_identity = workload_identity

    def validate(self):
        if self.workload_identity:
            self.workload_identity.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.workload_identity is not None:
            result['WorkloadIdentity'] = self.workload_identity.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('WorkloadIdentity') is not None:
            temp_model = GetWorkloadIdentityResponseBodyWorkloadIdentity()
            self.workload_identity = temp_model.from_map(m['WorkloadIdentity'])
        return self


class GetWorkloadIdentityResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: GetWorkloadIdentityResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = GetWorkloadIdentityResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class ListAPIKeyCredentialProvidersRequest(TeaModel):
    def __init__(
        self,
        max_results: int = None,
        next_token: str = None,
        token_vault_name: str = None,
    ):
        self.max_results = max_results
        self.next_token = next_token
        self.token_vault_name = token_vault_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.max_results is not None:
            result['MaxResults'] = self.max_results
        if self.next_token is not None:
            result['NextToken'] = self.next_token
        if self.token_vault_name is not None:
            result['TokenVaultName'] = self.token_vault_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('MaxResults') is not None:
            self.max_results = m.get('MaxResults')
        if m.get('NextToken') is not None:
            self.next_token = m.get('NextToken')
        if m.get('TokenVaultName') is not None:
            self.token_vault_name = m.get('TokenVaultName')
        return self


class ListAPIKeyCredentialProvidersResponseBodyAPIKeyCredentialProviders(TeaModel):
    def __init__(
        self,
        apikey_credential_provider_name: str = None,
        create_time: str = None,
        credential_provider_arn: str = None,
        description: str = None,
        token_vault_name: str = None,
        update_time: str = None,
    ):
        self.apikey_credential_provider_name = apikey_credential_provider_name
        self.create_time = create_time
        self.credential_provider_arn = credential_provider_arn
        self.description = description
        self.token_vault_name = token_vault_name
        self.update_time = update_time

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.apikey_credential_provider_name is not None:
            result['APIKeyCredentialProviderName'] = self.apikey_credential_provider_name
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.credential_provider_arn is not None:
            result['CredentialProviderArn'] = self.credential_provider_arn
        if self.description is not None:
            result['Description'] = self.description
        if self.token_vault_name is not None:
            result['TokenVaultName'] = self.token_vault_name
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('APIKeyCredentialProviderName') is not None:
            self.apikey_credential_provider_name = m.get('APIKeyCredentialProviderName')
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('CredentialProviderArn') is not None:
            self.credential_provider_arn = m.get('CredentialProviderArn')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('TokenVaultName') is not None:
            self.token_vault_name = m.get('TokenVaultName')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        return self


class ListAPIKeyCredentialProvidersResponseBody(TeaModel):
    def __init__(
        self,
        apikey_credential_providers: List[ListAPIKeyCredentialProvidersResponseBodyAPIKeyCredentialProviders] = None,
        max_results: int = None,
        next_token: str = None,
        request_id: str = None,
        total_count: int = None,
    ):
        self.apikey_credential_providers = apikey_credential_providers
        self.max_results = max_results
        self.next_token = next_token
        self.request_id = request_id
        self.total_count = total_count

    def validate(self):
        if self.apikey_credential_providers:
            for k in self.apikey_credential_providers:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        result['APIKeyCredentialProviders'] = []
        if self.apikey_credential_providers is not None:
            for k in self.apikey_credential_providers:
                result['APIKeyCredentialProviders'].append(k.to_map() if k else None)
        if self.max_results is not None:
            result['MaxResults'] = self.max_results
        if self.next_token is not None:
            result['NextToken'] = self.next_token
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.total_count is not None:
            result['TotalCount'] = self.total_count
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        self.apikey_credential_providers = []
        if m.get('APIKeyCredentialProviders') is not None:
            for k in m.get('APIKeyCredentialProviders'):
                temp_model = ListAPIKeyCredentialProvidersResponseBodyAPIKeyCredentialProviders()
                self.apikey_credential_providers.append(temp_model.from_map(k))
        if m.get('MaxResults') is not None:
            self.max_results = m.get('MaxResults')
        if m.get('NextToken') is not None:
            self.next_token = m.get('NextToken')
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('TotalCount') is not None:
            self.total_count = m.get('TotalCount')
        return self


class ListAPIKeyCredentialProvidersResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: ListAPIKeyCredentialProvidersResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = ListAPIKeyCredentialProvidersResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class ListClientSecretsRequest(TeaModel):
    def __init__(
        self,
        client_name: str = None,
        user_pool_name: str = None,
    ):
        self.client_name = client_name
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.client_name is not None:
            result['ClientName'] = self.client_name
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('ClientName') is not None:
            self.client_name = m.get('ClientName')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class ListClientSecretsResponseBodyClientSecrets(TeaModel):
    def __init__(
        self,
        client_secret_id: str = None,
        create_time: str = None,
    ):
        self.client_secret_id = client_secret_id
        self.create_time = create_time

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.client_secret_id is not None:
            result['ClientSecretId'] = self.client_secret_id
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('ClientSecretId') is not None:
            self.client_secret_id = m.get('ClientSecretId')
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        return self


class ListClientSecretsResponseBody(TeaModel):
    def __init__(
        self,
        client_id: str = None,
        client_secrets: List[ListClientSecretsResponseBodyClientSecrets] = None,
        request_id: str = None,
        user_pool_name: str = None,
    ):
        self.client_id = client_id
        self.client_secrets = client_secrets
        self.request_id = request_id
        self.user_pool_name = user_pool_name

    def validate(self):
        if self.client_secrets:
            for k in self.client_secrets:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.client_id is not None:
            result['ClientId'] = self.client_id
        result['ClientSecrets'] = []
        if self.client_secrets is not None:
            for k in self.client_secrets:
                result['ClientSecrets'].append(k.to_map() if k else None)
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('ClientId') is not None:
            self.client_id = m.get('ClientId')
        self.client_secrets = []
        if m.get('ClientSecrets') is not None:
            for k in m.get('ClientSecrets'):
                temp_model = ListClientSecretsResponseBodyClientSecrets()
                self.client_secrets.append(temp_model.from_map(k))
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class ListClientSecretsResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: ListClientSecretsResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = ListClientSecretsResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class ListIdentityProvidersRequest(TeaModel):
    def __init__(
        self,
        max_results: int = None,
        next_token: str = None,
    ):
        self.max_results = max_results
        self.next_token = next_token

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.max_results is not None:
            result['MaxResults'] = self.max_results
        if self.next_token is not None:
            result['NextToken'] = self.next_token
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('MaxResults') is not None:
            self.max_results = m.get('MaxResults')
        if m.get('NextToken') is not None:
            self.next_token = m.get('NextToken')
        return self


class ListIdentityProvidersResponseBodyIdentityProviders(TeaModel):
    def __init__(
        self,
        allowed_audience: List[str] = None,
        create_time: str = None,
        description: str = None,
        discovery_url: str = None,
        identity_provider_arn: str = None,
        identity_provider_name: str = None,
        update_time: str = None,
    ):
        self.allowed_audience = allowed_audience
        self.create_time = create_time
        self.description = description
        self.discovery_url = discovery_url
        self.identity_provider_arn = identity_provider_arn
        self.identity_provider_name = identity_provider_name
        self.update_time = update_time

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.allowed_audience is not None:
            result['AllowedAudience'] = self.allowed_audience
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.description is not None:
            result['Description'] = self.description
        if self.discovery_url is not None:
            result['DiscoveryURL'] = self.discovery_url
        if self.identity_provider_arn is not None:
            result['IdentityProviderArn'] = self.identity_provider_arn
        if self.identity_provider_name is not None:
            result['IdentityProviderName'] = self.identity_provider_name
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AllowedAudience') is not None:
            self.allowed_audience = m.get('AllowedAudience')
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('DiscoveryURL') is not None:
            self.discovery_url = m.get('DiscoveryURL')
        if m.get('IdentityProviderArn') is not None:
            self.identity_provider_arn = m.get('IdentityProviderArn')
        if m.get('IdentityProviderName') is not None:
            self.identity_provider_name = m.get('IdentityProviderName')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        return self


class ListIdentityProvidersResponseBody(TeaModel):
    def __init__(
        self,
        identity_providers: List[ListIdentityProvidersResponseBodyIdentityProviders] = None,
        max_results: int = None,
        next_token: str = None,
        request_id: str = None,
        total_count: int = None,
    ):
        self.identity_providers = identity_providers
        self.max_results = max_results
        self.next_token = next_token
        self.request_id = request_id
        self.total_count = total_count

    def validate(self):
        if self.identity_providers:
            for k in self.identity_providers:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        result['IdentityProviders'] = []
        if self.identity_providers is not None:
            for k in self.identity_providers:
                result['IdentityProviders'].append(k.to_map() if k else None)
        if self.max_results is not None:
            result['MaxResults'] = self.max_results
        if self.next_token is not None:
            result['NextToken'] = self.next_token
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.total_count is not None:
            result['TotalCount'] = self.total_count
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        self.identity_providers = []
        if m.get('IdentityProviders') is not None:
            for k in m.get('IdentityProviders'):
                temp_model = ListIdentityProvidersResponseBodyIdentityProviders()
                self.identity_providers.append(temp_model.from_map(k))
        if m.get('MaxResults') is not None:
            self.max_results = m.get('MaxResults')
        if m.get('NextToken') is not None:
            self.next_token = m.get('NextToken')
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('TotalCount') is not None:
            self.total_count = m.get('TotalCount')
        return self


class ListIdentityProvidersResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: ListIdentityProvidersResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = ListIdentityProvidersResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class ListOAuth2CredentialProvidersRequest(TeaModel):
    def __init__(
        self,
        max_results: int = None,
        next_token: str = None,
        token_vault_name: str = None,
    ):
        self.max_results = max_results
        self.next_token = next_token
        self.token_vault_name = token_vault_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.max_results is not None:
            result['MaxResults'] = self.max_results
        if self.next_token is not None:
            result['NextToken'] = self.next_token
        if self.token_vault_name is not None:
            result['TokenVaultName'] = self.token_vault_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('MaxResults') is not None:
            self.max_results = m.get('MaxResults')
        if m.get('NextToken') is not None:
            self.next_token = m.get('NextToken')
        if m.get('TokenVaultName') is not None:
            self.token_vault_name = m.get('TokenVaultName')
        return self


class ListOAuth2CredentialProvidersResponseBodyOAuth2CredentialProviders(TeaModel):
    def __init__(
        self,
        callback_url: str = None,
        create_time: str = None,
        credential_provider_arn: str = None,
        credential_provider_vendor: str = None,
        description: str = None,
        oauth_2credential_provider_name: str = None,
        oauth_2provider_config: OAuth2ProviderConfig = None,
        token_vault_name: str = None,
        update_time: str = None,
    ):
        self.callback_url = callback_url
        self.create_time = create_time
        self.credential_provider_arn = credential_provider_arn
        self.credential_provider_vendor = credential_provider_vendor
        self.description = description
        self.oauth_2credential_provider_name = oauth_2credential_provider_name
        self.oauth_2provider_config = oauth_2provider_config
        self.token_vault_name = token_vault_name
        self.update_time = update_time

    def validate(self):
        if self.oauth_2provider_config:
            self.oauth_2provider_config.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.callback_url is not None:
            result['CallbackURL'] = self.callback_url
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.credential_provider_arn is not None:
            result['CredentialProviderArn'] = self.credential_provider_arn
        if self.credential_provider_vendor is not None:
            result['CredentialProviderVendor'] = self.credential_provider_vendor
        if self.description is not None:
            result['Description'] = self.description
        if self.oauth_2credential_provider_name is not None:
            result['OAuth2CredentialProviderName'] = self.oauth_2credential_provider_name
        if self.oauth_2provider_config is not None:
            result['OAuth2ProviderConfig'] = self.oauth_2provider_config.to_map()
        if self.token_vault_name is not None:
            result['TokenVaultName'] = self.token_vault_name
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CallbackURL') is not None:
            self.callback_url = m.get('CallbackURL')
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('CredentialProviderArn') is not None:
            self.credential_provider_arn = m.get('CredentialProviderArn')
        if m.get('CredentialProviderVendor') is not None:
            self.credential_provider_vendor = m.get('CredentialProviderVendor')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('OAuth2CredentialProviderName') is not None:
            self.oauth_2credential_provider_name = m.get('OAuth2CredentialProviderName')
        if m.get('OAuth2ProviderConfig') is not None:
            temp_model = OAuth2ProviderConfig()
            self.oauth_2provider_config = temp_model.from_map(m['OAuth2ProviderConfig'])
        if m.get('TokenVaultName') is not None:
            self.token_vault_name = m.get('TokenVaultName')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        return self


class ListOAuth2CredentialProvidersResponseBody(TeaModel):
    def __init__(
        self,
        max_results: int = None,
        next_token: str = None,
        oauth_2credential_providers: List[ListOAuth2CredentialProvidersResponseBodyOAuth2CredentialProviders] = None,
        request_id: str = None,
        total_count: int = None,
    ):
        self.max_results = max_results
        self.next_token = next_token
        self.oauth_2credential_providers = oauth_2credential_providers
        self.request_id = request_id
        self.total_count = total_count

    def validate(self):
        if self.oauth_2credential_providers:
            for k in self.oauth_2credential_providers:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.max_results is not None:
            result['MaxResults'] = self.max_results
        if self.next_token is not None:
            result['NextToken'] = self.next_token
        result['OAuth2CredentialProviders'] = []
        if self.oauth_2credential_providers is not None:
            for k in self.oauth_2credential_providers:
                result['OAuth2CredentialProviders'].append(k.to_map() if k else None)
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.total_count is not None:
            result['TotalCount'] = self.total_count
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('MaxResults') is not None:
            self.max_results = m.get('MaxResults')
        if m.get('NextToken') is not None:
            self.next_token = m.get('NextToken')
        self.oauth_2credential_providers = []
        if m.get('OAuth2CredentialProviders') is not None:
            for k in m.get('OAuth2CredentialProviders'):
                temp_model = ListOAuth2CredentialProvidersResponseBodyOAuth2CredentialProviders()
                self.oauth_2credential_providers.append(temp_model.from_map(k))
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('TotalCount') is not None:
            self.total_count = m.get('TotalCount')
        return self


class ListOAuth2CredentialProvidersResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: ListOAuth2CredentialProvidersResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = ListOAuth2CredentialProvidersResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class ListPoliciesRequest(TeaModel):
    def __init__(
        self,
        max_results: int = None,
        next_token: str = None,
        policy_set_name: str = None,
    ):
        self.max_results = max_results
        self.next_token = next_token
        self.policy_set_name = policy_set_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.max_results is not None:
            result['MaxResults'] = self.max_results
        if self.next_token is not None:
            result['NextToken'] = self.next_token
        if self.policy_set_name is not None:
            result['PolicySetName'] = self.policy_set_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('MaxResults') is not None:
            self.max_results = m.get('MaxResults')
        if m.get('NextToken') is not None:
            self.next_token = m.get('NextToken')
        if m.get('PolicySetName') is not None:
            self.policy_set_name = m.get('PolicySetName')
        return self


class ListPoliciesResponseBodyPolicies(TeaModel):
    def __init__(
        self,
        create_time: str = None,
        definition: Definition = None,
        description: str = None,
        policy_arn: str = None,
        policy_name: str = None,
        policy_set_name: str = None,
        update_time: str = None,
    ):
        self.create_time = create_time
        self.definition = definition
        self.description = description
        self.policy_arn = policy_arn
        self.policy_name = policy_name
        self.policy_set_name = policy_set_name
        self.update_time = update_time

    def validate(self):
        if self.definition:
            self.definition.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.definition is not None:
            result['Definition'] = self.definition.to_map()
        if self.description is not None:
            result['Description'] = self.description
        if self.policy_arn is not None:
            result['PolicyArn'] = self.policy_arn
        if self.policy_name is not None:
            result['PolicyName'] = self.policy_name
        if self.policy_set_name is not None:
            result['PolicySetName'] = self.policy_set_name
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('Definition') is not None:
            temp_model = Definition()
            self.definition = temp_model.from_map(m['Definition'])
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('PolicyArn') is not None:
            self.policy_arn = m.get('PolicyArn')
        if m.get('PolicyName') is not None:
            self.policy_name = m.get('PolicyName')
        if m.get('PolicySetName') is not None:
            self.policy_set_name = m.get('PolicySetName')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        return self


class ListPoliciesResponseBody(TeaModel):
    def __init__(
        self,
        max_results: int = None,
        next_token: str = None,
        policies: List[ListPoliciesResponseBodyPolicies] = None,
        request_id: str = None,
        total_count: int = None,
    ):
        self.max_results = max_results
        self.next_token = next_token
        self.policies = policies
        self.request_id = request_id
        self.total_count = total_count

    def validate(self):
        if self.policies:
            for k in self.policies:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.max_results is not None:
            result['MaxResults'] = self.max_results
        if self.next_token is not None:
            result['NextToken'] = self.next_token
        result['Policies'] = []
        if self.policies is not None:
            for k in self.policies:
                result['Policies'].append(k.to_map() if k else None)
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.total_count is not None:
            result['TotalCount'] = self.total_count
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('MaxResults') is not None:
            self.max_results = m.get('MaxResults')
        if m.get('NextToken') is not None:
            self.next_token = m.get('NextToken')
        self.policies = []
        if m.get('Policies') is not None:
            for k in m.get('Policies'):
                temp_model = ListPoliciesResponseBodyPolicies()
                self.policies.append(temp_model.from_map(k))
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('TotalCount') is not None:
            self.total_count = m.get('TotalCount')
        return self


class ListPoliciesResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: ListPoliciesResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = ListPoliciesResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class ListPolicySetAttachedGatewaysRequest(TeaModel):
    def __init__(
        self,
        max_results: int = None,
        next_token: str = None,
        policy_set_name: str = None,
    ):
        self.max_results = max_results
        self.next_token = next_token
        self.policy_set_name = policy_set_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.max_results is not None:
            result['MaxResults'] = self.max_results
        if self.next_token is not None:
            result['NextToken'] = self.next_token
        if self.policy_set_name is not None:
            result['PolicySetName'] = self.policy_set_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('MaxResults') is not None:
            self.max_results = m.get('MaxResults')
        if m.get('NextToken') is not None:
            self.next_token = m.get('NextToken')
        if m.get('PolicySetName') is not None:
            self.policy_set_name = m.get('PolicySetName')
        return self


class ListPolicySetAttachedGatewaysResponseBodyAttachedGateways(TeaModel):
    def __init__(
        self,
        attached_policy_set_name: str = None,
        attached_time: str = None,
        enforcement_mode: str = None,
        gateway_arn: str = None,
    ):
        self.attached_policy_set_name = attached_policy_set_name
        self.attached_time = attached_time
        self.enforcement_mode = enforcement_mode
        self.gateway_arn = gateway_arn

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.attached_policy_set_name is not None:
            result['AttachedPolicySetName'] = self.attached_policy_set_name
        if self.attached_time is not None:
            result['AttachedTime'] = self.attached_time
        if self.enforcement_mode is not None:
            result['EnforcementMode'] = self.enforcement_mode
        if self.gateway_arn is not None:
            result['GatewayArn'] = self.gateway_arn
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AttachedPolicySetName') is not None:
            self.attached_policy_set_name = m.get('AttachedPolicySetName')
        if m.get('AttachedTime') is not None:
            self.attached_time = m.get('AttachedTime')
        if m.get('EnforcementMode') is not None:
            self.enforcement_mode = m.get('EnforcementMode')
        if m.get('GatewayArn') is not None:
            self.gateway_arn = m.get('GatewayArn')
        return self


class ListPolicySetAttachedGatewaysResponseBody(TeaModel):
    def __init__(
        self,
        attached_gateways: List[ListPolicySetAttachedGatewaysResponseBodyAttachedGateways] = None,
        max_results: int = None,
        next_token: str = None,
        request_id: str = None,
        total_count: int = None,
    ):
        self.attached_gateways = attached_gateways
        self.max_results = max_results
        self.next_token = next_token
        self.request_id = request_id
        self.total_count = total_count

    def validate(self):
        if self.attached_gateways:
            for k in self.attached_gateways:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        result['AttachedGateways'] = []
        if self.attached_gateways is not None:
            for k in self.attached_gateways:
                result['AttachedGateways'].append(k.to_map() if k else None)
        if self.max_results is not None:
            result['MaxResults'] = self.max_results
        if self.next_token is not None:
            result['NextToken'] = self.next_token
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.total_count is not None:
            result['TotalCount'] = self.total_count
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        self.attached_gateways = []
        if m.get('AttachedGateways') is not None:
            for k in m.get('AttachedGateways'):
                temp_model = ListPolicySetAttachedGatewaysResponseBodyAttachedGateways()
                self.attached_gateways.append(temp_model.from_map(k))
        if m.get('MaxResults') is not None:
            self.max_results = m.get('MaxResults')
        if m.get('NextToken') is not None:
            self.next_token = m.get('NextToken')
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('TotalCount') is not None:
            self.total_count = m.get('TotalCount')
        return self


class ListPolicySetAttachedGatewaysResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: ListPolicySetAttachedGatewaysResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = ListPolicySetAttachedGatewaysResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class ListPolicySetsRequest(TeaModel):
    def __init__(
        self,
        max_results: int = None,
        next_token: str = None,
    ):
        self.max_results = max_results
        self.next_token = next_token

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.max_results is not None:
            result['MaxResults'] = self.max_results
        if self.next_token is not None:
            result['NextToken'] = self.next_token
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('MaxResults') is not None:
            self.max_results = m.get('MaxResults')
        if m.get('NextToken') is not None:
            self.next_token = m.get('NextToken')
        return self


class ListPolicySetsResponseBodyPolicySets(TeaModel):
    def __init__(
        self,
        create_time: str = None,
        description: str = None,
        policy_set_arn: str = None,
        policy_set_name: str = None,
        update_time: str = None,
    ):
        self.create_time = create_time
        self.description = description
        self.policy_set_arn = policy_set_arn
        self.policy_set_name = policy_set_name
        self.update_time = update_time

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.description is not None:
            result['Description'] = self.description
        if self.policy_set_arn is not None:
            result['PolicySetArn'] = self.policy_set_arn
        if self.policy_set_name is not None:
            result['PolicySetName'] = self.policy_set_name
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('PolicySetArn') is not None:
            self.policy_set_arn = m.get('PolicySetArn')
        if m.get('PolicySetName') is not None:
            self.policy_set_name = m.get('PolicySetName')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        return self


class ListPolicySetsResponseBody(TeaModel):
    def __init__(
        self,
        max_results: int = None,
        next_token: str = None,
        policy_sets: List[ListPolicySetsResponseBodyPolicySets] = None,
        request_id: str = None,
        total_count: int = None,
    ):
        self.max_results = max_results
        self.next_token = next_token
        self.policy_sets = policy_sets
        self.request_id = request_id
        self.total_count = total_count

    def validate(self):
        if self.policy_sets:
            for k in self.policy_sets:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.max_results is not None:
            result['MaxResults'] = self.max_results
        if self.next_token is not None:
            result['NextToken'] = self.next_token
        result['PolicySets'] = []
        if self.policy_sets is not None:
            for k in self.policy_sets:
                result['PolicySets'].append(k.to_map() if k else None)
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.total_count is not None:
            result['TotalCount'] = self.total_count
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('MaxResults') is not None:
            self.max_results = m.get('MaxResults')
        if m.get('NextToken') is not None:
            self.next_token = m.get('NextToken')
        self.policy_sets = []
        if m.get('PolicySets') is not None:
            for k in m.get('PolicySets'):
                temp_model = ListPolicySetsResponseBodyPolicySets()
                self.policy_sets.append(temp_model.from_map(k))
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('TotalCount') is not None:
            self.total_count = m.get('TotalCount')
        return self


class ListPolicySetsResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: ListPolicySetsResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = ListPolicySetsResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class ListRoleAssignmentsRequest(TeaModel):
    def __init__(
        self,
        max_results: int = None,
        next_token: str = None,
        principal_name: str = None,
        principal_type: str = None,
        role_name: str = None,
        user_pool_name: str = None,
    ):
        self.max_results = max_results
        self.next_token = next_token
        self.principal_name = principal_name
        self.principal_type = principal_type
        self.role_name = role_name
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.max_results is not None:
            result['MaxResults'] = self.max_results
        if self.next_token is not None:
            result['NextToken'] = self.next_token
        if self.principal_name is not None:
            result['PrincipalName'] = self.principal_name
        if self.principal_type is not None:
            result['PrincipalType'] = self.principal_type
        if self.role_name is not None:
            result['RoleName'] = self.role_name
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('MaxResults') is not None:
            self.max_results = m.get('MaxResults')
        if m.get('NextToken') is not None:
            self.next_token = m.get('NextToken')
        if m.get('PrincipalName') is not None:
            self.principal_name = m.get('PrincipalName')
        if m.get('PrincipalType') is not None:
            self.principal_type = m.get('PrincipalType')
        if m.get('RoleName') is not None:
            self.role_name = m.get('RoleName')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class ListRoleAssignmentsResponseBodyAssignments(TeaModel):
    def __init__(
        self,
        create_time: str = None,
        principal_id: str = None,
        principal_name: str = None,
        principal_type: str = None,
        role_id: str = None,
        role_name: str = None,
        user_pool_id: str = None,
    ):
        self.create_time = create_time
        self.principal_id = principal_id
        self.principal_name = principal_name
        self.principal_type = principal_type
        self.role_id = role_id
        self.role_name = role_name
        self.user_pool_id = user_pool_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.principal_id is not None:
            result['PrincipalId'] = self.principal_id
        if self.principal_name is not None:
            result['PrincipalName'] = self.principal_name
        if self.principal_type is not None:
            result['PrincipalType'] = self.principal_type
        if self.role_id is not None:
            result['RoleId'] = self.role_id
        if self.role_name is not None:
            result['RoleName'] = self.role_name
        if self.user_pool_id is not None:
            result['UserPoolId'] = self.user_pool_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('PrincipalId') is not None:
            self.principal_id = m.get('PrincipalId')
        if m.get('PrincipalName') is not None:
            self.principal_name = m.get('PrincipalName')
        if m.get('PrincipalType') is not None:
            self.principal_type = m.get('PrincipalType')
        if m.get('RoleId') is not None:
            self.role_id = m.get('RoleId')
        if m.get('RoleName') is not None:
            self.role_name = m.get('RoleName')
        if m.get('UserPoolId') is not None:
            self.user_pool_id = m.get('UserPoolId')
        return self


class ListRoleAssignmentsResponseBody(TeaModel):
    def __init__(
        self,
        assignments: List[ListRoleAssignmentsResponseBodyAssignments] = None,
        max_results: int = None,
        next_token: str = None,
        request_id: str = None,
        total_count: int = None,
    ):
        self.assignments = assignments
        self.max_results = max_results
        self.next_token = next_token
        self.request_id = request_id
        self.total_count = total_count

    def validate(self):
        if self.assignments:
            for k in self.assignments:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        result['Assignments'] = []
        if self.assignments is not None:
            for k in self.assignments:
                result['Assignments'].append(k.to_map() if k else None)
        if self.max_results is not None:
            result['MaxResults'] = self.max_results
        if self.next_token is not None:
            result['NextToken'] = self.next_token
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.total_count is not None:
            result['TotalCount'] = self.total_count
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        self.assignments = []
        if m.get('Assignments') is not None:
            for k in m.get('Assignments'):
                temp_model = ListRoleAssignmentsResponseBodyAssignments()
                self.assignments.append(temp_model.from_map(k))
        if m.get('MaxResults') is not None:
            self.max_results = m.get('MaxResults')
        if m.get('NextToken') is not None:
            self.next_token = m.get('NextToken')
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('TotalCount') is not None:
            self.total_count = m.get('TotalCount')
        return self


class ListRoleAssignmentsResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: ListRoleAssignmentsResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = ListRoleAssignmentsResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class ListRolesRequest(TeaModel):
    def __init__(
        self,
        max_results: int = None,
        next_token: str = None,
        user_pool_name: str = None,
    ):
        self.max_results = max_results
        self.next_token = next_token
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.max_results is not None:
            result['MaxResults'] = self.max_results
        if self.next_token is not None:
            result['NextToken'] = self.next_token
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('MaxResults') is not None:
            self.max_results = m.get('MaxResults')
        if m.get('NextToken') is not None:
            self.next_token = m.get('NextToken')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class ListRolesResponseBodyRoles(TeaModel):
    def __init__(
        self,
        create_time: str = None,
        description: str = None,
        role_id: str = None,
        role_name: str = None,
        type: str = None,
        update_time: str = None,
    ):
        self.create_time = create_time
        self.description = description
        self.role_id = role_id
        self.role_name = role_name
        self.type = type
        self.update_time = update_time

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.description is not None:
            result['Description'] = self.description
        if self.role_id is not None:
            result['RoleId'] = self.role_id
        if self.role_name is not None:
            result['RoleName'] = self.role_name
        if self.type is not None:
            result['Type'] = self.type
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('RoleId') is not None:
            self.role_id = m.get('RoleId')
        if m.get('RoleName') is not None:
            self.role_name = m.get('RoleName')
        if m.get('Type') is not None:
            self.type = m.get('Type')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        return self


class ListRolesResponseBody(TeaModel):
    def __init__(
        self,
        max_results: int = None,
        next_token: str = None,
        request_id: str = None,
        roles: List[ListRolesResponseBodyRoles] = None,
        total_count: int = None,
    ):
        self.max_results = max_results
        self.next_token = next_token
        self.request_id = request_id
        self.roles = roles
        self.total_count = total_count

    def validate(self):
        if self.roles:
            for k in self.roles:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.max_results is not None:
            result['MaxResults'] = self.max_results
        if self.next_token is not None:
            result['NextToken'] = self.next_token
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        result['Roles'] = []
        if self.roles is not None:
            for k in self.roles:
                result['Roles'].append(k.to_map() if k else None)
        if self.total_count is not None:
            result['TotalCount'] = self.total_count
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('MaxResults') is not None:
            self.max_results = m.get('MaxResults')
        if m.get('NextToken') is not None:
            self.next_token = m.get('NextToken')
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        self.roles = []
        if m.get('Roles') is not None:
            for k in m.get('Roles'):
                temp_model = ListRolesResponseBodyRoles()
                self.roles.append(temp_model.from_map(k))
        if m.get('TotalCount') is not None:
            self.total_count = m.get('TotalCount')
        return self


class ListRolesResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: ListRolesResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = ListRolesResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class ListSAMLIdentityProviderCertificatesRequest(TeaModel):
    def __init__(
        self,
        user_pool_name: str = None,
    ):
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class ListSAMLIdentityProviderCertificatesResponseBodyX509Certificates(TeaModel):
    def __init__(
        self,
        certificate_id: str = None,
        x_509certificate: str = None,
    ):
        self.certificate_id = certificate_id
        self.x_509certificate = x_509certificate

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.certificate_id is not None:
            result['CertificateId'] = self.certificate_id
        if self.x_509certificate is not None:
            result['X509Certificate'] = self.x_509certificate
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CertificateId') is not None:
            self.certificate_id = m.get('CertificateId')
        if m.get('X509Certificate') is not None:
            self.x_509certificate = m.get('X509Certificate')
        return self


class ListSAMLIdentityProviderCertificatesResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
        x_509certificates: List[ListSAMLIdentityProviderCertificatesResponseBodyX509Certificates] = None,
    ):
        self.request_id = request_id
        self.x_509certificates = x_509certificates

    def validate(self):
        if self.x_509certificates:
            for k in self.x_509certificates:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        result['X509Certificates'] = []
        if self.x_509certificates is not None:
            for k in self.x_509certificates:
                result['X509Certificates'].append(k.to_map() if k else None)
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        self.x_509certificates = []
        if m.get('X509Certificates') is not None:
            for k in m.get('X509Certificates'):
                temp_model = ListSAMLIdentityProviderCertificatesResponseBodyX509Certificates()
                self.x_509certificates.append(temp_model.from_map(k))
        return self


class ListSAMLIdentityProviderCertificatesResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: ListSAMLIdentityProviderCertificatesResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = ListSAMLIdentityProviderCertificatesResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class ListTokenVaultsRequest(TeaModel):
    def __init__(
        self,
        max_results: int = None,
        next_token: str = None,
    ):
        self.max_results = max_results
        self.next_token = next_token

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.max_results is not None:
            result['MaxResults'] = self.max_results
        if self.next_token is not None:
            result['NextToken'] = self.next_token
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('MaxResults') is not None:
            self.max_results = m.get('MaxResults')
        if m.get('NextToken') is not None:
            self.next_token = m.get('NextToken')
        return self


class ListTokenVaultsResponseBodyTokenVaultsEncryptionConfig(TeaModel):
    def __init__(
        self,
        key_type: str = None,
        kms_key_arn: str = None,
    ):
        self.key_type = key_type
        self.kms_key_arn = kms_key_arn

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.key_type is not None:
            result['KeyType'] = self.key_type
        if self.kms_key_arn is not None:
            result['KmsKeyArn'] = self.kms_key_arn
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('KeyType') is not None:
            self.key_type = m.get('KeyType')
        if m.get('KmsKeyArn') is not None:
            self.kms_key_arn = m.get('KmsKeyArn')
        return self


class ListTokenVaultsResponseBodyTokenVaults(TeaModel):
    def __init__(
        self,
        create_time: str = None,
        description: str = None,
        encryption_config: ListTokenVaultsResponseBodyTokenVaultsEncryptionConfig = None,
        role_arn: str = None,
        token_vault_arn: str = None,
        token_vault_name: str = None,
        update_time: str = None,
    ):
        self.create_time = create_time
        self.description = description
        self.encryption_config = encryption_config
        self.role_arn = role_arn
        self.token_vault_arn = token_vault_arn
        self.token_vault_name = token_vault_name
        self.update_time = update_time

    def validate(self):
        if self.encryption_config:
            self.encryption_config.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.description is not None:
            result['Description'] = self.description
        if self.encryption_config is not None:
            result['EncryptionConfig'] = self.encryption_config.to_map()
        if self.role_arn is not None:
            result['RoleArn'] = self.role_arn
        if self.token_vault_arn is not None:
            result['TokenVaultArn'] = self.token_vault_arn
        if self.token_vault_name is not None:
            result['TokenVaultName'] = self.token_vault_name
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('EncryptionConfig') is not None:
            temp_model = ListTokenVaultsResponseBodyTokenVaultsEncryptionConfig()
            self.encryption_config = temp_model.from_map(m['EncryptionConfig'])
        if m.get('RoleArn') is not None:
            self.role_arn = m.get('RoleArn')
        if m.get('TokenVaultArn') is not None:
            self.token_vault_arn = m.get('TokenVaultArn')
        if m.get('TokenVaultName') is not None:
            self.token_vault_name = m.get('TokenVaultName')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        return self


class ListTokenVaultsResponseBody(TeaModel):
    def __init__(
        self,
        max_results: int = None,
        next_token: str = None,
        request_id: str = None,
        token_vaults: List[ListTokenVaultsResponseBodyTokenVaults] = None,
        total_count: int = None,
    ):
        self.max_results = max_results
        self.next_token = next_token
        self.request_id = request_id
        self.token_vaults = token_vaults
        self.total_count = total_count

    def validate(self):
        if self.token_vaults:
            for k in self.token_vaults:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.max_results is not None:
            result['MaxResults'] = self.max_results
        if self.next_token is not None:
            result['NextToken'] = self.next_token
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        result['TokenVaults'] = []
        if self.token_vaults is not None:
            for k in self.token_vaults:
                result['TokenVaults'].append(k.to_map() if k else None)
        if self.total_count is not None:
            result['TotalCount'] = self.total_count
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('MaxResults') is not None:
            self.max_results = m.get('MaxResults')
        if m.get('NextToken') is not None:
            self.next_token = m.get('NextToken')
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        self.token_vaults = []
        if m.get('TokenVaults') is not None:
            for k in m.get('TokenVaults'):
                temp_model = ListTokenVaultsResponseBodyTokenVaults()
                self.token_vaults.append(temp_model.from_map(k))
        if m.get('TotalCount') is not None:
            self.total_count = m.get('TotalCount')
        return self


class ListTokenVaultsResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: ListTokenVaultsResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = ListTokenVaultsResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class ListUserPoolClientsRequest(TeaModel):
    def __init__(
        self,
        max_results: int = None,
        next_token: str = None,
        user_pool_name: str = None,
    ):
        self.max_results = max_results
        self.next_token = next_token
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.max_results is not None:
            result['MaxResults'] = self.max_results
        if self.next_token is not None:
            result['NextToken'] = self.next_token
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('MaxResults') is not None:
            self.max_results = m.get('MaxResults')
        if m.get('NextToken') is not None:
            self.next_token = m.get('NextToken')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class ListUserPoolClientsResponseBodyClientsClientScopes(TeaModel):
    def __init__(
        self,
        description: str = None,
        scope_name: str = None,
    ):
        self.description = description
        self.scope_name = scope_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.description is not None:
            result['Description'] = self.description
        if self.scope_name is not None:
            result['ScopeName'] = self.scope_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('ScopeName') is not None:
            self.scope_name = m.get('ScopeName')
        return self


class ListUserPoolClientsResponseBodyClients(TeaModel):
    def __init__(
        self,
        access_token_validity: str = None,
        client_id: str = None,
        client_name: str = None,
        client_scopes: List[ListUserPoolClientsResponseBodyClientsClientScopes] = None,
        create_time: str = None,
        enforce_pkce: bool = None,
        redirect_uris: List[str] = None,
        refresh_token_validity: str = None,
        secret_required: bool = None,
        update_time: str = None,
        user_pool_name: str = None,
    ):
        self.access_token_validity = access_token_validity
        self.client_id = client_id
        self.client_name = client_name
        self.client_scopes = client_scopes
        self.create_time = create_time
        self.enforce_pkce = enforce_pkce
        self.redirect_uris = redirect_uris
        self.refresh_token_validity = refresh_token_validity
        self.secret_required = secret_required
        self.update_time = update_time
        self.user_pool_name = user_pool_name

    def validate(self):
        if self.client_scopes:
            for k in self.client_scopes:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.access_token_validity is not None:
            result['AccessTokenValidity'] = self.access_token_validity
        if self.client_id is not None:
            result['ClientId'] = self.client_id
        if self.client_name is not None:
            result['ClientName'] = self.client_name
        result['ClientScopes'] = []
        if self.client_scopes is not None:
            for k in self.client_scopes:
                result['ClientScopes'].append(k.to_map() if k else None)
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.enforce_pkce is not None:
            result['EnforcePKCE'] = self.enforce_pkce
        if self.redirect_uris is not None:
            result['RedirectURIs'] = self.redirect_uris
        if self.refresh_token_validity is not None:
            result['RefreshTokenValidity'] = self.refresh_token_validity
        if self.secret_required is not None:
            result['SecretRequired'] = self.secret_required
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AccessTokenValidity') is not None:
            self.access_token_validity = m.get('AccessTokenValidity')
        if m.get('ClientId') is not None:
            self.client_id = m.get('ClientId')
        if m.get('ClientName') is not None:
            self.client_name = m.get('ClientName')
        self.client_scopes = []
        if m.get('ClientScopes') is not None:
            for k in m.get('ClientScopes'):
                temp_model = ListUserPoolClientsResponseBodyClientsClientScopes()
                self.client_scopes.append(temp_model.from_map(k))
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('EnforcePKCE') is not None:
            self.enforce_pkce = m.get('EnforcePKCE')
        if m.get('RedirectURIs') is not None:
            self.redirect_uris = m.get('RedirectURIs')
        if m.get('RefreshTokenValidity') is not None:
            self.refresh_token_validity = m.get('RefreshTokenValidity')
        if m.get('SecretRequired') is not None:
            self.secret_required = m.get('SecretRequired')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class ListUserPoolClientsResponseBody(TeaModel):
    def __init__(
        self,
        clients: List[ListUserPoolClientsResponseBodyClients] = None,
        max_results: int = None,
        next_token: str = None,
        request_id: str = None,
        total_count: int = None,
    ):
        self.clients = clients
        self.max_results = max_results
        self.next_token = next_token
        self.request_id = request_id
        self.total_count = total_count

    def validate(self):
        if self.clients:
            for k in self.clients:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        result['Clients'] = []
        if self.clients is not None:
            for k in self.clients:
                result['Clients'].append(k.to_map() if k else None)
        if self.max_results is not None:
            result['MaxResults'] = self.max_results
        if self.next_token is not None:
            result['NextToken'] = self.next_token
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.total_count is not None:
            result['TotalCount'] = self.total_count
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        self.clients = []
        if m.get('Clients') is not None:
            for k in m.get('Clients'):
                temp_model = ListUserPoolClientsResponseBodyClients()
                self.clients.append(temp_model.from_map(k))
        if m.get('MaxResults') is not None:
            self.max_results = m.get('MaxResults')
        if m.get('NextToken') is not None:
            self.next_token = m.get('NextToken')
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('TotalCount') is not None:
            self.total_count = m.get('TotalCount')
        return self


class ListUserPoolClientsResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: ListUserPoolClientsResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = ListUserPoolClientsResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class ListUserPoolsRequest(TeaModel):
    def __init__(
        self,
        max_results: int = None,
        next_token: str = None,
    ):
        self.max_results = max_results
        self.next_token = next_token

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.max_results is not None:
            result['MaxResults'] = self.max_results
        if self.next_token is not None:
            result['NextToken'] = self.next_token
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('MaxResults') is not None:
            self.max_results = m.get('MaxResults')
        if m.get('NextToken') is not None:
            self.next_token = m.get('NextToken')
        return self


class ListUserPoolsResponseBodyUserPools(TeaModel):
    def __init__(
        self,
        create_time: str = None,
        description: str = None,
        update_time: str = None,
        user_pool_arn: str = None,
        user_pool_id: str = None,
        user_pool_name: str = None,
    ):
        self.create_time = create_time
        self.description = description
        self.update_time = update_time
        self.user_pool_arn = user_pool_arn
        self.user_pool_id = user_pool_id
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.description is not None:
            result['Description'] = self.description
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        if self.user_pool_arn is not None:
            result['UserPoolArn'] = self.user_pool_arn
        if self.user_pool_id is not None:
            result['UserPoolId'] = self.user_pool_id
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        if m.get('UserPoolArn') is not None:
            self.user_pool_arn = m.get('UserPoolArn')
        if m.get('UserPoolId') is not None:
            self.user_pool_id = m.get('UserPoolId')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class ListUserPoolsResponseBody(TeaModel):
    def __init__(
        self,
        max_results: int = None,
        next_token: str = None,
        request_id: str = None,
        total_count: int = None,
        user_pools: List[ListUserPoolsResponseBodyUserPools] = None,
    ):
        self.max_results = max_results
        self.next_token = next_token
        self.request_id = request_id
        self.total_count = total_count
        self.user_pools = user_pools

    def validate(self):
        if self.user_pools:
            for k in self.user_pools:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.max_results is not None:
            result['MaxResults'] = self.max_results
        if self.next_token is not None:
            result['NextToken'] = self.next_token
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.total_count is not None:
            result['TotalCount'] = self.total_count
        result['UserPools'] = []
        if self.user_pools is not None:
            for k in self.user_pools:
                result['UserPools'].append(k.to_map() if k else None)
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('MaxResults') is not None:
            self.max_results = m.get('MaxResults')
        if m.get('NextToken') is not None:
            self.next_token = m.get('NextToken')
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('TotalCount') is not None:
            self.total_count = m.get('TotalCount')
        self.user_pools = []
        if m.get('UserPools') is not None:
            for k in m.get('UserPools'):
                temp_model = ListUserPoolsResponseBodyUserPools()
                self.user_pools.append(temp_model.from_map(k))
        return self


class ListUserPoolsResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: ListUserPoolsResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = ListUserPoolsResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class ListUsersRequest(TeaModel):
    def __init__(
        self,
        max_results: int = None,
        next_token: str = None,
        user_pool_name: str = None,
    ):
        self.max_results = max_results
        self.next_token = next_token
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.max_results is not None:
            result['MaxResults'] = self.max_results
        if self.next_token is not None:
            result['NextToken'] = self.next_token
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('MaxResults') is not None:
            self.max_results = m.get('MaxResults')
        if m.get('NextToken') is not None:
            self.next_token = m.get('NextToken')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class ListUsersResponseBodyUsers(TeaModel):
    def __init__(
        self,
        create_time: str = None,
        description: str = None,
        display_name: str = None,
        update_time: str = None,
        user_id: str = None,
        user_name: str = None,
    ):
        self.create_time = create_time
        self.description = description
        self.display_name = display_name
        self.update_time = update_time
        self.user_id = user_id
        self.user_name = user_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.description is not None:
            result['Description'] = self.description
        if self.display_name is not None:
            result['DisplayName'] = self.display_name
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        if self.user_id is not None:
            result['UserId'] = self.user_id
        if self.user_name is not None:
            result['UserName'] = self.user_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('DisplayName') is not None:
            self.display_name = m.get('DisplayName')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        if m.get('UserId') is not None:
            self.user_id = m.get('UserId')
        if m.get('UserName') is not None:
            self.user_name = m.get('UserName')
        return self


class ListUsersResponseBody(TeaModel):
    def __init__(
        self,
        max_results: int = None,
        next_token: str = None,
        request_id: str = None,
        total_count: int = None,
        users: List[ListUsersResponseBodyUsers] = None,
    ):
        self.max_results = max_results
        self.next_token = next_token
        self.request_id = request_id
        self.total_count = total_count
        self.users = users

    def validate(self):
        if self.users:
            for k in self.users:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.max_results is not None:
            result['MaxResults'] = self.max_results
        if self.next_token is not None:
            result['NextToken'] = self.next_token
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.total_count is not None:
            result['TotalCount'] = self.total_count
        result['Users'] = []
        if self.users is not None:
            for k in self.users:
                result['Users'].append(k.to_map() if k else None)
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('MaxResults') is not None:
            self.max_results = m.get('MaxResults')
        if m.get('NextToken') is not None:
            self.next_token = m.get('NextToken')
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('TotalCount') is not None:
            self.total_count = m.get('TotalCount')
        self.users = []
        if m.get('Users') is not None:
            for k in m.get('Users'):
                temp_model = ListUsersResponseBodyUsers()
                self.users.append(temp_model.from_map(k))
        return self


class ListUsersResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: ListUsersResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = ListUsersResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class ListWorkloadIdentitiesRequest(TeaModel):
    def __init__(
        self,
        max_results: int = None,
        next_token: str = None,
    ):
        self.max_results = max_results
        self.next_token = next_token

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.max_results is not None:
            result['MaxResults'] = self.max_results
        if self.next_token is not None:
            result['NextToken'] = self.next_token
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('MaxResults') is not None:
            self.max_results = m.get('MaxResults')
        if m.get('NextToken') is not None:
            self.next_token = m.get('NextToken')
        return self


class ListWorkloadIdentitiesResponseBodyWorkloadIdentities(TeaModel):
    def __init__(
        self,
        allowed_resource_oauth_2return_urls: List[str] = None,
        create_time: str = None,
        description: str = None,
        identity_provider_name: str = None,
        role_arn: str = None,
        update_time: str = None,
        workload_identity_arn: str = None,
        workload_identity_name: str = None,
    ):
        self.allowed_resource_oauth_2return_urls = allowed_resource_oauth_2return_urls
        self.create_time = create_time
        self.description = description
        self.identity_provider_name = identity_provider_name
        self.role_arn = role_arn
        self.update_time = update_time
        self.workload_identity_arn = workload_identity_arn
        self.workload_identity_name = workload_identity_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.allowed_resource_oauth_2return_urls is not None:
            result['AllowedResourceOAuth2ReturnURLs'] = self.allowed_resource_oauth_2return_urls
        if self.create_time is not None:
            result['CreateTime'] = self.create_time
        if self.description is not None:
            result['Description'] = self.description
        if self.identity_provider_name is not None:
            result['IdentityProviderName'] = self.identity_provider_name
        if self.role_arn is not None:
            result['RoleArn'] = self.role_arn
        if self.update_time is not None:
            result['UpdateTime'] = self.update_time
        if self.workload_identity_arn is not None:
            result['WorkloadIdentityArn'] = self.workload_identity_arn
        if self.workload_identity_name is not None:
            result['WorkloadIdentityName'] = self.workload_identity_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AllowedResourceOAuth2ReturnURLs') is not None:
            self.allowed_resource_oauth_2return_urls = m.get('AllowedResourceOAuth2ReturnURLs')
        if m.get('CreateTime') is not None:
            self.create_time = m.get('CreateTime')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('IdentityProviderName') is not None:
            self.identity_provider_name = m.get('IdentityProviderName')
        if m.get('RoleArn') is not None:
            self.role_arn = m.get('RoleArn')
        if m.get('UpdateTime') is not None:
            self.update_time = m.get('UpdateTime')
        if m.get('WorkloadIdentityArn') is not None:
            self.workload_identity_arn = m.get('WorkloadIdentityArn')
        if m.get('WorkloadIdentityName') is not None:
            self.workload_identity_name = m.get('WorkloadIdentityName')
        return self


class ListWorkloadIdentitiesResponseBody(TeaModel):
    def __init__(
        self,
        max_results: int = None,
        next_token: str = None,
        request_id: str = None,
        total_count: int = None,
        workload_identities: List[ListWorkloadIdentitiesResponseBodyWorkloadIdentities] = None,
    ):
        self.max_results = max_results
        self.next_token = next_token
        self.request_id = request_id
        self.total_count = total_count
        self.workload_identities = workload_identities

    def validate(self):
        if self.workload_identities:
            for k in self.workload_identities:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.max_results is not None:
            result['MaxResults'] = self.max_results
        if self.next_token is not None:
            result['NextToken'] = self.next_token
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.total_count is not None:
            result['TotalCount'] = self.total_count
        result['WorkloadIdentities'] = []
        if self.workload_identities is not None:
            for k in self.workload_identities:
                result['WorkloadIdentities'].append(k.to_map() if k else None)
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('MaxResults') is not None:
            self.max_results = m.get('MaxResults')
        if m.get('NextToken') is not None:
            self.next_token = m.get('NextToken')
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('TotalCount') is not None:
            self.total_count = m.get('TotalCount')
        self.workload_identities = []
        if m.get('WorkloadIdentities') is not None:
            for k in m.get('WorkloadIdentities'):
                temp_model = ListWorkloadIdentitiesResponseBodyWorkloadIdentities()
                self.workload_identities.append(temp_model.from_map(k))
        return self


class ListWorkloadIdentitiesResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: ListWorkloadIdentitiesResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = ListWorkloadIdentitiesResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class SetSAMLIdentityProviderRequest(TeaModel):
    def __init__(
        self,
        entity_id: str = None,
        jitprovision_status: str = None,
        jitupdate_status: str = None,
        login_url: str = None,
        ssostatus: str = None,
        user_pool_name: str = None,
        x_509certificates: List[str] = None,
    ):
        self.entity_id = entity_id
        self.jitprovision_status = jitprovision_status
        self.jitupdate_status = jitupdate_status
        self.login_url = login_url
        self.ssostatus = ssostatus
        self.user_pool_name = user_pool_name
        self.x_509certificates = x_509certificates

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.entity_id is not None:
            result['EntityId'] = self.entity_id
        if self.jitprovision_status is not None:
            result['JITProvisionStatus'] = self.jitprovision_status
        if self.jitupdate_status is not None:
            result['JITUpdateStatus'] = self.jitupdate_status
        if self.login_url is not None:
            result['LoginUrl'] = self.login_url
        if self.ssostatus is not None:
            result['SSOStatus'] = self.ssostatus
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        if self.x_509certificates is not None:
            result['X509Certificates'] = self.x_509certificates
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('EntityId') is not None:
            self.entity_id = m.get('EntityId')
        if m.get('JITProvisionStatus') is not None:
            self.jitprovision_status = m.get('JITProvisionStatus')
        if m.get('JITUpdateStatus') is not None:
            self.jitupdate_status = m.get('JITUpdateStatus')
        if m.get('LoginUrl') is not None:
            self.login_url = m.get('LoginUrl')
        if m.get('SSOStatus') is not None:
            self.ssostatus = m.get('SSOStatus')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        if m.get('X509Certificates') is not None:
            self.x_509certificates = m.get('X509Certificates')
        return self


class SetSAMLIdentityProviderShrinkRequest(TeaModel):
    def __init__(
        self,
        entity_id: str = None,
        jitprovision_status: str = None,
        jitupdate_status: str = None,
        login_url: str = None,
        ssostatus: str = None,
        user_pool_name: str = None,
        x_509certificates_shrink: str = None,
    ):
        self.entity_id = entity_id
        self.jitprovision_status = jitprovision_status
        self.jitupdate_status = jitupdate_status
        self.login_url = login_url
        self.ssostatus = ssostatus
        self.user_pool_name = user_pool_name
        self.x_509certificates_shrink = x_509certificates_shrink

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.entity_id is not None:
            result['EntityId'] = self.entity_id
        if self.jitprovision_status is not None:
            result['JITProvisionStatus'] = self.jitprovision_status
        if self.jitupdate_status is not None:
            result['JITUpdateStatus'] = self.jitupdate_status
        if self.login_url is not None:
            result['LoginUrl'] = self.login_url
        if self.ssostatus is not None:
            result['SSOStatus'] = self.ssostatus
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        if self.x_509certificates_shrink is not None:
            result['X509Certificates'] = self.x_509certificates_shrink
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('EntityId') is not None:
            self.entity_id = m.get('EntityId')
        if m.get('JITProvisionStatus') is not None:
            self.jitprovision_status = m.get('JITProvisionStatus')
        if m.get('JITUpdateStatus') is not None:
            self.jitupdate_status = m.get('JITUpdateStatus')
        if m.get('LoginUrl') is not None:
            self.login_url = m.get('LoginUrl')
        if m.get('SSOStatus') is not None:
            self.ssostatus = m.get('SSOStatus')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        if m.get('X509Certificates') is not None:
            self.x_509certificates_shrink = m.get('X509Certificates')
        return self


class SetSAMLIdentityProviderResponseBodySSOIdentityProviderConfigurationX509Certificates(TeaModel):
    def __init__(
        self,
        certificate_id: str = None,
        x_509certificate: str = None,
    ):
        self.certificate_id = certificate_id
        self.x_509certificate = x_509certificate

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.certificate_id is not None:
            result['CertificateId'] = self.certificate_id
        if self.x_509certificate is not None:
            result['X509Certificate'] = self.x_509certificate
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CertificateId') is not None:
            self.certificate_id = m.get('CertificateId')
        if m.get('X509Certificate') is not None:
            self.x_509certificate = m.get('X509Certificate')
        return self


class SetSAMLIdentityProviderResponseBodySSOIdentityProviderConfiguration(TeaModel):
    def __init__(
        self,
        entity_id: str = None,
        jitprovision_status: str = None,
        jitupdate_status: str = None,
        login_url: str = None,
        samlbinding_type: str = None,
        ssostatus: str = None,
        x_509certificates: List[SetSAMLIdentityProviderResponseBodySSOIdentityProviderConfigurationX509Certificates] = None,
    ):
        self.entity_id = entity_id
        self.jitprovision_status = jitprovision_status
        self.jitupdate_status = jitupdate_status
        self.login_url = login_url
        self.samlbinding_type = samlbinding_type
        self.ssostatus = ssostatus
        self.x_509certificates = x_509certificates

    def validate(self):
        if self.x_509certificates:
            for k in self.x_509certificates:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.entity_id is not None:
            result['EntityId'] = self.entity_id
        if self.jitprovision_status is not None:
            result['JITProvisionStatus'] = self.jitprovision_status
        if self.jitupdate_status is not None:
            result['JITUpdateStatus'] = self.jitupdate_status
        if self.login_url is not None:
            result['LoginUrl'] = self.login_url
        if self.samlbinding_type is not None:
            result['SAMLBindingType'] = self.samlbinding_type
        if self.ssostatus is not None:
            result['SSOStatus'] = self.ssostatus
        result['X509Certificates'] = []
        if self.x_509certificates is not None:
            for k in self.x_509certificates:
                result['X509Certificates'].append(k.to_map() if k else None)
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('EntityId') is not None:
            self.entity_id = m.get('EntityId')
        if m.get('JITProvisionStatus') is not None:
            self.jitprovision_status = m.get('JITProvisionStatus')
        if m.get('JITUpdateStatus') is not None:
            self.jitupdate_status = m.get('JITUpdateStatus')
        if m.get('LoginUrl') is not None:
            self.login_url = m.get('LoginUrl')
        if m.get('SAMLBindingType') is not None:
            self.samlbinding_type = m.get('SAMLBindingType')
        if m.get('SSOStatus') is not None:
            self.ssostatus = m.get('SSOStatus')
        self.x_509certificates = []
        if m.get('X509Certificates') is not None:
            for k in m.get('X509Certificates'):
                temp_model = SetSAMLIdentityProviderResponseBodySSOIdentityProviderConfigurationX509Certificates()
                self.x_509certificates.append(temp_model.from_map(k))
        return self


class SetSAMLIdentityProviderResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
        ssoidentity_provider_configuration: SetSAMLIdentityProviderResponseBodySSOIdentityProviderConfiguration = None,
    ):
        self.request_id = request_id
        self.ssoidentity_provider_configuration = ssoidentity_provider_configuration

    def validate(self):
        if self.ssoidentity_provider_configuration:
            self.ssoidentity_provider_configuration.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.ssoidentity_provider_configuration is not None:
            result['SSOIdentityProviderConfiguration'] = self.ssoidentity_provider_configuration.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('SSOIdentityProviderConfiguration') is not None:
            temp_model = SetSAMLIdentityProviderResponseBodySSOIdentityProviderConfiguration()
            self.ssoidentity_provider_configuration = temp_model.from_map(m['SSOIdentityProviderConfiguration'])
        return self


class SetSAMLIdentityProviderResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: SetSAMLIdentityProviderResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = SetSAMLIdentityProviderResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class UpdateAPIKeyCredentialProviderRequest(TeaModel):
    def __init__(
        self,
        apikey: str = None,
        apikey_credential_provider_name: str = None,
        description: str = None,
        token_vault_name: str = None,
    ):
        self.apikey = apikey
        self.apikey_credential_provider_name = apikey_credential_provider_name
        self.description = description
        self.token_vault_name = token_vault_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.apikey is not None:
            result['APIKey'] = self.apikey
        if self.apikey_credential_provider_name is not None:
            result['APIKeyCredentialProviderName'] = self.apikey_credential_provider_name
        if self.description is not None:
            result['Description'] = self.description
        if self.token_vault_name is not None:
            result['TokenVaultName'] = self.token_vault_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('APIKey') is not None:
            self.apikey = m.get('APIKey')
        if m.get('APIKeyCredentialProviderName') is not None:
            self.apikey_credential_provider_name = m.get('APIKeyCredentialProviderName')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('TokenVaultName') is not None:
            self.token_vault_name = m.get('TokenVaultName')
        return self


class UpdateAPIKeyCredentialProviderResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
    ):
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class UpdateAPIKeyCredentialProviderResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: UpdateAPIKeyCredentialProviderResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = UpdateAPIKeyCredentialProviderResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class UpdateGatewayPolicyConfigRequest(TeaModel):
    def __init__(
        self,
        enforcement_mode: str = None,
        gateway_arn: str = None,
    ):
        self.enforcement_mode = enforcement_mode
        self.gateway_arn = gateway_arn

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.enforcement_mode is not None:
            result['EnforcementMode'] = self.enforcement_mode
        if self.gateway_arn is not None:
            result['GatewayArn'] = self.gateway_arn
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('EnforcementMode') is not None:
            self.enforcement_mode = m.get('EnforcementMode')
        if m.get('GatewayArn') is not None:
            self.gateway_arn = m.get('GatewayArn')
        return self


class UpdateGatewayPolicyConfigResponseBodyGatewayPolicyConfig(TeaModel):
    def __init__(
        self,
        enforcement_mode: str = None,
        policy_set_arn: str = None,
    ):
        self.enforcement_mode = enforcement_mode
        self.policy_set_arn = policy_set_arn

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.enforcement_mode is not None:
            result['EnforcementMode'] = self.enforcement_mode
        if self.policy_set_arn is not None:
            result['PolicySetArn'] = self.policy_set_arn
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('EnforcementMode') is not None:
            self.enforcement_mode = m.get('EnforcementMode')
        if m.get('PolicySetArn') is not None:
            self.policy_set_arn = m.get('PolicySetArn')
        return self


class UpdateGatewayPolicyConfigResponseBody(TeaModel):
    def __init__(
        self,
        gateway_policy_config: UpdateGatewayPolicyConfigResponseBodyGatewayPolicyConfig = None,
        request_id: str = None,
    ):
        self.gateway_policy_config = gateway_policy_config
        self.request_id = request_id

    def validate(self):
        if self.gateway_policy_config:
            self.gateway_policy_config.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.gateway_policy_config is not None:
            result['GatewayPolicyConfig'] = self.gateway_policy_config.to_map()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('GatewayPolicyConfig') is not None:
            temp_model = UpdateGatewayPolicyConfigResponseBodyGatewayPolicyConfig()
            self.gateway_policy_config = temp_model.from_map(m['GatewayPolicyConfig'])
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class UpdateGatewayPolicyConfigResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: UpdateGatewayPolicyConfigResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = UpdateGatewayPolicyConfigResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class UpdateIdentityProviderRequest(TeaModel):
    def __init__(
        self,
        allowed_audience: List[str] = None,
        description: str = None,
        discovery_url: str = None,
        identity_provider_name: str = None,
    ):
        self.allowed_audience = allowed_audience
        self.description = description
        self.discovery_url = discovery_url
        self.identity_provider_name = identity_provider_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.allowed_audience is not None:
            result['AllowedAudience'] = self.allowed_audience
        if self.description is not None:
            result['Description'] = self.description
        if self.discovery_url is not None:
            result['DiscoveryURL'] = self.discovery_url
        if self.identity_provider_name is not None:
            result['IdentityProviderName'] = self.identity_provider_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AllowedAudience') is not None:
            self.allowed_audience = m.get('AllowedAudience')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('DiscoveryURL') is not None:
            self.discovery_url = m.get('DiscoveryURL')
        if m.get('IdentityProviderName') is not None:
            self.identity_provider_name = m.get('IdentityProviderName')
        return self


class UpdateIdentityProviderShrinkRequest(TeaModel):
    def __init__(
        self,
        allowed_audience_shrink: str = None,
        description: str = None,
        discovery_url: str = None,
        identity_provider_name: str = None,
    ):
        self.allowed_audience_shrink = allowed_audience_shrink
        self.description = description
        self.discovery_url = discovery_url
        self.identity_provider_name = identity_provider_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.allowed_audience_shrink is not None:
            result['AllowedAudience'] = self.allowed_audience_shrink
        if self.description is not None:
            result['Description'] = self.description
        if self.discovery_url is not None:
            result['DiscoveryURL'] = self.discovery_url
        if self.identity_provider_name is not None:
            result['IdentityProviderName'] = self.identity_provider_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AllowedAudience') is not None:
            self.allowed_audience_shrink = m.get('AllowedAudience')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('DiscoveryURL') is not None:
            self.discovery_url = m.get('DiscoveryURL')
        if m.get('IdentityProviderName') is not None:
            self.identity_provider_name = m.get('IdentityProviderName')
        return self


class UpdateIdentityProviderResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
    ):
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class UpdateIdentityProviderResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: UpdateIdentityProviderResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = UpdateIdentityProviderResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class UpdateOAuth2CredentialProviderRequest(TeaModel):
    def __init__(
        self,
        callback_url: str = None,
        credential_provider_vendor: str = None,
        description: str = None,
        oauth_2credential_provider_name: str = None,
        oauth_2provider_config: OAuth2ProviderConfig = None,
        token_vault_name: str = None,
    ):
        self.callback_url = callback_url
        # AliyunOAuth2
        self.credential_provider_vendor = credential_provider_vendor
        self.description = description
        self.oauth_2credential_provider_name = oauth_2credential_provider_name
        self.oauth_2provider_config = oauth_2provider_config
        self.token_vault_name = token_vault_name

    def validate(self):
        if self.oauth_2provider_config:
            self.oauth_2provider_config.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.callback_url is not None:
            result['CallbackURL'] = self.callback_url
        if self.credential_provider_vendor is not None:
            result['CredentialProviderVendor'] = self.credential_provider_vendor
        if self.description is not None:
            result['Description'] = self.description
        if self.oauth_2credential_provider_name is not None:
            result['OAuth2CredentialProviderName'] = self.oauth_2credential_provider_name
        if self.oauth_2provider_config is not None:
            result['OAuth2ProviderConfig'] = self.oauth_2provider_config.to_map()
        if self.token_vault_name is not None:
            result['TokenVaultName'] = self.token_vault_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CallbackURL') is not None:
            self.callback_url = m.get('CallbackURL')
        if m.get('CredentialProviderVendor') is not None:
            self.credential_provider_vendor = m.get('CredentialProviderVendor')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('OAuth2CredentialProviderName') is not None:
            self.oauth_2credential_provider_name = m.get('OAuth2CredentialProviderName')
        if m.get('OAuth2ProviderConfig') is not None:
            temp_model = OAuth2ProviderConfig()
            self.oauth_2provider_config = temp_model.from_map(m['OAuth2ProviderConfig'])
        if m.get('TokenVaultName') is not None:
            self.token_vault_name = m.get('TokenVaultName')
        return self


class UpdateOAuth2CredentialProviderShrinkRequest(TeaModel):
    def __init__(
        self,
        callback_url: str = None,
        credential_provider_vendor: str = None,
        description: str = None,
        oauth_2credential_provider_name: str = None,
        oauth_2provider_config_shrink: str = None,
        token_vault_name: str = None,
    ):
        self.callback_url = callback_url
        # AliyunOAuth2
        self.credential_provider_vendor = credential_provider_vendor
        self.description = description
        self.oauth_2credential_provider_name = oauth_2credential_provider_name
        self.oauth_2provider_config_shrink = oauth_2provider_config_shrink
        self.token_vault_name = token_vault_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.callback_url is not None:
            result['CallbackURL'] = self.callback_url
        if self.credential_provider_vendor is not None:
            result['CredentialProviderVendor'] = self.credential_provider_vendor
        if self.description is not None:
            result['Description'] = self.description
        if self.oauth_2credential_provider_name is not None:
            result['OAuth2CredentialProviderName'] = self.oauth_2credential_provider_name
        if self.oauth_2provider_config_shrink is not None:
            result['OAuth2ProviderConfig'] = self.oauth_2provider_config_shrink
        if self.token_vault_name is not None:
            result['TokenVaultName'] = self.token_vault_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CallbackURL') is not None:
            self.callback_url = m.get('CallbackURL')
        if m.get('CredentialProviderVendor') is not None:
            self.credential_provider_vendor = m.get('CredentialProviderVendor')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('OAuth2CredentialProviderName') is not None:
            self.oauth_2credential_provider_name = m.get('OAuth2CredentialProviderName')
        if m.get('OAuth2ProviderConfig') is not None:
            self.oauth_2provider_config_shrink = m.get('OAuth2ProviderConfig')
        if m.get('TokenVaultName') is not None:
            self.token_vault_name = m.get('TokenVaultName')
        return self


class UpdateOAuth2CredentialProviderResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
    ):
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class UpdateOAuth2CredentialProviderResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: UpdateOAuth2CredentialProviderResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = UpdateOAuth2CredentialProviderResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class UpdatePolicyRequest(TeaModel):
    def __init__(
        self,
        definition: Definition = None,
        description: str = None,
        policy_name: str = None,
        policy_set_name: str = None,
    ):
        self.definition = definition
        self.description = description
        self.policy_name = policy_name
        self.policy_set_name = policy_set_name

    def validate(self):
        if self.definition:
            self.definition.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.definition is not None:
            result['Definition'] = self.definition.to_map()
        if self.description is not None:
            result['Description'] = self.description
        if self.policy_name is not None:
            result['PolicyName'] = self.policy_name
        if self.policy_set_name is not None:
            result['PolicySetName'] = self.policy_set_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Definition') is not None:
            temp_model = Definition()
            self.definition = temp_model.from_map(m['Definition'])
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('PolicyName') is not None:
            self.policy_name = m.get('PolicyName')
        if m.get('PolicySetName') is not None:
            self.policy_set_name = m.get('PolicySetName')
        return self


class UpdatePolicyShrinkRequest(TeaModel):
    def __init__(
        self,
        definition_shrink: str = None,
        description: str = None,
        policy_name: str = None,
        policy_set_name: str = None,
    ):
        self.definition_shrink = definition_shrink
        self.description = description
        self.policy_name = policy_name
        self.policy_set_name = policy_set_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.definition_shrink is not None:
            result['Definition'] = self.definition_shrink
        if self.description is not None:
            result['Description'] = self.description
        if self.policy_name is not None:
            result['PolicyName'] = self.policy_name
        if self.policy_set_name is not None:
            result['PolicySetName'] = self.policy_set_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Definition') is not None:
            self.definition_shrink = m.get('Definition')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('PolicyName') is not None:
            self.policy_name = m.get('PolicyName')
        if m.get('PolicySetName') is not None:
            self.policy_set_name = m.get('PolicySetName')
        return self


class UpdatePolicyResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
    ):
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class UpdatePolicyResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: UpdatePolicyResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = UpdatePolicyResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class UpdatePolicySetRequest(TeaModel):
    def __init__(
        self,
        description: str = None,
        policy_set_name: str = None,
    ):
        self.description = description
        self.policy_set_name = policy_set_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.description is not None:
            result['Description'] = self.description
        if self.policy_set_name is not None:
            result['PolicySetName'] = self.policy_set_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('PolicySetName') is not None:
            self.policy_set_name = m.get('PolicySetName')
        return self


class UpdatePolicySetResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
    ):
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class UpdatePolicySetResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: UpdatePolicySetResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = UpdatePolicySetResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class UpdateRoleRequest(TeaModel):
    def __init__(
        self,
        description: str = None,
        role_name: str = None,
        user_pool_name: str = None,
    ):
        self.description = description
        self.role_name = role_name
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.description is not None:
            result['Description'] = self.description
        if self.role_name is not None:
            result['RoleName'] = self.role_name
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('RoleName') is not None:
            self.role_name = m.get('RoleName')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class UpdateRoleResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
    ):
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class UpdateRoleResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: UpdateRoleResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = UpdateRoleResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class UpdateTokenVaultRequest(TeaModel):
    def __init__(
        self,
        description: str = None,
        role_arn: str = None,
        token_vault_name: str = None,
    ):
        self.description = description
        self.role_arn = role_arn
        self.token_vault_name = token_vault_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.description is not None:
            result['Description'] = self.description
        if self.role_arn is not None:
            result['RoleArn'] = self.role_arn
        if self.token_vault_name is not None:
            result['TokenVaultName'] = self.token_vault_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('RoleArn') is not None:
            self.role_arn = m.get('RoleArn')
        if m.get('TokenVaultName') is not None:
            self.token_vault_name = m.get('TokenVaultName')
        return self


class UpdateTokenVaultResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
    ):
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class UpdateTokenVaultResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: UpdateTokenVaultResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = UpdateTokenVaultResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class UpdateUserPoolRequest(TeaModel):
    def __init__(
        self,
        description: str = None,
        user_pool_name: str = None,
    ):
        self.description = description
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.description is not None:
            result['Description'] = self.description
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class UpdateUserPoolResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
    ):
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class UpdateUserPoolResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: UpdateUserPoolResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = UpdateUserPoolResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class UpdateUserPoolClientRequest(TeaModel):
    def __init__(
        self,
        access_token_validity: str = None,
        client_name: str = None,
        enforce_pkce: bool = None,
        redirect_uris: str = None,
        refresh_token_validity: str = None,
        secret_required: bool = None,
        user_pool_name: str = None,
    ):
        self.access_token_validity = access_token_validity
        self.client_name = client_name
        self.enforce_pkce = enforce_pkce
        self.redirect_uris = redirect_uris
        self.refresh_token_validity = refresh_token_validity
        self.secret_required = secret_required
        self.user_pool_name = user_pool_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.access_token_validity is not None:
            result['AccessTokenValidity'] = self.access_token_validity
        if self.client_name is not None:
            result['ClientName'] = self.client_name
        if self.enforce_pkce is not None:
            result['EnforcePKCE'] = self.enforce_pkce
        if self.redirect_uris is not None:
            result['RedirectURIs'] = self.redirect_uris
        if self.refresh_token_validity is not None:
            result['RefreshTokenValidity'] = self.refresh_token_validity
        if self.secret_required is not None:
            result['SecretRequired'] = self.secret_required
        if self.user_pool_name is not None:
            result['UserPoolName'] = self.user_pool_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AccessTokenValidity') is not None:
            self.access_token_validity = m.get('AccessTokenValidity')
        if m.get('ClientName') is not None:
            self.client_name = m.get('ClientName')
        if m.get('EnforcePKCE') is not None:
            self.enforce_pkce = m.get('EnforcePKCE')
        if m.get('RedirectURIs') is not None:
            self.redirect_uris = m.get('RedirectURIs')
        if m.get('RefreshTokenValidity') is not None:
            self.refresh_token_validity = m.get('RefreshTokenValidity')
        if m.get('SecretRequired') is not None:
            self.secret_required = m.get('SecretRequired')
        if m.get('UserPoolName') is not None:
            self.user_pool_name = m.get('UserPoolName')
        return self


class UpdateUserPoolClientResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
    ):
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class UpdateUserPoolClientResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: UpdateUserPoolClientResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = UpdateUserPoolClientResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class UpdateWorkloadIdentityRequest(TeaModel):
    def __init__(
        self,
        allowed_resource_oauth_2return_urls: List[str] = None,
        description: str = None,
        identity_provider_name: str = None,
        role_arn: str = None,
        workload_identity_name: str = None,
    ):
        self.allowed_resource_oauth_2return_urls = allowed_resource_oauth_2return_urls
        self.description = description
        self.identity_provider_name = identity_provider_name
        self.role_arn = role_arn
        self.workload_identity_name = workload_identity_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.allowed_resource_oauth_2return_urls is not None:
            result['AllowedResourceOAuth2ReturnURLs'] = self.allowed_resource_oauth_2return_urls
        if self.description is not None:
            result['Description'] = self.description
        if self.identity_provider_name is not None:
            result['IdentityProviderName'] = self.identity_provider_name
        if self.role_arn is not None:
            result['RoleArn'] = self.role_arn
        if self.workload_identity_name is not None:
            result['WorkloadIdentityName'] = self.workload_identity_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AllowedResourceOAuth2ReturnURLs') is not None:
            self.allowed_resource_oauth_2return_urls = m.get('AllowedResourceOAuth2ReturnURLs')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('IdentityProviderName') is not None:
            self.identity_provider_name = m.get('IdentityProviderName')
        if m.get('RoleArn') is not None:
            self.role_arn = m.get('RoleArn')
        if m.get('WorkloadIdentityName') is not None:
            self.workload_identity_name = m.get('WorkloadIdentityName')
        return self


class UpdateWorkloadIdentityShrinkRequest(TeaModel):
    def __init__(
        self,
        allowed_resource_oauth_2return_urls_shrink: str = None,
        description: str = None,
        identity_provider_name: str = None,
        role_arn: str = None,
        workload_identity_name: str = None,
    ):
        self.allowed_resource_oauth_2return_urls_shrink = allowed_resource_oauth_2return_urls_shrink
        self.description = description
        self.identity_provider_name = identity_provider_name
        self.role_arn = role_arn
        self.workload_identity_name = workload_identity_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.allowed_resource_oauth_2return_urls_shrink is not None:
            result['AllowedResourceOAuth2ReturnURLs'] = self.allowed_resource_oauth_2return_urls_shrink
        if self.description is not None:
            result['Description'] = self.description
        if self.identity_provider_name is not None:
            result['IdentityProviderName'] = self.identity_provider_name
        if self.role_arn is not None:
            result['RoleArn'] = self.role_arn
        if self.workload_identity_name is not None:
            result['WorkloadIdentityName'] = self.workload_identity_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AllowedResourceOAuth2ReturnURLs') is not None:
            self.allowed_resource_oauth_2return_urls_shrink = m.get('AllowedResourceOAuth2ReturnURLs')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('IdentityProviderName') is not None:
            self.identity_provider_name = m.get('IdentityProviderName')
        if m.get('RoleArn') is not None:
            self.role_arn = m.get('RoleArn')
        if m.get('WorkloadIdentityName') is not None:
            self.workload_identity_name = m.get('WorkloadIdentityName')
        return self


class UpdateWorkloadIdentityResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
    ):
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class UpdateWorkloadIdentityResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: UpdateWorkloadIdentityResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = UpdateWorkloadIdentityResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


