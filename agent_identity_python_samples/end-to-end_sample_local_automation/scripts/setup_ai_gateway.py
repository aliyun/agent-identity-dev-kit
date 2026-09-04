import base64
import json
import os
import random
import string
import time
import uuid
from typing import Any

from alibabacloud_apig20240327 import models as apig_models
from alibabacloud_apig20240327.client import Client as ApigClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_openapi.exceptions import ClientException
from alibabacloud_vpc20160428 import models as vpc_models
from alibabacloud_vpc20160428.client import Client as VpcClient


def _is_true(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _load_body(name: str) -> dict[str, Any] | None:
    text = os.getenv(f"{name}_JSON", "").strip()
    if text:
        return json.loads(text)
    file_path = os.getenv(f"{name}_FILE", "").strip()
    if file_path:
        if not os.path.exists(file_path):
            raise RuntimeError(f"{name}_FILE not found: {file_path}")
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    return None


def _model_from_dict(model_cls, body: dict[str, Any]):
    model = model_cls()
    return model.from_map(body or {})


def _to_map(response: Any) -> dict[str, Any]:
    if response is None or getattr(response, "body", None) is None:
        return {}
    if hasattr(response.body, "to_map"):
        return response.body.to_map()
    return {}


def _pick_id(data: dict[str, Any], *keys: str) -> str | None:
    candidates = [data]
    for key in ("data", "Data"):
        nested = data.get(key) if isinstance(data, dict) else None
        if isinstance(nested, dict):
            candidates.append(nested)
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        for key in keys:
            value = candidate.get(key)
            if isinstance(value, str) and value:
                return value
    return None


def _get_account_id(access_key_id: str, access_key_secret: str) -> str:
    """Retrieve the current account ID via STS GetCallerIdentity."""
    from alibabacloud_sts20150401.client import Client as StsClient
    from alibabacloud_sts20150401 import models as sts_models
    sts_config = open_api_models.Config(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        endpoint="sts.aliyuncs.com",
    )
    sts_client = StsClient(sts_config)
    resp = sts_client.get_caller_identity()
    return resp.body.account_id


def _create_apig_client(access_key_id: str, access_key_secret: str, region: str) -> ApigClient:
    config = open_api_models.Config(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        region_id=region,
        endpoint=f"apig.{region}.aliyuncs.com",
    )
    return ApigClient(config)


def _create_vpc_client(access_key_id: str, access_key_secret: str, region: str) -> VpcClient:
    config = open_api_models.Config(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        region_id=region,
        endpoint=f"vpc.{region}.aliyuncs.com",
    )
    return VpcClient(config)


def _list_vpcs(vpc_client: VpcClient) -> list[dict[str, Any]]:
    response = vpc_client.describe_vpcs(vpc_models.DescribeVpcsRequest(page_number=1, page_size=50))
    return _to_map(response).get("Vpcs", {}).get("Vpc", []) or []


def _list_vswitches(vpc_client: VpcClient, vpc_id: str) -> list[dict[str, Any]]:
    response = vpc_client.describe_vswitches(vpc_models.DescribeVSwitchesRequest(vpc_id=vpc_id, page_number=1, page_size=50))
    return _to_map(response).get("VSwitches", {}).get("VSwitch", []) or []


def _wait_vpc_available(vpc_client: VpcClient, vpc_id: str, timeout_seconds: int = 120, interval: int = 5) -> None:
    """Poll VPC status until it becomes Available or timeout is reached."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        response = vpc_client.describe_vpcs(vpc_models.DescribeVpcsRequest(vpc_id=vpc_id))
        vpc_list = _to_map(response).get("Vpcs", {}).get("Vpc", []) or []
        if vpc_list:
            status = vpc_list[0].get("Status", "")
            if status == "Available":
                return
            print(f"[WAIT] VPC {vpc_id} status: {status}, waiting for Available...")
        time.sleep(interval)
    raise RuntimeError(f"VPC {vpc_id} did not become Available within {timeout_seconds}s.")


def _create_vpc(vpc_client: VpcClient) -> tuple[str, dict[str, Any]]:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    vpc_name = os.getenv("APIG_VPC_NAME", f"agent-ai-gw-vpc-{suffix}").strip()
    cidr_block = os.getenv("APIG_VPC_CIDR", "10.250.0.0/16").strip()
    request = vpc_models.CreateVpcRequest(vpc_name=vpc_name, cidr_block=cidr_block)
    response = vpc_client.create_vpc(request)
    body = _to_map(response)
    vpc_id = _pick_id(body, "VpcId", "vpcId")
    if not vpc_id:
        raise RuntimeError(f"CreateVpc succeeded but VpcId not found: {body}")
    _wait_vpc_available(vpc_client, vpc_id)
    return vpc_id, body


def _select_zones(region: str, existing_vswitches: list[dict[str, Any]], vpc_client: VpcClient) -> tuple[str, str]:
    zone1 = os.getenv("APIG_GATEWAY_ZONE1_ID", "").strip()
    zone2 = os.getenv("APIG_GATEWAY_ZONE2_ID", "").strip()
    if zone1 and zone2:
        return zone1, zone2

    existing_zone_ids = []
    for item in existing_vswitches:
        zone_id = item.get("ZoneId")
        if isinstance(zone_id, str) and zone_id and zone_id not in existing_zone_ids:
            existing_zone_ids.append(zone_id)
    if len(existing_zone_ids) >= 2:
        return existing_zone_ids[0], existing_zone_ids[1]

    if region == "cn-beijing":
        return "cn-beijing-k", "cn-beijing-l"

    zone_response = vpc_client.describe_zones(vpc_models.DescribeZonesRequest())
    zones = _to_map(zone_response).get("Zones", {}).get("Zone", []) or []
    available = [item.get("ZoneId") for item in zones if isinstance(item.get("ZoneId"), str) and item.get("ZoneId")]
    if len(available) < 2:
        raise RuntimeError(f"Not enough zones available in region {region}: {available}")
    return available[0], available[1]


def _wait_vswitch_available(vpc_client: VpcClient, vswitch_id: str, timeout_seconds: int = 120, interval: int = 5) -> None:
    """Poll vSwitch status until it becomes Available or timeout is reached."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        response = vpc_client.describe_vswitches(vpc_models.DescribeVSwitchesRequest(v_switch_id=vswitch_id))
        vswitch_list = _to_map(response).get("VSwitches", {}).get("VSwitch", []) or []
        if vswitch_list:
            status = vswitch_list[0].get("Status", "")
            if status == "Available":
                return
            print(f"[WAIT] vSwitch {vswitch_id} status: {status}, waiting for Available...")
        time.sleep(interval)
    raise RuntimeError(f"vSwitch {vswitch_id} did not become Available within {timeout_seconds}s.")


def _create_vswitch(vpc_client: VpcClient, vpc_id: str, zone_id: str, cidr: str, name_prefix: str) -> tuple[str, dict[str, Any]]:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    request = vpc_models.CreateVSwitchRequest(
        vpc_id=vpc_id,
        zone_id=zone_id,
        cidr_block=cidr,
        v_switch_name=f"{name_prefix}-{zone_id}-{suffix}",
    )
    response = vpc_client.create_vswitch(request)
    body = _to_map(response)
    vswitch_id = _pick_id(body, "VSwitchId", "vSwitchId")
    if not vswitch_id:
        raise RuntimeError(f"CreateVSwitch succeeded but VSwitchId not found: {body}")
    _wait_vswitch_available(vpc_client, vswitch_id)
    return vswitch_id, body


def _ensure_network_prerequisites(vpc_client: VpcClient, region: str) -> dict[str, Any]:
    result: dict[str, Any] = {}

    print("[INFO] Creating new VPC for AI Gateway...")
    vpc_id, create_vpc_resp = _create_vpc(vpc_client)
    result["vpc"] = {"action": "create", "vpc_id": vpc_id, "response": create_vpc_resp}

    vswitches: list[dict[str, Any]] = []
    zone1, zone2 = _select_zones(region, vswitches, vpc_client)
    zone_to_vswitch = {
        item.get("ZoneId"): item.get("VSwitchId")
        for item in vswitches
        if isinstance(item.get("ZoneId"), str) and isinstance(item.get("VSwitchId"), str)
    }

    configured_vsw1 = os.getenv("APIG_GATEWAY_VSWITCH1_ID", "").strip()
    configured_vsw2 = os.getenv("APIG_GATEWAY_VSWITCH2_ID", "").strip()
    if configured_vsw1:
        zone_to_vswitch[zone1] = configured_vsw1
    if configured_vsw2:
        zone_to_vswitch[zone2] = configured_vsw2

    created_vswitches = []
    for index, zone_id in enumerate((zone1, zone2), start=1):
        if zone_to_vswitch.get(zone_id):
            continue
        cidr = os.getenv(f"APIG_GATEWAY_VSWITCH{index}_CIDR", "").strip()
        if not cidr:
            if result["vpc"]["action"] == "create":
                cidr = f"10.250.{index}.0/24"
            else:
                raise RuntimeError(
                    f"No existing vSwitch in zone {zone_id}. "
                    f"Please provide APIG_GATEWAY_VSWITCH{index}_CIDR to create one in existing VPC {vpc_id}."
                )
        vswitch_id, create_vswitch_resp = _create_vswitch(vpc_client, vpc_id, zone_id, cidr, "apig-vsw")
        zone_to_vswitch[zone_id] = vswitch_id
        created_vswitches.append({"zone_id": zone_id, "vswitch_id": vswitch_id, "response": create_vswitch_resp})

    result["v_switches"] = {
        "zone1": {"zone_id": zone1, "vswitch_id": zone_to_vswitch[zone1]},
        "zone2": {"zone_id": zone2, "vswitch_id": zone_to_vswitch[zone2]},
        "created": created_vswitches,
    }
    return result


def _build_gateway_body_from_network(network: dict[str, Any]) -> dict[str, Any]:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return {
        "name": os.getenv("APIG_GATEWAY_NAME", f"agent-ai-gw-{suffix}").strip(),
        "gatewayType": os.getenv("APIG_GATEWAY_TYPE", "AI").strip(),
        "chargeType": os.getenv("APIG_GATEWAY_CHARGE_TYPE", "POSTPAY").strip(),
        "spec": os.getenv("APIG_GATEWAY_SPEC", "aigw.small.x1").strip(),
        "vpcId": network["vpc"]["vpc_id"],
        "networkAccessConfig": {
            "type": os.getenv("APIG_GATEWAY_NETWORK_TYPE", "Internet").strip(),
        },
        "zoneConfig": {
            "selectOption": "Manual",
            "zones": [
                {
                    "zoneId": network["v_switches"]["zone1"]["zone_id"],
                    "vSwitchId": network["v_switches"]["zone1"]["vswitch_id"],
                },
                {
                    "zoneId": network["v_switches"]["zone2"]["zone_id"],
                    "vSwitchId": network["v_switches"]["zone2"]["vswitch_id"],
                },
            ],
        },
    }


def _get_default_environment_id(apig_client: ApigClient, gateway_id: str) -> str | None:
    get_resp = apig_client.get_gateway(gateway_id)
    data = _to_map(get_resp).get("data", {}) or {}
    environments = data.get("environments", []) or []
    for item in environments:
        env_id = item.get("environmentId")
        if isinstance(env_id, str) and env_id:
            return env_id
    return None


def _resolve_service_id_from_body_or_env(gateway_id: str, mcp_body: dict[str, Any] | None) -> str | None:
    explicit_service_id = os.getenv("APIG_SERVICE_ID", "").strip()
    if explicit_service_id:
        return explicit_service_id
    if not mcp_body:
        return None
    backend = mcp_body.get("backend") or mcp_body.get("backendConfig") or {}
    services = backend.get("services") or []
    if not services:
        return None
    first_service = services[0] or {}
    service_id = first_service.get("serviceId")
    if isinstance(service_id, str) and service_id:
        return service_id
    return None


def _build_default_service_body(gateway_id: str) -> dict[str, Any]:
    service_name = os.getenv("APIG_SERVICE_NAME", "agentidentitydata").strip() or "agentidentitydata"
    service_domain = os.getenv(
        "APIG_SERVICE_FQDN",
        "agentidentitydata-vpc.cn-beijing.aliyuncs.com:443",
    ).strip()
    if ":" not in service_domain:
        service_domain = f"{service_domain}:443"
    source_type = os.getenv("APIG_SERVICE_SOURCE_TYPE", "DNS").strip() or "DNS"
    return {
        "gatewayId": gateway_id,
        "sourceType": source_type,
        "serviceConfigs": [
            {
                "name": service_name,
                "addresses": [service_domain],
            }
        ],
    }


def _resolve_plugin_class_id(apig_client: ApigClient, gateway_id: str) -> str:
    explicit_plugin_class_id = os.getenv("APIG_PLUGIN_CLASS_ID", "").strip()
    if explicit_plugin_class_id:
        return explicit_plugin_class_id

    default_plugin_name = "agent-identity-oauth"
    plugin_class_name = os.getenv("APIG_PLUGIN_CLASS_NAME", "").strip() or default_plugin_name
    request = apig_models.ListPluginClassesRequest(gateway_id=gateway_id, page_size=100, page_number=1)
    request.name_like = plugin_class_name
    response = apig_client.list_plugin_classes(request)
    body = _to_map(response)
    items = body.get("data", {}).get("items", []) or []
    if not items:
        raise RuntimeError(
            f"No plugin classes found matching '{plugin_class_name}' for APIG plugin installation. "
            "Please set APIG_PLUGIN_CLASS_ID (or APIG_PLUGIN_CLASS_NAME) explicitly."
        )
    lowered = plugin_class_name.lower()
    exact = next((item for item in items if str(item.get("name", "")).lower() == lowered), None)
    if exact and isinstance(exact.get("pluginClassId"), str) and exact.get("pluginClassId"):
        return exact["pluginClassId"]
    fallback = next((item for item in items if isinstance(item.get("pluginClassId"), str) and item.get("pluginClassId")), None)
    if not fallback:
        raise RuntimeError(
            f"Plugin class '{plugin_class_name}' not found in ListPluginClasses response. "
            f"Available: {[item.get('name') for item in items]}"
        )
    return fallback["pluginClassId"]


def _resolve_or_create_policy_id(apig_client: ApigClient) -> tuple[str, dict[str, Any] | None]:
    explicit_policy_id = os.getenv("APIG_POLICY_ID", "").strip()
    if explicit_policy_id:
        return explicit_policy_id, None

    policy_body = _load_body("APIG_CREATE_POLICY_BODY")
    if policy_body:
        create_policy_resp = apig_client.create_policy(_model_from_dict(apig_models.CreatePolicyRequest, policy_body))
        create_policy_map = _to_map(create_policy_resp)
        policy_id = _pick_id(create_policy_map, "policyId", "PolicyId", "id")
        if not policy_id:
            raise RuntimeError(f"CreatePolicy succeeded but policyId not found: {create_policy_map}")
        return policy_id, {"create_policy_response": create_policy_map}

    # Zero-config fallback: create a default ServiceTls policy.
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    tls_config = json.dumps({
        "mode": "SIMPLE",
        "sni": "agentidentitydata-vpc.cn-beijing.aliyuncs.com",
        "enable": True,
    })
    fallback_body = {
        "name": f"auto-servicetls-{suffix}",
        "className": "ServiceTls",
        "description": "Auto-created by setup_ai_gateway.py",
        "config": tls_config,
    }
    create_policy_resp = apig_client.create_policy(_model_from_dict(apig_models.CreatePolicyRequest, fallback_body))
    create_policy_map = _to_map(create_policy_resp)
    policy_id = _pick_id(create_policy_map, "policyId", "PolicyId", "id")
    if not policy_id:
        raise RuntimeError(f"Default CreatePolicy succeeded but policyId not found: {create_policy_map}")
    return policy_id, {"create_policy_response": create_policy_map, "policy_create_mode": "default_servicetls"}


def _build_default_mcp_spec() -> str:
    # Start with empty tools, then add maps-geo in Step 5.
    return (
        "server:\n"
        "  name: test-mcp\n"
        "  version: 1.0.0\n"
        "tools: []\n"
    )


def _build_default_mcp_body(gateway_id: str, service_id: str, domain_id: str) -> dict[str, Any]:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return {
        "gatewayId": gateway_id,
        "name": f"test-mcp-{suffix}",
        "description": "Auto-created MCP server by setup_ai_gateway.py",
        "type": "RealMCP",
        "protocol": "HTTP",
        "exposedUriPath": "/mcp",
        "domainIds": [domain_id],
        "match": {
            "methods": ["GET", "POST"],
            "path": {
                "type": "Prefix",
                "value": "/mcp",
            },
        },
        "backendConfig": {
            "scene": "SingleService",
            "services": [
                {
                    "serviceId": service_id,
                    "protocol": "HTTP",
                    "port": 80,
                    "weight": 100,
                }
            ],
        },
    }


def _build_default_maps_geo_swagger() -> str:
    swagger_doc = {
        "openapi": "3.0.1",
        "info": {"title": "test-mcp", "version": "1.0.0"},
        "paths": {
            "/maps/geo": {
                "get": {
                    "operationId": "maps-geo",
                    "summary": "查询经纬度",
                    "parameters": [
                        {"name": "address", "in": "query", "required": True, "schema": {"type": "string"}}
                    ],
                    "responses": {"200": {"description": "ok"}},
                }
            }
        },
    }
    return json.dumps(swagger_doc, ensure_ascii=False)


def _extract_streamable_http_urls(mcp_server_map: dict[str, Any]) -> list[str]:
    data = mcp_server_map.get("data", {}) if isinstance(mcp_server_map, dict) else {}
    path = data.get("mcpServerPath") or data.get("exposedUriPath") or "/mcp"
    urls: list[str] = []
    for info in data.get("domainInfos", []) or []:
        if not isinstance(info, dict):
            continue
        name = info.get("name")
        if not isinstance(name, str) or not name:
            continue
        proto = "https" if str(info.get("protocol", "")).upper() == "HTTPS" else "http"
        normalized = path if str(path).startswith("/") else f"/{path}"
        urls.append(f"{proto}://{name}{normalized}")
    return urls


def _create_mcp_with_retry(apig_client: ApigClient, body: dict[str, Any]) -> dict[str, Any]:
    timeout_seconds = int(os.getenv("APIG_MCP_CREATE_WAIT_TIMEOUT_SECONDS", "300"))
    interval_seconds = int(os.getenv("APIG_MCP_CREATE_WAIT_INTERVAL_SECONDS", "10"))
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while True:
        try:
            resp = apig_client.create_mcp_server(_model_from_dict(apig_models.CreateMcpServerRequest, body))
            return _to_map(resp)
        except ClientException as error:
            last_error = error
            if getattr(error, "code", "") != "NotFound.MCPServerApiNotFound":
                raise
            if time.time() >= deadline:
                raise
            time.sleep(interval_seconds)
    if last_error:
        raise last_error
    raise RuntimeError("create_mcp_server failed without specific error")


def _wait_gateway_running(apig_client: ApigClient, gateway_id: str) -> dict[str, Any]:
    timeout_seconds = int(os.getenv("APIG_GATEWAY_WAIT_TIMEOUT_SECONDS", "300"))
    interval_seconds = int(os.getenv("APIG_GATEWAY_WAIT_INTERVAL_SECONDS", "10"))
    deadline = time.time() + timeout_seconds
    history: list[dict[str, Any]] = []

    poll_count = 0
    while True:
        poll_count += 1
        list_resp = apig_client.list_gateways(apig_models.ListGatewaysRequest(page_size=50, page_number=1))
        body = _to_map(list_resp)
        items = body.get("data", {}).get("items", []) or []
        current = next((item for item in items if item.get("gatewayId") == gateway_id), None)
        status = (current or {}).get("status")
        elapsed = int(time.time() - (deadline - timeout_seconds))
        print(f"[WAIT] Gateway {gateway_id} status: {status} (poll #{poll_count}, elapsed {elapsed}s/{timeout_seconds}s)")
        history.append(
            {
                "timestamp": int(time.time()),
                "status": status,
                "request_id": body.get("requestId"),
            }
        )
        if status == "Running":
            print(f"[OK] Gateway {gateway_id} is Running.")
            return {
                "ready": True,
                "gateway_id": gateway_id,
                "status": status,
                "history": history,
            }
        if time.time() >= deadline:
            raise RuntimeError(
                f"Gateway {gateway_id} not ready within {timeout_seconds}s. "
                f"Last status={status}, poll_history={history}"
            )
        time.sleep(interval_seconds)


def run_ai_gateway_setup(cli_bin: str | None, access_key_id: str, access_key_secret: str, region: str) -> dict[str, Any]:
    """
    Set up AI gateway + policy + MCP server via Python SDK.

    The `cli_bin` argument is kept for backward compatibility and is ignored.

    Prerequisite automation before CreateGateway:
      1) Reuse existing VPC/vSwitch when available.
      2) If missing, create VPC and/or required vSwitches automatically.
    """
    _ = cli_bin
    stage = str(os.getenv("APIG_SETUP_STAGE", "all")).strip().lower() or "all"
    result: dict[str, Any] = {"enabled": True, "setup_stage": stage}
    apig_client = _create_apig_client(access_key_id, access_key_secret, region)

    gateway_id = os.getenv("APIG_GATEWAY_ID", "").strip()
    if not gateway_id:
        vpc_client = _create_vpc_client(access_key_id, access_key_secret, region)
        network = _ensure_network_prerequisites(vpc_client, region)
        result["network_prerequisites"] = network
    else:
        network = {}

    if not gateway_id:
        gateway_body = _load_body("APIG_CREATE_GATEWAY_BODY") or _build_gateway_body_from_network(network)
        gateway_req = _model_from_dict(apig_models.CreateGatewayRequest, gateway_body)
        max_retries = 6
        for attempt in range(1, max_retries + 1):
            try:
                create_gateway_resp = apig_client.create_gateway(gateway_req)
                break
            except Exception as exc:
                error_code = getattr(exc, "code", "") or ""
                if "FailToRequestVSwitch" in str(exc) or "FailToRequestVSwitch" in error_code:
                    if attempt < max_retries:
                        wait_seconds = 10 * attempt
                        print(f"[RETRY] create_gateway attempt {attempt}/{max_retries} failed (VSwitch sync delay), retrying in {wait_seconds}s...")
                        time.sleep(wait_seconds)
                        continue
                raise
        create_gateway_map = _to_map(create_gateway_resp)
        gateway_id = _pick_id(create_gateway_map, "gatewayId", "GatewayId", "id")
        if not gateway_id:
            raise RuntimeError(f"CreateGateway succeeded but gatewayId not found: {create_gateway_map}")
        result["create_gateway_response"] = create_gateway_map
    result["gateway_id"] = gateway_id
    result["gateway_wait"] = _wait_gateway_running(apig_client, gateway_id)
    if stage in {"gateway", "gateway_only"}:
        result["stage_complete"] = "gateway_only"
        return result

    # Step 1: CreateService
    service_id = os.getenv("APIG_SERVICE_ID", "").strip()
    mcp_body = _load_body("APIG_CREATE_MCP_SERVER_BODY")
    if not service_id:
        service_id = _resolve_service_id_from_body_or_env(gateway_id, mcp_body)
    if not service_id:
        service_body = _load_body("APIG_CREATE_SERVICE_BODY") or _build_default_service_body(gateway_id)
        service_body.setdefault("gatewayId", gateway_id)
        service_name = ""
        service_configs = service_body.get("serviceConfigs") or []
        if service_configs and isinstance(service_configs[0], dict):
            service_name = str(service_configs[0].get("name", "")).strip()
        try:
            create_service_resp = apig_client.create_service(_model_from_dict(apig_models.CreateServiceRequest, service_body))
            create_service_map = _to_map(create_service_resp)
        except ClientException as error:
            if getattr(error, "code", "") != "Conflict.ServiceExisted":
                raise
            if not service_name:
                raise RuntimeError(
                    "CreateService hit Conflict.ServiceExisted but service name is unavailable for lookup."
                ) from error
            list_services_resp = apig_client.list_services(
                apig_models.ListServicesRequest(gateway_id=gateway_id, name=service_name, page_number=1, page_size=50)
            )
            list_services_map = _to_map(list_services_resp)
            items = list_services_map.get("data", {}).get("items", []) or []
            matched = next(
                (
                    item
                    for item in items
                    if isinstance(item, dict) and str(item.get("name", "")).strip() == service_name
                ),
                None,
            )
            service_id = matched.get("serviceId") if isinstance(matched, dict) else None
            if not service_id:
                raise RuntimeError(
                    f"CreateService conflict but failed to locate existing service '{service_name}'. "
                    f"list_services={list_services_map}"
                ) from error
            result["create_service_response"] = {
                "reused_due_conflict": True,
                "conflict_request_id": getattr(error, "request_id", None),
                "service_id": service_id,
                "service_name": service_name,
                "list_services_response": list_services_map,
            }
        else:
            service_id = _pick_id(create_service_map, "serviceId", "ServiceId", "id")
            if not service_id:
                data = create_service_map.get("data", {}) if isinstance(create_service_map, dict) else {}
                service_ids = data.get("serviceIds") if isinstance(data, dict) else None
                if isinstance(service_ids, list) and service_ids and isinstance(service_ids[0], str):
                    service_id = service_ids[0]
            if not service_id:
                raise RuntimeError(f"CreateService succeeded but serviceId not found: {create_service_map}")
            result["create_service_response"] = create_service_map
    result["service_id"] = service_id

    # Step 2: GetService
    get_service_resp = apig_client.get_service(service_id)
    result["get_service_response"] = _to_map(get_service_resp)

    if stage != "mcp_only":
        # Step 3: CreatePolicy
        policy_id, policy_meta = _resolve_or_create_policy_id(apig_client)
        if policy_meta:
            result.update(policy_meta)
        result["policy_id"] = policy_id

        # Step 4: CreatePolicyAttachment (attach to service by default)
        attach_body = _load_body("APIG_POLICY_ATTACHMENT_BODY")
        if not attach_body:
            environment_id = _get_default_environment_id(apig_client, gateway_id)
            attach_body = {
                "gatewayId": gateway_id,
                "policyId": policy_id,
                "attachResourceType": "GatewayService",
                "attachResourceId": service_id,
                "environmentId": environment_id,
            }
            if not attach_body["environmentId"]:
                raise RuntimeError("Unable to auto-detect gateway environmentId; provide APIG_POLICY_ATTACHMENT_BODY_JSON.")
        try:
            create_attach_resp = apig_client.create_policy_attachment(
                _model_from_dict(apig_models.CreatePolicyAttachmentRequest, attach_body)
            )
            create_policy_attachment_map = _to_map(create_attach_resp)
            result["create_policy_attachment_response"] = create_policy_attachment_map
            policy_attachment_id = _pick_id(
                create_policy_attachment_map,
                "policyAttachmentId",
                "PolicyAttachmentId",
                "attachmentId",
                "AttachmentId",
                "id",
            )
            if policy_attachment_id:
                result["policy_attachment_id"] = policy_attachment_id
        except ClientException as error:
            if getattr(error, "code", "") != "Conflict.PolicyAttachConflict":
                raise
            result["create_policy_attachment_response"] = {
                "reused_due_conflict": True,
                "conflict_request_id": getattr(error, "request_id", None),
                "message": getattr(error, "message", ""),
            }

    # Step 5: InstallPlugin (runs regardless of stage, as long as not gateway_only)
    plugin_id = os.getenv("APIG_PLUGIN_ID", "").strip()
    if not plugin_id:
        install_body = _load_body("APIG_INSTALL_PLUGIN_BODY")
        if not install_body:
            install_body = {
                "gatewayIds": [gateway_id],
                "pluginClassId": _resolve_plugin_class_id(apig_client, gateway_id),
            }
        else:
            install_body.setdefault("gatewayIds", [gateway_id])
            if not install_body.get("pluginClassId"):
                install_body["pluginClassId"] = _resolve_plugin_class_id(apig_client, gateway_id)
        install_plugin_resp = apig_client.install_plugin(_model_from_dict(apig_models.InstallPluginRequest, install_body))
        install_plugin_map = _to_map(install_plugin_resp)
        install_results = install_plugin_map.get("data", {}).get("installPluginResults", []) or []
        plugin_id = next(
            (
                item.get("pluginId")
                for item in install_results
                if isinstance(item, dict) and item.get("gatewayId") == gateway_id and isinstance(item.get("pluginId"), str)
            ),
            None,
        )
        if not plugin_id:
            plugin_id = next(
                (
                    item.get("pluginId")
                    for item in install_results
                    if isinstance(item, dict) and isinstance(item.get("pluginId"), str)
                ),
                None,
            )
        if not plugin_id:
            raise RuntimeError(f"InstallPlugin succeeded but pluginId not found: {install_plugin_map}")
        result["install_plugin_response"] = install_plugin_map
    result["plugin_id"] = plugin_id

    # Step 6: CreatePluginAttachment
    plugin_attachment_body = _load_body("APIG_PLUGIN_ATTACHMENT_BODY")
    if not plugin_attachment_body:
        gateway_arn = os.getenv("AGENTIDENTITY_GATEWAY_ARN", "").strip()
        if not gateway_arn:
            account_id = _get_account_id(access_key_id, access_key_secret)
            gateway_arn = f"acs:apig:{region}:{account_id}:gateway/{gateway_id}"
        plugin_config_yaml = (
            f'agentIdentityService:\n'
            f'  serviceName: "agentidentitydata.dns"\n'
            f'  serviceUrl: "https://agentidentitydata-vpc.{region}.aliyuncs.com"\n'
            f'  resourceId: "{gateway_arn}"'
        )
        plugin_config_b64 = base64.b64encode(plugin_config_yaml.encode("utf-8")).decode("utf-8")
        plugin_attachment_body = {
            "gatewayId": gateway_id,
            "pluginId": plugin_id,
            "pluginConfig": plugin_config_b64,
            "attachResourceType": "Gateway",
            "attachResourceIds": [gateway_id],
            "enable": True,
        }
    try:
        create_plugin_attachment_resp = apig_client.create_plugin_attachment(
            _model_from_dict(apig_models.CreatePluginAttachmentRequest, plugin_attachment_body)
        )
        create_plugin_attachment_map = _to_map(create_plugin_attachment_resp)
        result["create_plugin_attachment_response"] = create_plugin_attachment_map
        plugin_attachment_id = _pick_id(
            create_plugin_attachment_map,
            "pluginAttachmentId",
            "PluginAttachmentId",
            "attachmentId",
            "AttachmentId",
            "id",
        )
        if plugin_attachment_id:
            result["plugin_attachment_id"] = plugin_attachment_id
    except ClientException as error:
        if getattr(error, "code", "") != "Conflict.PluginRuleExisted":
            raise
        result["create_plugin_attachment_response"] = {
            "reused_due_conflict": True,
            "conflict_request_id": getattr(error, "request_id", None),
            "message": getattr(error, "message", ""),
        }

    # Step 4/5/6 in doc: MCP create -> add tool -> get streamable URL
    mcp_server_id = os.getenv("APIG_MCP_SERVER_ID", "").strip()
    if not mcp_server_id:
        # Build defaults so MCP steps run in AK/SK-only mode.
        if not mcp_body:
            domain_name = os.getenv("APIG_MCP_DOMAIN_NAME", f"test-mcp-{uuid.uuid4().hex[:6]}.example.com").strip()
            domain_protocol = os.getenv("APIG_MCP_DOMAIN_PROTOCOL", "HTTP").strip() or "HTTP"
            create_domain_resp = apig_client.create_domain(
                apig_models.CreateDomainRequest(name=domain_name, protocol=domain_protocol, gateway_type="AI")
            )
            create_domain_map = _to_map(create_domain_resp)
            domain_id = _pick_id(create_domain_map, "domainId", "DomainId", "id")
            if not domain_id:
                raise RuntimeError(f"CreateDomain succeeded but domainId not found: {create_domain_map}")
            result["create_domain_response"] = create_domain_map
            result["domain_id"] = domain_id
            mcp_body = _build_default_mcp_body(gateway_id=gateway_id, service_id=service_id, domain_id=domain_id)

        mcp_body.setdefault("gatewayId", gateway_id)
        backend = mcp_body.get("backend") or mcp_body.get("backendConfig")
        if isinstance(backend, dict):
            services = backend.get("services")
            if isinstance(services, list) and services:
                if isinstance(services[0], dict) and not services[0].get("serviceId"):
                    services[0]["serviceId"] = service_id
            else:
                backend["services"] = [{"serviceId": service_id, "protocol": "HTTP", "port": 80, "weight": 100}]
        requested_create_from_type = os.getenv("APIG_MCP_CREATE_FROM_TYPE", "ApiGatewayHttpToMCP").strip()
        if not requested_create_from_type:
            requested_create_from_type = "ApiGatewayHttpToMCP"
        mcp_body.setdefault("createFromType", requested_create_from_type)

        # APIG currently treats HTTP->MCP as an implicit mode:
        # do not pass createFromType and force protocol=HTTP.
        if mcp_body.get("createFromType") == "ApiGatewayHttpToMCP":
            mcp_body["protocol"] = "HTTP"
            mcp_body.pop("createFromType", None)
            result["mcp_create_mode"] = "implicit_http_to_mcp"
        else:
            result["mcp_create_mode"] = str(mcp_body.get("createFromType"))

        try:
            create_mcp_map = _create_mcp_with_retry(apig_client, mcp_body)
        except ClientException as error:
            if getattr(error, "code", "") not in {"NotFound.MCPServerApiNotFound", "InvalidParameter.WithValue"}:
                raise
            # Fallback for tenants/gateways where implicit Http->MCP is unavailable.
            fallback_body = dict(mcp_body)
            fallback_body["createFromType"] = "ApiGatewayProxyMcpHosting"
            fallback_body["protocol"] = "StreamableHTTP"
            fallback_mcp_cfg = fallback_body.get("mcpServerConfig")
            if not isinstance(fallback_mcp_cfg, dict):
                fallback_mcp_cfg = {}
            fallback_mcp_cfg.setdefault("mcpServerSpec", _build_default_mcp_spec())
            fallback_body["mcpServerConfig"] = fallback_mcp_cfg
            create_mcp_map = _create_mcp_with_retry(apig_client, fallback_body)
            result["mcp_create_fallback"] = {
                "requested_mode": result.get("mcp_create_mode"),
                "fallback_mode": "ApiGatewayProxyMcpHosting",
                "reason_code": getattr(error, "code", None),
                "reason_request_id": getattr(error, "request_id", None),
                "reason_message": getattr(error, "message", None),
            }
            result["mcp_create_mode"] = "fallback_proxy_hosting"
        mcp_server_id = _pick_id(create_mcp_map, "mcpServerId", "McpServerId", "id")
        if not mcp_server_id:
            raise RuntimeError(f"CreateMcpServer succeeded but mcpServerId not found: {create_mcp_map}")
        result["create_mcp_server_response"] = create_mcp_map
    if mcp_server_id:
        result["mcp_server_id"] = mcp_server_id

    if mcp_server_id and _is_true(os.getenv("APIG_ADD_DEFAULT_MCP_TOOL", "true")):
        get_before_resp = apig_client.get_mcp_server(mcp_server_id)
        get_before_map = _to_map(get_before_resp)
        data = get_before_map.get("data", {}) if isinstance(get_before_map, dict) else {}
        backend = data.get("backend", {}) if isinstance(data.get("backend", {}), dict) else {}
        services = []
        for item in backend.get("services", []) or []:
            if not isinstance(item, dict):
                continue
            services.append(
                apig_models.UpdateMcpServerRequestBackendConfigServices(
                    service_id=item.get("serviceId"),
                    protocol=item.get("protocol"),
                    port=item.get("port"),
                    weight=item.get("weight"),
                    version=item.get("version"),
                )
            )
        update_req = apig_models.UpdateMcpServerRequest(
            create_from_type=data.get("createFromType"),
            type=data.get("type") or "RealMCP",
            protocol=data.get("protocol") or "HTTP",
            description=data.get("description"),
            domain_ids=data.get("domainIds"),
            exposed_uri_path=data.get("exposedUriPath") or "/mcp",
            match=(apig_models.HttpRouteMatch().from_map(data.get("match"))) if data.get("match") else None,
            backend_config=apig_models.UpdateMcpServerRequestBackendConfig(
                scene=backend.get("scene") or "SingleService",
                services=services,
            ),
            mcp_server_config=apig_models.UpdateMcpServerRequestMcpServerConfig(
                swagger_config=os.getenv("APIG_MCP_DEFAULT_SWAGGER_JSON", "").strip() or _build_default_maps_geo_swagger()
            ),
        )
        update_resp = apig_client.update_mcp_server(mcp_server_id, update_req)
        result["update_mcp_server_response"] = _to_map(update_resp)

    if mcp_server_id and _is_true(os.getenv("APIG_DEPLOY_MCP_SERVER", "true")):
        deploy_resp = apig_client.deploy_mcp_server(mcp_server_id)
        result["deploy_mcp_server_response"] = _to_map(deploy_resp)
        get_resp = apig_client.get_mcp_server(mcp_server_id)
        get_map = _to_map(get_resp)
        result["get_mcp_server_response"] = get_map
        result["mcp_streamable_http_urls"] = _extract_streamable_http_urls(get_map)

    return result


if __name__ == "__main__":
    access_key_id = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID", "")
    access_key_secret = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET", "")
    region = os.getenv("AGENT_IDENTITY_REGION_ID", "cn-beijing")
    if not access_key_id or not access_key_secret:
        raise RuntimeError("ALIBABA_CLOUD_ACCESS_KEY_ID and ALIBABA_CLOUD_ACCESS_KEY_SECRET are required.")
    output = run_ai_gateway_setup(None, access_key_id, access_key_secret, region)
    print(json.dumps(output, ensure_ascii=False, indent=2))
