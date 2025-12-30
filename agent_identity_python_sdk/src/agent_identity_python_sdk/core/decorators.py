"""Authentication decorators for agent identity service."""

import asyncio
import contextvars
import logging
import os
import uuid
from functools import wraps
from typing import Any, Callable, Dict, List, Literal, Optional

from ..context import AgentIdentityContext
from ..core.identity import IdentityClient
from ..model.stscredential import STSCredential
from ..utils.config import read_local_config, write_local_config

logger = logging.getLogger("agentidentity.core.decorators")
logger.setLevel("INFO")
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())

def get_region() -> str:
    region_env = os.getenv("AGENT_IDENTITY_REGION_ID", None)
    if region_env is not None:
        return region_env
    return "cn-beijing"

def requires_access_token(
    *,
    credential_provider_name: str,
    inject_param_name: str = "access_token",
    scopes: Optional[List[str]] = None,
    on_auth_url: Optional[Callable[[str], Any]] = None,
    auth_flow: Literal["USER_FEDERATION"] = "USER_FEDERATION",
    callback_url: Optional[str] = None,
    force_authentication: bool = False,
    custom_parameters: Optional[Dict[str, str]] = None,
    poll_for_token: bool = True,
) -> Callable:

    """Decorator that fetches an OAuth2 access token before calling the decorated function.

    Args:
        credential_provider_name: The OAuth2 credential provider name

        inject_param_name: Parameter name to inject the token into

        scopes: OAuth2 scopes list

        on_auth_url: Callback function for handling authorization URLs when they are obtained

        auth_flow: Authentication flow type ("USER_FEDERATION")

        callback_url: OAuth2 callback URL

        force_authentication: Whether to force authentication, if enabled, access token acquisition will require authorization

        custom_parameters: A map of custom parameters to be included in the OAuth2 authorization request to the credential provider,
                           which will be passed through and carried in the callback to the callback URL.

        poll_for_token: Whether to poll for the token when authorization is required. If False, when getting OAuth Token and an authorization URL is returned, an exception will be thrown after calling on_auth_url.

    Returns:

        Decorator function that handles OAuth2 token acquisition and injection
    """

    def decorator(func: Callable) -> Callable:
        client = IdentityClient(get_region())

        async def _get_token() -> str:
            user_id = AgentIdentityContext.get_user_id()
            id_token = AgentIdentityContext.get_user_token()
            state = AgentIdentityContext.get_custom_state()

            workload_access_token = await _get_workload_access_token(client, user_id=user_id, id_token=id_token)
            credential_client = await client.get_sts_credential_client(workload_token=workload_access_token,
                                                                       user_id=user_id, user_token=id_token)

            return await client.get_token(
                credential_provider_name=credential_provider_name,
                workload_identity_token=workload_access_token,
                scopes=scopes,
                on_auth_url=on_auth_url,
                auth_flow=auth_flow,
                callback_url=callback_url,
                force_authentication=force_authentication,
                custom_state=state,
                custom_parameters=custom_parameters,
                credential=credential_client,
                poll_for_token=poll_for_token
            )

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs_func: Any) -> Any:
            kwargs_func[inject_param_name] = await _get_token()
            return await func(*args, **kwargs_func)

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs_func: Any) -> Any:
            if _has_running_loop():
                ctx = contextvars.copy_context()
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(ctx.run, asyncio.run, _get_token())
                    token = future.result()
            else:
                token = asyncio.run(_get_token())

            kwargs_func[inject_param_name] = token
            return func(*args, **kwargs_func)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def requires_api_key(*, credential_provider_name: str, inject_param_name: str = "api_key") -> Callable:
    """Decorator that fetches an api key before calling the decorated function.

    Args:
        credential_provider_name: The credential provider name

        inject_param_name: Parameter name to inject the API key into

    Returns:

        Decorator function that handles API key acquisition and injection
    """

    def decorator(func: Callable) -> Callable:
        client = IdentityClient(get_region())

        async def _get_api_key():
            user_id = AgentIdentityContext.get_user_id()
            id_token = AgentIdentityContext.get_user_token()

            workload_access_token = await _get_workload_access_token(client, user_id=user_id, id_token=id_token)
            credential_client = await client.get_sts_credential_client(workload_token=workload_access_token, user_id=user_id, user_token=id_token)
            return await client.get_api_key(
                credential_provider_name=credential_provider_name,
                agent_identity_token=workload_access_token,
                credential=credential_client
            )

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            api_key = await _get_api_key()
            kwargs[inject_param_name] = api_key
            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            if _has_running_loop():
                ctx = contextvars.copy_context()
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(ctx.run, asyncio.run, _get_api_key())
                    api_key = future.result()
            else:
                api_key = asyncio.run(_get_api_key())

            kwargs[inject_param_name] = api_key
            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator

def requires_sts_token(*, inject_param_name: str = "sts_credential",
                       session_duration: Optional[str] = 3600,
                       policy: Optional[str] = None
                       ) -> Callable:
    """Decorator that fetches a STS token before calling the decorated function.

    Args:
        inject_param_name: Parameter name to inject the STS credential into

        session_duration: The duration in seconds for which the STS credential should be valid.
                          Defaults to 3600 seconds (1 hour).

        policy: An optional policy in JSON format that further restricts the permissions of the STS credential.
                This policy is combined with the role's policy when issuing the credentials.

    Returns:

        Decorator function that handles STS credential acquisition and injection
    """

    def decorator(func: Callable) -> Callable:
        client = IdentityClient(get_region())

        async def _get_sts_token() -> STSCredential:
            user_id = AgentIdentityContext.get_user_id()
            id_token = AgentIdentityContext.get_user_token()

            workload_access_token = await _get_workload_access_token(client, user_id=user_id, id_token=id_token)
            return await client.assume_role_for_workload_identity(workload_token=workload_access_token,
                                                                  role_session_name=f'AgentIdentitySessionRole-{uuid.uuid4()}',
                                                                  duration_seconds=session_duration,
                                                                  policy=policy)

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            sts_credential = await _get_sts_token()
            kwargs[inject_param_name] = sts_credential
            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            if _has_running_loop():
                ctx = contextvars.copy_context()
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(ctx.run, asyncio.run, _get_sts_token())
                    sts_credential = future.result()
            else:
                sts_credential = asyncio.run(_get_sts_token())

            kwargs[inject_param_name] = sts_credential
            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


async def _get_workload_access_token_local(client: IdentityClient, user_id: Optional[str] = None, id_token: Optional[str] = None) -> str:
    workload_identity_name = os.environ.get("AGENT_IDENTITY_WORKLOAD_IDENTITY_NAME", None)
    if not workload_identity_name:
        workload_identity_name = read_local_config('workload_identity_name')

    if workload_identity_name:
        logger.info(f"Using workload identity from config file: {workload_identity_name}")
    else:
        workload_identity_name = client.create_workload_identity()
        logger.info("Created a workload identity: %s", workload_identity_name)

    write_local_config("workload_identity_name", workload_identity_name)

    return client.get_workload_access_token(workload_identity_name, user_id=user_id, user_token=id_token)


async def _get_workload_access_token(client: IdentityClient,
        user_id: Optional[str] = None,
        id_token: Optional[str] = None) -> str:
    token = AgentIdentityContext.get_workload_access_token()
    if token is not None:
        return token
    else:
        return await _get_workload_access_token_local(client, user_id, id_token)


def _has_running_loop() -> bool:
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False
