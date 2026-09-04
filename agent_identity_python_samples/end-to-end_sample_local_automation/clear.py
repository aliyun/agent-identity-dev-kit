import json
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

from agent_identity_python_sdk.core import IdentityClient
from alibabacloud_agentidentity20250901 import models as agentidentity_models
from alibabacloud_agentidentity20250901_inner.client import Client as InnerControlClient
from alibabacloud_agentidentity20250901_inner import models as inner_models
from alibabacloud_apig20240327.client import Client as ApigClient
from alibabacloud_apig20240327 import models as apig_models
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_ims20190815.client import Client as ImsClient
from alibabacloud_ims20190815.models import DeleteApplicationRequest
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_openapi.exceptions import ClientException
from alibabacloud_vpc20160428.client import Client as VpcClient
from alibabacloud_vpc20160428 import models as vpc_models


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = ROOT_DIR / ".config.json"
REGION = os.environ.get("AGENT_IDENTITY_REGION_ID", "cn-beijing")
DRY_RUN = str(os.getenv("CLEAR_DRY_RUN", "")).strip().lower() in {"1", "true", "yes", "on"}


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise RuntimeError(f"{CONFIG_PATH.name} not found. Nothing to clear.")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(config: dict[str, Any]) -> None:
    if DRY_RUN:
        return
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cfg(config: dict[str, Any], key: str) -> str:
    value = config.get(key)
    return value if isinstance(value, str) else ""


def to_map(response: Any) -> dict[str, Any]:
    if response is None or getattr(response, "body", None) is None:
        return {}
    if hasattr(response.body, "to_map"):
        return response.body.to_map()
    return {}


def nested_values(data: Any, keys: set[str]) -> list[str]:
    found: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key in keys and isinstance(value, str) and value:
                found.append(value)
            else:
                found.extend(nested_values(value, keys))
    elif isinstance(data, list):
        for item in data:
            found.extend(nested_values(item, keys))
    return found


def first_nested_value(data: Any, *keys: str) -> str:
    values = nested_values(data, set(keys))
    return values[0] if values else ""


def is_not_found(error: Exception) -> bool:
    code = str(getattr(error, "code", "") or "")
    message = str(getattr(error, "message", "") or error)
    text = f"{code} {message}".lower()
    return any(
        marker in text
        for marker in [
            "gatewaynotattached",
            "is deleted",
            "notfound",
            "not found",
            "notexist",
            "not exists",
            "notexisted",
            "entitynotexists",
            "entitynotexist",
            "resourcenotfound",
        ]
    )


def run_step(name: str, action: Callable[[], Any], required: bool = False) -> bool:
    logger.info("[CLEAR] %s", name)
    if DRY_RUN:
        logger.info("[DRY-RUN] skip %s", name)
        return True
    try:
        action()
        logger.info("[OK] %s", name)
        return True
    except ClientException as error:
        if is_not_found(error):
            logger.warning("[SKIP] %s: resource not found", name)
            return True
        if required:
            logger.error("[FAIL] %s: %s", name, error)
            return False
        logger.warning("[WARN] %s failed: %s", name, error)
        return True
    except Exception as error:
        if is_not_found(error):
            logger.warning("[SKIP] %s: resource not found", name)
            return True
        if required:
            logger.error("[FAIL] %s: %s", name, error)
            return False
        logger.warning("[WARN] %s failed: %s", name, error)
        return True


def run_retry_step(name: str,
                   action: Callable[[], Any],
                   attempts: int = 10,
                   delay_seconds: int = 15,
                   required: bool = True) -> bool:
    for attempt in range(1, attempts + 1):
        logger.info("[CLEAR] %s attempt %s/%s", name, attempt, attempts)
        if DRY_RUN:
            logger.info("[DRY-RUN] skip %s", name)
            return True
        try:
            action()
            logger.info("[OK] %s", name)
            return True
        except ClientException as error:
            if is_not_found(error):
                logger.warning("[SKIP] %s: resource not found", name)
                return True
            if attempt < attempts:
                logger.warning("[WAIT] %s failed, retrying in %ss: %s", name, delay_seconds, error)
                time.sleep(delay_seconds)
                continue
            if required:
                logger.error("[FAIL] %s: %s", name, error)
                return False
            logger.warning("[WARN] %s failed: %s", name, error)
            return True
        except Exception as error:
            if is_not_found(error):
                logger.warning("[SKIP] %s: resource not found", name)
                return True
            if attempt < attempts:
                logger.warning("[WAIT] %s failed, retrying in %ss: %s", name, delay_seconds, error)
                time.sleep(delay_seconds)
                continue
            if required:
                logger.error("[FAIL] %s: %s", name, error)
                return False
            logger.warning("[WARN] %s failed: %s", name, error)
            return True
    return not required


def make_clients():
    access_key_id = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
    access_key_secret = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
    if not access_key_id or not access_key_secret:
        raise RuntimeError("Missing ALIBABA_CLOUD_ACCESS_KEY_ID or ALIBABA_CLOUD_ACCESS_KEY_SECRET.")

    credential = CredentialClient()
    identity_client = IdentityClient(REGION)
    inner_client = InnerControlClient(
        config=open_api_models.Config(
            credential=credential,
            region_id=REGION,
            endpoint=f"agentidentity.{REGION}.aliyuncs.com",
        )
    )
    apig_client = ApigClient(
        open_api_models.Config(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            region_id=REGION,
            endpoint=f"apig.{REGION}.aliyuncs.com",
        )
    )
    vpc_client = VpcClient(
        open_api_models.Config(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            region_id=REGION,
            endpoint=f"vpc.{REGION}.aliyuncs.com",
        )
    )
    ims_client = ImsClient(config=open_api_models.Config(credential=credential))
    return identity_client, inner_client, apig_client, vpc_client, ims_client


def derive_gateway_arn(config: dict[str, Any]) -> str:
    gateway_arn = cfg(config, "agentidentity_gateway_arn")
    if gateway_arn:
        return gateway_arn
    gateway_id = cfg(config, "apig_gateway_id")
    role_arn = cfg(config, "role_arn")
    account_id = ""
    if role_arn.startswith("acs:ram::"):
        account_id = role_arn.split(":")[4]
    if gateway_id and account_id:
        gateway_arn = f"acs:apig:{REGION}:{account_id}:gateway/{gateway_id}"
        config["agentidentity_gateway_arn"] = gateway_arn
        return gateway_arn
    return ""


def resolve_apig_dependencies(config: dict[str, Any], apig_client: ApigClient) -> None:
    mcp_server_id = cfg(config, "apig_mcp_server_id")
    gateway_id = cfg(config, "apig_gateway_id")
    plugin_id = cfg(config, "apig_plugin_id")

    if mcp_server_id:
        try:
            mcp_map = to_map(apig_client.get_mcp_server(mcp_server_id))
            data = mcp_map.get("data") or mcp_map.get("Data") or {}
            if isinstance(data, dict):
                if not cfg(config, "apig_gateway_id"):
                    value = data.get("gatewayId") or data.get("GatewayId")
                    if isinstance(value, str):
                        config["apig_gateway_id"] = value
                        gateway_id = value
                if not cfg(config, "apig_service_id"):
                    service_id = first_nested_value(data, "serviceId", "ServiceId")
                    if service_id:
                        config["apig_service_id"] = service_id
                if not cfg(config, "apig_domain_id"):
                    domain_id = first_nested_value(data, "domainId", "DomainId")
                    if domain_id:
                        config["apig_domain_id"] = domain_id
        except ClientException as error:
            if not is_not_found(error):
                logger.warning("Failed to inspect MCP server %s: %s", mcp_server_id, error)

    if gateway_id and not cfg(config, "apig_plugin_attachment_id"):
        try:
            req = apig_models.ListPluginAttachmentsRequest(
                gateway_id=gateway_id,
                plugin_id=plugin_id or None,
                page_number=1,
                page_size=50,
            )
            items = nested_values(to_map(apig_client.list_plugin_attachments(req)), {"pluginAttachmentId", "PluginAttachmentId"})
            if items:
                config["apig_plugin_attachment_id"] = items[0]
        except ClientException as error:
            if not is_not_found(error):
                logger.warning("Failed to list plugin attachments: %s", error)

    if gateway_id and not cfg(config, "apig_plugin_id"):
        try:
            req = apig_models.ListPluginsRequest(
                gateway_id=gateway_id,
                include_builtin_ai_gateway=True,
                page_number=1,
                page_size=50,
            )
            items = nested_values(to_map(apig_client.list_plugins(req)), {"pluginId", "PluginId"})
            if items:
                config["apig_plugin_id"] = items[0]
        except ClientException as error:
            if not is_not_found(error):
                logger.warning("Failed to list plugins: %s", error)

    if gateway_id and not cfg(config, "apig_policy_attachment_id"):
        try:
            req = apig_models.ListPoliciesRequest(
                gateway_id=gateway_id,
                with_attachments=True,
                with_system_policy=False,
            )
            policy_map = to_map(apig_client.list_policies(req))
            policy_attachment_id = first_nested_value(
                policy_map,
                "policyAttachmentId",
                "PolicyAttachmentId",
                "attachmentId",
                "AttachmentId",
            )
            if policy_attachment_id:
                config["apig_policy_attachment_id"] = policy_attachment_id
        except ClientException as error:
            if not is_not_found(error):
                logger.warning("Failed to list policy attachments: %s", error)


def resolve_policy_set(config: dict[str, Any], inner_client: InnerControlClient) -> None:
    if cfg(config, "agentidentity_policy_set_name"):
        return
    gateway_arn = derive_gateway_arn(config)
    if not gateway_arn:
        return
    try:
        resp = inner_client.get_gateway_policy_config(
            inner_models.GetGatewayPolicyConfigRequest(gateway_arn=gateway_arn)
        )
        body = to_map(resp)
        policy_set_name = first_nested_value(body, "policySetName", "PolicySetName", "policy_set_name")
        if policy_set_name:
            config["agentidentity_policy_set_name"] = policy_set_name
    except Exception as error:
        logger.warning("Failed to inspect gateway policy config: %s", error)


def clear_gateway_binding(config: dict[str, Any],
                          apig_client: ApigClient,
                          inner_client: InnerControlClient) -> bool:
    success = True
    mcp_server_id = cfg(config, "apig_mcp_server_id")
    plugin_attachment_id = cfg(config, "apig_plugin_attachment_id")
    policy_attachment_id = cfg(config, "apig_policy_attachment_id")
    policy_id = cfg(config, "apig_policy_id")
    plugin_id = cfg(config, "apig_plugin_id")
    service_id = cfg(config, "apig_service_id")
    gateway_arn = derive_gateway_arn(config)
    policy_set_name = cfg(config, "agentidentity_policy_set_name")
    policy_name = cfg(config, "agentidentity_policy_name")

    if mcp_server_id:
        success &= run_step("APIG__UnDeployMcpServer", lambda: apig_client.un_deploy_mcp_server(mcp_server_id))
        success &= run_step("APIG__DeleteMcpServer", lambda: apig_client.delete_mcp_server(mcp_server_id), required=True)
    else:
        logger.warning("[SKIP] APIG MCP server id missing")

    if plugin_attachment_id:
        success &= run_step(
            "APIG__DeletePluginAttachment",
            lambda: apig_client.delete_plugin_attachment(plugin_attachment_id),
        )
    else:
        logger.warning("[SKIP] APIG plugin attachment id missing")

    if policy_attachment_id:
        success &= run_step(
            "APIG__DeletePolicyAttachment",
            lambda: apig_client.delete_policy_attachment(policy_attachment_id),
        )
    else:
        logger.warning("[SKIP] APIG policy attachment id missing")

    if policy_id:
        success &= run_step("APIG__DeletePolicy", lambda: apig_client.delete_policy(policy_id))
    else:
        logger.warning("[SKIP] APIG policy id missing")

    if plugin_id:
        success &= run_step("APIG__UninstallPlugin", lambda: apig_client.uninstall_plugin(plugin_id))
    else:
        logger.warning("[SKIP] APIG plugin id missing")

    if service_id:
        success &= run_step("APIG__DeleteService", lambda: apig_client.delete_service(service_id))
    else:
        logger.warning("[SKIP] APIG service id missing")

    if policy_set_name and gateway_arn:
        success &= run_step(
            "agentidentity__DetachPolicySetFromGateway",
            lambda: inner_client.detach_policy_set_from_gateway(
                inner_models.DetachPolicySetFromGatewayRequest(
                    policy_set_name=policy_set_name,
                    gateway_arn=gateway_arn,
                )
            ),
        )
    else:
        logger.warning("[SKIP] AgentIdentity policy set name or gateway ARN missing")

    if policy_set_name and policy_name:
        success &= run_step(
            "agentidentity__DeletePolicy",
            lambda: inner_client.delete_policy(
                inner_models.DeletePolicyRequest(
                    policy_set_name=policy_set_name,
                    policy_name=policy_name,
                )
            ),
        )
    else:
        logger.warning("[SKIP] AgentIdentity policy name or policy set name missing")

    if policy_set_name:
        success &= run_step(
            "agentidentity__DeletePolicySet",
            lambda: inner_client.delete_policy_set(
                inner_models.DeletePolicySetRequest(policy_set_name=policy_set_name)
            ),
            required=True,
        )
    else:
        logger.warning("[SKIP] AgentIdentity policy set name missing")

    return success


def clear_remaining_apig(config: dict[str, Any], apig_client: ApigClient, vpc_client: VpcClient) -> bool:
    success = True
    domain_id = cfg(config, "apig_domain_id")
    gateway_id = cfg(config, "apig_gateway_id")
    vswitch_ids = config.get("apig_vswitch_ids")
    vpc_id = cfg(config, "apig_vpc_id")

    if domain_id:
        success &= run_step("APIG__DeleteDomain", lambda: apig_client.delete_domain(domain_id))
    if gateway_id:
        success &= run_step("APIG__DeleteGateway", lambda: apig_client.delete_gateway(gateway_id), required=True)
    if isinstance(vswitch_ids, list):
        for vswitch_id in vswitch_ids:
            if isinstance(vswitch_id, str) and vswitch_id:
                success &= run_retry_step(
                    f"VPC__DeleteVSwitch({vswitch_id})",
                    lambda value=vswitch_id: vpc_client.delete_vswitch(
                        vpc_models.DeleteVSwitchRequest(region_id=REGION, v_switch_id=value)
                    ),
                    attempts=12,
                    delay_seconds=15,
                )
    if vpc_id:
        success &= run_retry_step(
            "VPC__DeleteVpc",
            lambda: vpc_client.delete_vpc(
                vpc_models.DeleteVpcRequest(region_id=REGION, vpc_id=vpc_id, force_delete=True)
            ),
            attempts=12,
            delay_seconds=15,
        )
    return success


def clear_agent_identity_core(config: dict[str, Any],
                              identity_client: IdentityClient,
                              ims_client: ImsClient) -> None:
    api_key_provider = cfg(config, "api_key_provider_name")
    oauth_provider = cfg(config, "oauth_credential_provider_name")
    workload_identity = cfg(config, "workload_identity_name")
    identity_provider = cfg(config, "identity_provider_name")
    inbound_app_id = cfg(config, "inbound_app_id")
    mcp_app_id = cfg(config, "mcp_app_id")

    if api_key_provider:
        run_step(
            "agentidentity__DeleteAPIKeyCredentialProvider",
            lambda: identity_client.control_client.delete_apikey_credential_provider(
                agentidentity_models.DeleteAPIKeyCredentialProviderRequest(
                    apikey_credential_provider_name=api_key_provider
                )
            ),
        )
    if oauth_provider:
        delete_oauth = getattr(identity_client.control_client, "delete_oauth2_credential_provider", None)
        if delete_oauth is None:
            delete_oauth = getattr(identity_client.control_client, "delete_oauth_2credential_provider")
        run_step(
            "agentidentity__DeleteOAuth2CredentialProvider",
            lambda: delete_oauth(
                agentidentity_models.DeleteOAuth2CredentialProviderRequest(
                    oauth2_credential_provider_name=oauth_provider
                )
            ),
        )
    if workload_identity:
        run_step(
            "agentidentity__DeleteWorkloadIdentity",
            lambda: identity_client.control_client.delete_workload_identity(
                agentidentity_models.DeleteWorkloadIdentityRequest(workload_identity_name=workload_identity)
            ),
        )
    if identity_provider:
        run_step(
            "agentidentity__DeleteIdentityProvider",
            lambda: identity_client.control_client.delete_identity_provider(
                agentidentity_models.DeleteIdentityProviderRequest(identity_provider_name=identity_provider)
            ),
        )
    if inbound_app_id:
        run_step("IMS__DeleteInboundApplication", lambda: ims_client.delete_application(DeleteApplicationRequest(app_id=inbound_app_id)))
    if mcp_app_id:
        run_step("IMS__DeleteMcpApplication", lambda: ims_client.delete_application(DeleteApplicationRequest(app_id=mcp_app_id)))


def aliyun_cli(args: list[str]) -> None:
    access_key_id = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID", "")
    access_key_secret = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET", "")
    cmd = [
        "aliyun",
        *args,
        "--region",
        REGION,
        "--access-key-id",
        access_key_id,
        "--access-key-secret",
        access_key_secret,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as error:
        stdout = (error.stdout or "").strip()
        stderr = (error.stderr or "").strip()
        raise RuntimeError(
            f"Aliyun CLI command failed with exit code {error.returncode}. stdout={stdout} stderr={stderr}"
        ) from error


def aliyun_cli_json(args: list[str]) -> dict[str, Any]:
    access_key_id = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID", "")
    access_key_secret = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET", "")
    cmd = [
        "aliyun",
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
        stdout = (error.stdout or "").strip()
        stderr = (error.stderr or "").strip()
        raise RuntimeError(
            f"Aliyun CLI command failed with exit code {error.returncode}. stdout={stdout} stderr={stderr}"
        ) from error
    return json.loads(result.stdout or "{}")


def clear_ram(config: dict[str, Any]) -> bool:
    success = True
    role_name = cfg(config, "admin_bootstrap_role_name")
    if not role_name and cfg(config, "role_arn"):
        role_name = cfg(config, "role_arn").rsplit("/", 1)[-1]

    if role_name:
        for policy_name in ["AliyunOSSFullAccess", "AliyunAgentIdentityDataFullAccess"]:
            success &= run_step(
                f"RAM__DetachPolicyFromRole({policy_name})",
                lambda name=policy_name: aliyun_cli([
                    "ram",
                    "DetachPolicyFromRole",
                    "--PolicyType",
                    "System",
                    "--PolicyName",
                    name,
                    "--RoleName",
                    role_name,
                ]),
            )
        role_custom_policies: list[str] = []
        try:
            policies = aliyun_cli_json(["ram", "ListPoliciesForRole", "--RoleName", role_name]).get("Policies", {}).get("Policy", [])
            for item in policies:
                if not isinstance(item, dict):
                    continue
                policy_name = item.get("PolicyName")
                policy_type = item.get("PolicyType")
                if not isinstance(policy_name, str) or not isinstance(policy_type, str):
                    continue
                success &= run_step(
                    f"RAM__DetachPolicyFromRole({policy_name})",
                    lambda name=policy_name, ptype=policy_type: aliyun_cli([
                        "ram",
                        "DetachPolicyFromRole",
                        "--PolicyType",
                        ptype,
                        "--PolicyName",
                        name,
                        "--RoleName",
                        role_name,
                    ]),
                )
                if policy_type == "Custom" and policy_name.startswith("AgentIdentityPolicy-"):
                    role_custom_policies.append(policy_name)
        except Exception as error:
            logger.warning("Failed to inspect role policies for %s: %s", role_name, error)

        success &= run_step("RAM__DeleteRole", lambda: aliyun_cli(["ram", "DeleteRole", "--RoleName", role_name]), required=True)
        for policy_name in role_custom_policies:
            success &= run_step(
                f"RAM__DeleteRoleCustomPolicy({policy_name})",
                lambda name=policy_name: aliyun_cli(["ram", "DeletePolicy", "--PolicyName", name]),
            )

    ram_user = cfg(config, "provisioned_ram_user_name")
    if not ram_user:
        return success

    success &= run_step(
        "RAM__DeleteAccessKey",
        lambda: aliyun_cli([
            "ram",
            "DeleteAccessKey",
            "--UserName",
            ram_user,
            "--UserAccessKeyId",
            cfg(config, "provisioned_ram_access_key_id"),
        ]),
    )
    if DRY_RUN:
        logger.info("[DRY-RUN] skip RAM bootstrap policy discovery")
        return success

    policy_name = ""
    if ram_user.startswith("agent-identity-"):
        policy_name = f"agent-identity-prepare-{ram_user.removeprefix('agent-identity-')}"
    try:
        policies = aliyun_cli_json(["ram", "ListPoliciesForUser", "--UserName", ram_user]).get("Policies", {}).get("Policy", [])
        for item in policies:
            candidate = item.get("PolicyName") if isinstance(item, dict) else ""
            if isinstance(candidate, str) and candidate.startswith("agent-identity-prepare-"):
                policy_name = candidate
                break
    except Exception as error:
        logger.warning("Failed to inspect bootstrap RAM user policies: %s", error)

    if policy_name:
        success &= run_step(
            "RAM__DetachBootstrapPolicyFromUser",
            lambda: aliyun_cli([
                "ram",
                "DetachPolicyFromUser",
                "--PolicyType",
                "Custom",
                "--PolicyName",
                policy_name,
                "--UserName",
                ram_user,
            ]),
        )
        success &= run_step(
            "RAM__DeleteBootstrapPolicy",
            lambda: aliyun_cli(["ram", "DeletePolicy", "--PolicyName", policy_name]),
        )
    success &= run_step("RAM__DeleteBootstrapUser", lambda: aliyun_cli(["ram", "DeleteUser", "--UserName", ram_user]), required=True)
    return success


def stop_local_services() -> None:
    for pattern in ["deploy_starter.main", "application.backend.app"]:
        run_step(
            f"Local__Stop({pattern})",
            lambda value=pattern: subprocess.run(["pkill", "-f", value], check=False),
        )


def archive_config() -> None:
    if DRY_RUN:
        return
    target = ROOT_DIR / f".config.json.cleared.{time.strftime('%Y%m%d%H%M%S')}"
    CONFIG_PATH.rename(target)
    logger.info("[OK] Archived .config.json to %s", target.name)


def main() -> None:
    config = load_config()
    logger.info("[CLEAR] region=%s dry_run=%s", REGION, DRY_RUN)
    logger.info("[CLEAR] resources=%s", json.dumps(config, ensure_ascii=False, indent=2))
    identity_client, inner_client, apig_client, vpc_client, ims_client = make_clients()

    stop_local_services()
    if DRY_RUN:
        logger.info("[DRY-RUN] skip cloud dependency discovery")
    else:
        resolve_apig_dependencies(config, apig_client)
        resolve_policy_set(config, inner_client)
        save_config(config)

    gateway_success = clear_gateway_binding(config, apig_client, inner_client)
    remaining_apig_success = clear_remaining_apig(config, apig_client, vpc_client)
    clear_agent_identity_core(config, identity_client, ims_client)
    ram_success = clear_ram(config)

    if not (gateway_success and remaining_apig_success and ram_success):
        raise RuntimeError("Gateway binding cleanup has failures. .config.json is kept for retry.")
    archive_config()
    logger.info("[OK] clear.py completed.")


if __name__ == "__main__":
    main()
