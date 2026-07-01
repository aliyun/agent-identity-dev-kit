import json
import importlib
import importlib.util
import logging
import os
import random
import shutil
import string
import subprocess
import uuid
from pathlib import Path

from agent_identity_cli import CreateWorkloadIdentityConfig, create_workload_identity
from agent_identity_python_sdk.core import IdentityClient
from agent_identity_python_sdk.core.decorators import get_region
from agent_identity_python_sdk.utils.config import write_local_config
from alibabacloud_agentidentity20250901 import models as agentidentity_models
from alibabacloud_agentidentity20250901_inner.client import Client as InnerControlClient
from alibabacloud_agentidentity20250901_inner import models as inner_models
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_ims20190815.client import Client as ImsClient
from alibabacloud_ims20190815.models import CreateApplicationRequest
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_openapi.exceptions import ClientException

from application.backend.config import get_app_config_with_default
from deploy_starter.tools.context.config import get_config_with_default
from scripts.setup_ai_gateway import run_ai_gateway_setup

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def ui_section(title: str) -> None:
    logger.info("")
    logger.info("================================================================")
    logger.info("[SECTION] %s", title)
    logger.info("================================================================")


def ui_step(title: str) -> None:
    logger.info("[STEP] %s", title)


def ui_ok(message: str) -> None:
    logger.info("[OK] %s", message)


def ui_warn(message: str) -> None:
    logger.warning("[WARN] %s", message)


def ui_fail(message: str) -> None:
    logger.error("[FAIL] %s", message)


REGION = get_region()
OAUTH_REDIRECT_URI_FOR_CONFIRM = f"{get_config_with_default('APP_REDIRECT_URI', 'http://localhost:8090')}/callback"
OAUTH_REDIRECT_URI_FOR_INBOUND = get_app_config_with_default('INBOUND_REDIRECT_URI', 'http://localhost:8090')
DASHSCOPE_API_KEY = get_app_config_with_default('DASHSCOPE_API_KEY', 'mock')

INBOUND_APP_NAME = f"aliyun-inbound-{uuid.uuid4()}"
INBOUND_PROVIDER_NAME = "test-provider"
MCP_APP_NAME = f"aliyun-mcp-{uuid.uuid4()}"
PROTOCOL_VERSION = "2.1"
OAUTH2_CREDENTIAL_PROVIDER_NAME = "test-provider-for-mcp-oauth"
API_KEY_CREDENTIAL_PROVIDER_NAME = "test-provider-api-key"
DISCOVERY_URL = "https://oauth.aliyun.com/.well-known/openid-configuration"

client = None
inner_control_client = None
ims_client = None





def sdk_capabilities() -> dict[str, object]:
    methods = [m for m in dir(client.control_client) if not m.startswith("_")]
    inner_methods = [m for m in dir(inner_control_client) if not m.startswith("_")]
    return {
        "control_method_count": len(methods),
        "supports_policy_set": "create_policy_set" in inner_methods and "attach_policy_set_to_gateway" in inner_methods,
    }


def ensure_aliyun_cli() -> str:
    """Check aliyun cli via `aliyun version`, install by bash if missing."""
    try:
        subprocess.run(["aliyun", "version"], check=True, capture_output=True, text=True)
        return "aliyun"
    except Exception:
        logger.info("aliyun CLI not found, installing via official bash script.")
        install_cmd = '/bin/bash -c "$(curl -fsSL https://aliyuncli.alicdn.com/install.sh)"'
        result = subprocess.run(install_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            # Fallback: user-local install without sudo.
            logger.warning("Official installer failed, fallback to user-local install. stderr=%s", result.stderr.strip())
            local_bin = Path.home() / ".local" / "bin"
            local_bin.mkdir(parents=True, exist_ok=True)
            local_cmd = (
                f'mkdir -p "{local_bin}" && cd "{local_bin}" && '
                "curl -fsSL -o aliyun-cli-macosx-latest-universal.tgz "
                "https://aliyuncli.alicdn.com/aliyun-cli-macosx-latest-universal.tgz && "
                "tar zxf aliyun-cli-macosx-latest-universal.tgz && chmod +x aliyun"
            )
            subprocess.run(local_cmd, shell=True, check=True)
            os.environ["PATH"] = f"{local_bin}:{os.environ.get('PATH', '')}"

    subprocess.run(["aliyun", "version"], check=True, capture_output=True, text=True)
    return "aliyun"


def aliyun_cli_json(cli_bin: str, args: list[str], access_key_id: str, access_key_secret: str) -> dict:
    cmd = [
        cli_bin,
        *args,
        "--region",
        REGION,
        "--access-key-id",
        access_key_id,
        "--access-key-secret",
        access_key_secret,
    ]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as error:
        stderr = (error.stderr or "").strip()
        stdout = (error.stdout or "").strip()
        raise RuntimeError(
            f"Aliyun CLI command failed: {' '.join(cmd)}\nstdout: {stdout}\nstderr: {stderr}"
        ) from error

    body = result.stdout.strip() or "{}"
    try:
        return json.loads(body)
    except json.JSONDecodeError as error:
        # Some CLI versions may include non-JSON prefix/suffix in stdout.
        start = body.find("{")
        end = body.rfind("}")
        if start != -1 and end != -1 and end >= start:
            return json.loads(body[start : end + 1])
        raise RuntimeError(f"Aliyun CLI returned non-JSON output: {body}") from error


def init_clients():
    global client, inner_control_client, ims_client
    client = IdentityClient(REGION)
    credential = CredentialClient()
    ims_client = ImsClient(config=open_api_models.Config(credential=credential))
    inner_control_client = InnerControlClient(config=open_api_models.Config(
        credential=credential,
        region_id=REGION,
        endpoint=f"agentidentity.{REGION}.aliyuncs.com"
    ))


def extract_role_name(role_arn: str) -> str:
    if not role_arn or "/" not in role_arn:
        raise ValueError(f"Invalid role ARN: {role_arn}")
    return role_arn.rsplit("/", 1)[-1]


def create_prepare_ram_user_with_cli(cli_bin: str, admin_ak: str, admin_sk: str) -> tuple[str, str, str]:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    user_name = f"agent-identity-{suffix}"
    policy_name = f"agent-identity-prepare-{suffix}"

    aliyun_cli_json(
        cli_bin,
        ["ram", "CreateUser", "--UserName", user_name, "--Comments", "Auto generated by prepare.py"],
        admin_ak,
        admin_sk,
    )
    access_key_resp = aliyun_cli_json(
        cli_bin,
        ["ram", "CreateAccessKey", "--UserName", user_name],
        admin_ak,
        admin_sk,
    )
    policy_doc = {
        "Version": "1",
        "Statement": [
            {"Effect": "Allow", "Action": "agentidentity:*", "Resource": "*"},
            {"Effect": "Allow", "Action": "agentidentitydata:*", "Resource": "*"},
            {
                "Effect": "Allow",
                "Action": "ram:CreateServiceLinkedRole",
                "Resource": "*",
                "Condition": {"StringEquals": {"ram:ServiceName": ["agentidentity.aliyuncs.com"]}},
            },
            {
                "Effect": "Allow",
                "Action": [
                    "ram:CreateApplication",
                    "ram:CreateRole",
                    "ram:CreatePolicy",
                    "ram:AttachPolicyToRole",
                    "ram:CreateAppSecret",
                    "ram:DeleteApplication",
                ],
                "Resource": "*",
            },
        ],
    }
    aliyun_cli_json(
        cli_bin,
        ["ram", "CreatePolicy", "--PolicyName", policy_name, "--PolicyDocument", json.dumps(policy_doc)],
        admin_ak,
        admin_sk,
    )
    aliyun_cli_json(
        cli_bin,
        ["ram", "AttachPolicyToUser", "--PolicyType", "Custom", "--PolicyName", policy_name, "--UserName", user_name],
        admin_ak,
        admin_sk,
    )

    key_info = access_key_resp.get("AccessKey", {})
    return user_name, key_info.get("AccessKeyId"), key_info.get("AccessKeySecret")


def attach_role_policies_with_cli(cli_bin: str, admin_ak: str, admin_sk: str, role_name: str):
    for policy_name in ["AliyunOSSFullAccess", "AliyunAgentIdentityDataFullAccess"]:
        try:
            aliyun_cli_json(
                cli_bin,
                ["ram", "AttachPolicyToRole", "--PolicyType", "System", "--PolicyName", policy_name, "--RoleName", role_name],
                admin_ak,
                admin_sk,
            )
        except subprocess.CalledProcessError as error:
            text = (error.stderr or "") + (error.stdout or "")
            if "EntityAlreadyExists" in text:
                logger.info("Policy %s already attached to role %s", policy_name, role_name)
                continue
            raise

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
    create_identity_provider_request = agentidentity_models.CreateIdentityProviderRequest(
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
            logger.warning('[409] IdentityProvider already exists, deleting and recreating: %s', INBOUND_PROVIDER_NAME)
            delete_workload_identities_for_provider(INBOUND_PROVIDER_NAME)
            delete_identity_provider_if_exists(INBOUND_PROVIDER_NAME)
            response = client.control_client.create_identity_provider(request=create_identity_provider_request)
            logger.info(f'Identity provider: {response.body.identity_provider.identity_provider_name} recreated.')
            return response.body.identity_provider.identity_provider_name
        else:
            raise


def delete_workload_identities_for_provider(identity_provider_name: str) -> None:
    next_token = None
    while True:
        response = client.control_client.list_workload_identities(
            request=agentidentity_models.ListWorkloadIdentitiesRequest(next_token=next_token)
        )
        for identity in response.body.workload_identities or []:
            if identity.identity_provider_name != identity_provider_name:
                continue
            logger.info("Deleting stale workload identity before provider recreation: %s", identity.workload_identity_name)
            client.control_client.delete_workload_identity(
                request=agentidentity_models.DeleteWorkloadIdentityRequest(
                    workload_identity_name=identity.workload_identity_name
                )
            )
        if response.body.next_token is None:
            break
        next_token = response.body.next_token


def delete_identity_provider_if_exists(name: str) -> None:
    try:
        client.control_client.delete_identity_provider(
            request=agentidentity_models.DeleteIdentityProviderRequest(identity_provider_name=name)
        )
    except ClientException as error:
        if error.code != "EntityNotExists.IdentityProvider":
            raise


def delete_oauth2_credential_provider_if_exists(name: str) -> None:
    delete_method = getattr(client.control_client, "delete_oauth2_credential_provider", None)
    if delete_method is None:
        delete_method = getattr(client.control_client, "delete_oauth_2credential_provider", None)
    if delete_method is None:
        raise RuntimeError("AgentIdentity SDK does not expose OAuth2 credential provider delete API.")
    try:
        delete_method(
            request=agentidentity_models.DeleteOAuth2CredentialProviderRequest(
                oauth2_credential_provider_name=name
            )
        )
    except ClientException as error:
        if error.code != "EntityNotExists.OAuth2CredentialProvider":
            raise


def delete_api_key_credential_provider_if_exists(name: str) -> None:
    try:
        client.control_client.delete_apikey_credential_provider(
            request=agentidentity_models.DeleteAPIKeyCredentialProviderRequest(
                apikey_credential_provider_name=name
            )
        )
    except ClientException as error:
        if error.code != "EntityNotExists.APIKeyCredentialProvider":
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
    config = agentidentity_models.OAuth2ProviderConfig(
        included_oauth2_provider_config=agentidentity_models.IncludedOAuth2ProviderConfig(client_id=app_id),
    )
    try:
        create_method = getattr(client.control_client, "create_oauth2_credential_provider", None)
        if create_method is None:
            create_method = getattr(client.control_client, "create_oauth_2credential_provider", None)
        if create_method is None:
            raise RuntimeError("AgentIdentity SDK does not expose OAuth2 credential provider create API.")

        response = create_method(
            request=agentidentity_models.CreateOAuth2CredentialProviderRequest(
                oauth2_credential_provider_name=OAUTH2_CREDENTIAL_PROVIDER_NAME,
                credential_provider_vendor='AliyunOAuth2',
                oauth2_provider_config=config,
                description='This is a OAuth2 credential provider for alibaba cloud mcp server.',
                callback_url=callback_url,
            )
        )
        logger.info(f'OAuth2 credential provider: {response.body.oauth2_credential_provider.oauth2_credential_provider_name} created.')
        return response.body.oauth2_credential_provider.oauth2_credential_provider_name
    except AttributeError as error:
        logger.warning("Skip OAuth2 credential provider due to SDK field mismatch: %s", error)
        return "skipped_due_sdk_mismatch"
    except ClientException as error:
        if error.code == 'EntityAlreadyExists.OAuth2CredentialProvider':
            logger.warning('[409] OAuth2CredentialProvider already exists, deleting and recreating: %s', OAUTH2_CREDENTIAL_PROVIDER_NAME)
            delete_oauth2_credential_provider_if_exists(OAUTH2_CREDENTIAL_PROVIDER_NAME)
            response = create_method(
                request=agentidentity_models.CreateOAuth2CredentialProviderRequest(
                    oauth2_credential_provider_name=OAUTH2_CREDENTIAL_PROVIDER_NAME,
                    credential_provider_vendor='AliyunOAuth2',
                    oauth2_provider_config=config,
                    description='This is a OAuth2 credential provider for alibaba cloud mcp server.',
                    callback_url=callback_url,
                )
            )
            logger.info(f'OAuth2 credential provider: {response.body.oauth2_credential_provider.oauth2_credential_provider_name} recreated.')
            return response.body.oauth2_credential_provider.oauth2_credential_provider_name
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
            agentidentity_models.CreateAPIKeyCredentialProviderRequest(
                apikey_credential_provider_name=API_KEY_CREDENTIAL_PROVIDER_NAME,
                description='This is a test API key provider.',
                apikey=DASHSCOPE_API_KEY
            )
        )
        logger.info(f'API key credential provider: {response.body.apikey_credential_provider.apikey_credential_provider_name} created.')
        return response.body.apikey_credential_provider.apikey_credential_provider_name
    except AttributeError as error:
        logger.warning("Skip API key credential provider due to SDK field mismatch: %s", error)
        return "skipped_due_sdk_mismatch"
    except ClientException as error:
        if error.code == 'EntityAlreadyExists.APIKeyCredentialProvider':
            logger.warning('[409] APIKeyCredentialProvider already exists, deleting and recreating: %s', API_KEY_CREDENTIAL_PROVIDER_NAME)
            delete_api_key_credential_provider_if_exists(API_KEY_CREDENTIAL_PROVIDER_NAME)
            response = client.control_client.create_apikey_credential_provider(
                agentidentity_models.CreateAPIKeyCredentialProviderRequest(
                    apikey_credential_provider_name=API_KEY_CREDENTIAL_PROVIDER_NAME,
                    description='This is a test API key provider.',
                    apikey=DASHSCOPE_API_KEY
                )
            )
            logger.info(f'API key credential provider: {response.body.apikey_credential_provider.apikey_credential_provider_name} recreated.')
            return response.body.apikey_credential_provider.apikey_credential_provider_name
        else:
            raise


def run_agentidentity_policy_set_setup() -> dict[str, object]:
    """
    Optional 1.3 AgentIdentity PolicySet automation.

    Controlled by env vars:
      - ENABLE_AGENTIDENTITY_POLICYSET_SETUP=<true by default, set false to disable>
      - AGENTIDENTITY_POLICY_SET_NAME=<required when enabled>
      - AGENTIDENTITY_POLICY_SET_DESCRIPTION=<optional>
      - AGENTIDENTITY_GATEWAY_ARN=<optional, attach when provided>
      - AGENTIDENTITY_ENFORCEMENT_MODE=<optional, default ENFORCE>
      - AGENTIDENTITY_POLICY_NAME=<optional, create policy when provided with statement>
      - AGENTIDENTITY_POLICY_DESCRIPTION=<optional>
      - AGENTIDENTITY_POLICY_CEDAR_STATEMENT=<optional, cedar statement text>
    """
    enabled = str(os.getenv("ENABLE_AGENTIDENTITY_POLICYSET_SETUP", "true")).strip().lower() in {"1", "true", "yes", "on"}
    if not enabled:
        return {"enabled": False}

    caps = sdk_capabilities()
    if not caps["supports_policy_set"]:
        logger.warning(
            "PolicySet setup skipped: current SDK does not expose PolicySet APIs. "
            "This is expected in some temporary SDK builds."
        )
        return {
            "enabled": False,
            "skipped": True,
            "reason": "sdk_policy_set_api_not_available",
        }

    model_module = inner_models
    create_policy_set_request_cls = getattr(model_module, "CreatePolicySetRequest", None)
    attach_policy_set_request_cls = getattr(model_module, "AttachPolicySetToGatewayRequest", None)
    create_policy_request_cls = getattr(model_module, "CreatePolicyRequest", None)
    definition_cls = getattr(model_module, "Definition", None)
    definition_cedar_cls = getattr(model_module, "DefinitionCedar", None)
    if not create_policy_set_request_cls or not attach_policy_set_request_cls:
        logger.warning(
            "PolicySet setup skipped: PolicySet request models are not available in current SDK package."
        )
        return {
            "enabled": False,
            "skipped": True,
            "reason": "sdk_policy_set_models_not_available",
        }

    policy_set_name = str(os.getenv("AGENTIDENTITY_POLICY_SET_NAME", "")).strip()
    if not policy_set_name:
        policy_set_name = f"ps-auto-{uuid.uuid4().hex[:8]}"

    policy_set_description = str(os.getenv("AGENTIDENTITY_POLICY_SET_DESCRIPTION", "Created by prepare.py")).strip()
    create_resp = inner_control_client.create_policy_set(
        request=create_policy_set_request_cls(
            policy_set_name=policy_set_name,
            description=policy_set_description,
        )
    )
    policy_set_arn = None
    if getattr(create_resp, "body", None) and getattr(create_resp.body, "policy_set", None):
        policy_set_arn = getattr(create_resp.body.policy_set, "policy_set_arn", None)
    logger.info("PolicySet created: %s", policy_set_name)

    policy_name = str(os.getenv("AGENTIDENTITY_POLICY_NAME", "")).strip()
    policy_cedar_statement = os.getenv("AGENTIDENTITY_POLICY_CEDAR_STATEMENT")
    auto_create_policy = str(os.getenv("AGENTIDENTITY_AUTO_CREATE_POLICY", "true")).strip().lower() in {"1", "true", "yes", "on"}
    if auto_create_policy and not policy_name:
        policy_name = f"policy-auto-{uuid.uuid4().hex[:8]}"
    if auto_create_policy and not policy_cedar_statement:
        # 1.3 default: deny all first, then user can update policy content later.
        policy_cedar_statement = "forbid (principal, action, resource);"
    if policy_name and policy_cedar_statement:
        if not create_policy_request_cls or not definition_cls or not definition_cedar_cls:
            raise RuntimeError("CreatePolicyRequest/Definition models are not available in current SDK package.")
        try:
            inner_control_client.create_policy(
                request=create_policy_request_cls(
                    policy_name=policy_name,
                    policy_set_name=policy_set_name,
                    description=str(os.getenv("AGENTIDENTITY_POLICY_DESCRIPTION", "Created by prepare.py")).strip(),
                    definition=definition_cls(
                        cedar=definition_cedar_cls(
                            statement=policy_cedar_statement,
                        )
                    ),
                )
            )
            logger.info("Policy created: %s", policy_name)
        except ClientException as error:
            if error.code != "EntityAlreadyExists.Policy":
                raise
            logger.warning("Policy already exists, skip creating: %s", policy_name)

    attached_gateways = None
    gateway_policy_config = None
    gateway_arn = str(os.getenv("AGENTIDENTITY_GATEWAY_ARN", "")).strip()
    if gateway_arn:
        raw_mode = str(os.getenv("AGENTIDENTITY_ENFORCEMENT_MODE", "ENFORCE")).strip()
        enforcement_alias = {
            "enforcing": "ENFORCE",
            "enforce": "ENFORCE",
            "ENFORCING": "ENFORCE",
            "ENFORCE": "ENFORCE",
        }
        enforcement_mode = enforcement_alias.get(raw_mode, enforcement_alias.get(raw_mode.lower(), raw_mode))
        try:
            inner_control_client.attach_policy_set_to_gateway(
                request=attach_policy_set_request_cls(
                    policy_set_name=policy_set_name,
                    gateway_arn=gateway_arn,
                    enforcement_mode=enforcement_mode,
                )
            )
            logger.info("PolicySet %s attached to gateway %s", policy_set_name, gateway_arn)
        except ClientException as error:
            if error.code != "GatewayAlreadyAttached":
                raise
            logger.warning(
                "Gateway already attached to another PolicySet, continue with verification. request_id=%s",
                getattr(error, "request_id", None),
            )

        # Best-effort verification to avoid false negatives from field mismatch/parsing issues.
        list_attached_request_cls = getattr(model_module, "ListPolicySetAttachedGatewaysRequest", None)
        get_gateway_policy_config_request_cls = getattr(model_module, "GetGatewayPolicyConfigRequest", None)
        if list_attached_request_cls and hasattr(inner_control_client, "list_policy_set_attached_gateways"):
            list_resp = inner_control_client.list_policy_set_attached_gateways(
                request=list_attached_request_cls(policy_set_name=policy_set_name)
            )
            if getattr(list_resp, "body", None) and hasattr(list_resp.body, "to_map"):
                attached_gateways = list_resp.body.to_map().get("AttachedGateways")
        if get_gateway_policy_config_request_cls and hasattr(inner_control_client, "get_gateway_policy_config"):
            cfg_resp = inner_control_client.get_gateway_policy_config(
                request=get_gateway_policy_config_request_cls(gateway_arn=gateway_arn)
            )
            if getattr(cfg_resp, "body", None) and hasattr(cfg_resp.body, "to_map"):
                gateway_policy_config = cfg_resp.body.to_map().get("GatewayPolicyConfig")

    return {
        "enabled": True,
        "policy_set_name": policy_set_name,
        "policy_set_arn": policy_set_arn,
        "policy_name": policy_name or None,
        "attached_gateway_arn": gateway_arn or None,
        "enforcement_mode": enforcement_mode if gateway_arn else None,
        "attached_gateways": attached_gateways,
        "gateway_policy_config": gateway_policy_config,
    }


def persist_ai_gateway_cleanup_config(ai_gateway_summary: dict[str, object] | None,
                                      policy_set_summary: dict[str, object] | None) -> None:
    """Persist resource IDs needed by the one-click cleanup script."""
    if ai_gateway_summary:
        network = ai_gateway_summary.get("network_prerequisites") or {}
        vpc = network.get("vpc") if isinstance(network, dict) else {}
        v_switches = network.get("v_switches") if isinstance(network, dict) else {}
        created_vswitches = v_switches.get("created") if isinstance(v_switches, dict) else []

        cleanup_fields = {
            "apig_gateway_id": ai_gateway_summary.get("gateway_id"),
            "apig_mcp_server_id": ai_gateway_summary.get("mcp_server_id"),
            "apig_policy_id": ai_gateway_summary.get("policy_id"),
            "apig_policy_attachment_id": ai_gateway_summary.get("policy_attachment_id"),
            "apig_plugin_id": ai_gateway_summary.get("plugin_id"),
            "apig_plugin_attachment_id": ai_gateway_summary.get("plugin_attachment_id"),
            "apig_service_id": ai_gateway_summary.get("service_id"),
            "apig_domain_id": ai_gateway_summary.get("domain_id"),
            "apig_vpc_id": vpc.get("vpc_id") if isinstance(vpc, dict) and vpc.get("action") == "create" else None,
            "apig_vswitch_ids": [
                item.get("vswitch_id")
                for item in created_vswitches
                if isinstance(item, dict) and item.get("vswitch_id")
            ],
        }
        for key, value in cleanup_fields.items():
            if value:
                write_local_config(key, value)

    if policy_set_summary:
        policy_set_name = policy_set_summary.get("policy_set_name")
        policy_name = policy_set_summary.get("policy_name")
        gateway_arn = policy_set_summary.get("attached_gateway_arn")
        if policy_set_name:
            write_local_config("agentidentity_policy_set_name", policy_set_name)
        if policy_name:
            write_local_config("agentidentity_policy_name", policy_name)
        if gateway_arn:
            write_local_config("agentidentity_gateway_arn", gateway_arn)


if __name__ == '__main__':
    try:
        ui_section("Alibaba Cloud Demo Bootstrap")
        ui_step("Checking required inputs")
        cli_bin = ensure_aliyun_cli()
        admin_access_key_id = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
        admin_access_key_secret = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
        if not admin_access_key_id or not admin_access_key_secret:
            raise RuntimeError("Missing required env vars: ALIBABA_CLOUD_ACCESS_KEY_ID and ALIBABA_CLOUD_ACCESS_KEY_SECRET.")
        ui_ok("Input validation passed")

        ui_step("Creating dedicated RAM user for automation")
        ram_user_name, ram_user_ak, ram_user_sk = create_prepare_ram_user_with_cli(
            cli_bin=cli_bin,
            admin_ak=admin_access_key_id,
            admin_sk=admin_access_key_secret,
        )
        if not ram_user_ak or not ram_user_sk:
            raise RuntimeError("Failed to create access key for generated RAM user.")
        os.environ["ALIBABA_CLOUD_ACCESS_KEY_ID"] = ram_user_ak
        os.environ["ALIBABA_CLOUD_ACCESS_KEY_SECRET"] = ram_user_sk
        write_local_config("provisioned_ram_user_name", ram_user_name)
        write_local_config("provisioned_ram_access_key_id", ram_user_ak)
        logger.info("Created RAM user via aliyun CLI: %s", ram_user_name)
        logger.info("export ALIBABA_CLOUD_ACCESS_KEY_ID=%s", ram_user_ak)
        logger.info("export ALIBABA_CLOUD_ACCESS_KEY_SECRET=%s", ram_user_sk)
        ui_ok("RAM bootstrap credentials are ready")

        ui_step("Initializing SDK clients")
        init_clients()
        caps = sdk_capabilities()
        logger.info("AgentIdentity SDK capability: methods=%s, supports_policy_set=%s", caps["control_method_count"], caps["supports_policy_set"])
        ui_ok("SDK clients initialized")

        ui_section("Provision Core Identity Resources")
        ui_step("Creating inbound application")
        inbound_app_id, inbound_app_name, inbound_callback_url = create_mcp_application(
            app_name=INBOUND_APP_NAME,
            app_type='WebApp',
            predefined_scopes='aliuid;profile;openid',
            redirect_uris=OAUTH_REDIRECT_URI_FOR_INBOUND,
            protocol_version='2.1',
        )
        ui_ok("Inbound application created")

        ui_step("Creating MCP application")
        mcp_app_id, mcp_app_name, mcp_callback_url = create_mcp_application(
            app_name=MCP_APP_NAME,
            app_type='NativeApp',
            predefined_scopes='aliuid;profile;openid;/acs/mcp-server',
            redirect_uris=f'https://agentidentitydata.{REGION}.aliyuncs.com/oauth2/callback/{uuid.uuid4()}',
            protocol_version='2.1',
        )
        ui_ok("MCP application created")

        ui_step("Creating identity provider, workload identity, and providers")
        identity_provider_name = create_identity_provider(inbound_app_id)
        workload_identity_name, role_arn = create_role_and_workload_identity(OAUTH_REDIRECT_URI_FOR_CONFIRM)
        oauth_credential_provider_name = create_oauth2_credential_provider(app_id=mcp_app_id, callback_url=mcp_callback_url)
        api_key_provider_name = create_api_key_provider()
        role_name = extract_role_name(role_arn)
        attach_role_policies_with_cli(
            cli_bin=cli_bin,
            admin_ak=admin_access_key_id,
            admin_sk=admin_access_key_secret,
            role_name=role_name,
        )
        logger.info(
            "Attached policies via aliyun CLI to role %s: AliyunOSSFullAccess, AliyunAgentIdentityDataFullAccess",
            role_name,
        )
        ui_ok("Core identity resources are ready")

        ui_section("AI Gateway / PolicySet Setup")
        ai_gateway_summary = None
        agentidentity_policy_set_summary = None
        ai_enabled = str(os.getenv("ENABLE_AI_GATEWAY_SETUP", "true")).strip().lower() in {"1", "true", "yes", "on"}
        policy_set_enabled = str(os.getenv("ENABLE_AGENTIDENTITY_POLICYSET_SETUP", "true")).strip().lower() in {"1", "true", "yes", "on"}
        if ai_enabled and policy_set_enabled:
            try:
                # Correct order per APIG console flow:
                # 1) CreateGateway + wait Running
                # 2) CreateService -> GetService -> CreatePolicy -> CreatePolicyAttachment
                #    -> InstallPlugin -> CreatePluginAttachment
                # 3) AttachPolicySetToGateway (must be AFTER plugin attachment)
                ui_step("Running ordered setup: gateway -> APIG resources -> policy set")
                ai_gateway_summary = run_ai_gateway_setup(
                    cli_bin=cli_bin,
                    access_key_id=admin_access_key_id,
                    access_key_secret=admin_access_key_secret,
                    region=REGION,
                )
                gateway_id = ai_gateway_summary.get("gateway_id")
                write_local_config("apig_gateway_id", gateway_id)
                write_local_config("apig_mcp_server_id", ai_gateway_summary.get("mcp_server_id"))
                write_local_config("apig_policy_id", ai_gateway_summary.get("policy_id") or "")

                if not os.getenv("AGENTIDENTITY_GATEWAY_ARN") and gateway_id:
                    from agent_identity_cli.utils.credentials import get_account_id
                    account_id = get_account_id()
                    gateway_arn = f"acs:apig:{REGION}:{account_id}:gateway/{gateway_id}"
                    os.environ["AGENTIDENTITY_GATEWAY_ARN"] = gateway_arn
                    logger.info("Auto-derived AGENTIDENTITY_GATEWAY_ARN from APIG gateway: %s", gateway_arn)

                agentidentity_policy_set_summary = run_agentidentity_policy_set_setup()
                ui_ok("Ordered AI gateway + policy set setup completed")
            except Exception:
                raise
        else:
            if ai_enabled:
                ui_step("Running AI gateway setup")
                ai_gateway_summary = run_ai_gateway_setup(
                    cli_bin=cli_bin,
                    access_key_id=admin_access_key_id,
                    access_key_secret=admin_access_key_secret,
                    region=REGION,
                )
                write_local_config("apig_gateway_id", ai_gateway_summary.get("gateway_id"))
                write_local_config("apig_mcp_server_id", ai_gateway_summary.get("mcp_server_id"))
                write_local_config("apig_policy_id", ai_gateway_summary.get("policy_id"))
                ui_ok("AI gateway setup completed")
            else:
                ui_warn("AI gateway setup skipped because ENABLE_AI_GATEWAY_SETUP is false.")

            if policy_set_enabled:
                ui_step("Running AgentIdentity PolicySet setup")
                agentidentity_policy_set_summary = run_agentidentity_policy_set_setup()
                ui_ok("AgentIdentity PolicySet setup completed")
            else:
                ui_warn("AgentIdentity PolicySet setup skipped because ENABLE_AGENTIDENTITY_POLICYSET_SETUP is false.")

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
        write_local_config('admin_bootstrap_role_name', role_name)
        persist_ai_gateway_cleanup_config(ai_gateway_summary, agentidentity_policy_set_summary)

        ui_section("Execution Summary")
        logger.info("Resources Summary:")
        summary = {
            "cli_bootstrap": {
                "ram_user_name": ram_user_name,
                "export_env": {
                    "ALIBABA_CLOUD_ACCESS_KEY_ID": ram_user_ak,
                    "ALIBABA_CLOUD_ACCESS_KEY_SECRET": ram_user_sk,
                },
            },
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
                "arn": role_arn,
                "attached_system_policies": [
                    "AliyunOSSFullAccess",
                    "AliyunAgentIdentityDataFullAccess",
                ],
            },
            "credential_providers": {
                "oauth2": oauth_credential_provider_name,
                "api_key": api_key_provider_name
            },
            "ai_gateway_setup": ai_gateway_summary or {
                "enabled": False,
                "hint": "Set ENABLE_AI_GATEWAY_SETUP=true (default) and provide APIG_* bodies/IDs to enable."
            },
            "agentidentity_policy_set_setup": agentidentity_policy_set_summary or {
                "enabled": False,
                "hint": "Set ENABLE_AGENTIDENTITY_POLICYSET_SETUP=true (default) and provide AGENTIDENTITY_* inputs to enable."
            },
        }
        logger.info(json.dumps(summary, indent=2, ensure_ascii=False))
        ui_ok("prepare.py finished successfully")
        logger.info("Next step: start local services and open http://localhost:8090")
    except Exception as error:
        ui_fail(str(error))
        logger.error(
            "Preparation failed. Please check the error above and rerun after fixing. "
            "If needed, keep the full log and .config.json for troubleshooting."
        )
        raise
