import os
from contextvars import ContextVar
from typing import Optional

class AgentIdentityContext:
    """
    AgentIdentityContext is a context management class used to store user-related information in concurrent environments.
    It utilizes contextvars to ensure data isolation between threads/asynchronous tasks.

    This class is primarily used to store the following pieces of information:
    1. user_id: Unique identifier for the user, used to identify the current operating user
    2. user_token: User access token, used for authentication and authorization
    3. custom_state: Custom state parameter, used in OAuth2 flow to prevent CSRF attacks and verify request sources during callback
    4. workload_access_token: Token for accessing workload resources, which can be retrieved from context or environment variable
    5. session_id: Unique identifier for the session, used to track and manage user sessions

    These pieces of information are isolated within threads, allowing safe usage in asynchronous operations or multi-threaded environments
    without risk of data confusion.
    """

    # Session ID context variable, used to pass session identifier within request chain
    _session_id: ContextVar[Optional[str]] = ContextVar("session_id")

    # User ID context variable, used to pass user id within request chain
    _user_id: ContextVar[Optional[str]] = ContextVar("user_id")

    # User token context variable, used to pass user token within request chain
    _user_token: ContextVar[Optional[str]] = ContextVar("user_token")

    # Custom state context variable, used to pass custom state within request chain.
    # The custom state will be carried when OAuth2 authorization is successful and redirected to the user application.
    # It is recommended that the user application perform ownership verification of the callback login status and state
    # to prevent the link from being maliciously disseminated and causing unauthorized access.
    _custom_state: ContextVar[Optional[str]] = ContextVar("custom_state")

    # Workload access token context variable, used to pass workload authentication token within request chain
    # The workload access token will be retrieved from this context first, if not present,
    # it will read from environment variable. This allows the platform to preset the workload
    # access token to the agent execution environment in certain scenarios. If neither exists,
    # the Agent Identity SDK will automatically acquire it for the client based on the current context.
    _workload_access_token: ContextVar[Optional[str]] = ContextVar("workload_access_token")

    @classmethod
    def set_user_id(cls, user_id: str):
        # Set the user ID in the context
        cls._user_id.set(user_id)

    @classmethod
    def get_user_id(cls) -> Optional[str]:
        # Get the user ID from context
        try:
            return cls._user_id.get()
        except LookupError:
            return None

    @classmethod
    def set_user_token(cls, token: str):
        # Set the user token in the context
        cls._user_token.set(token)

    @classmethod
    def get_user_token(cls) -> Optional[str]:
        # Get the user token from context
        try:
            return cls._user_token.get()
        except LookupError:
            return None

    @classmethod
    def set_custom_state(cls, state: str):
        # Set the custom state in the context
        cls._custom_state.set(state)

    @classmethod
    def get_custom_state(cls) -> Optional[str]:
        # Get the custom state from context
        try:
            return cls._custom_state.get()
        except LookupError:
            return None

    @classmethod
    def set_workload_access_token(cls, token: str):
        # Set the workload access token in the context
        cls._workload_access_token.set(token)

    @classmethod
    def get_workload_access_token(cls) -> Optional[str]:
        # Get the workload access token from context or environment variable
        try:
            workload_access_token = cls._workload_access_token.get()
            if workload_access_token is None:
                return os.environ.get("AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN", None)
            return workload_access_token  # Return the context value if it's not None
        except LookupError:
            return None

    @classmethod
    def clear(cls):
        # Clear all context variables
        cls._session_id.set(None)
        cls._user_id.set(None)
        cls._user_token.set(None)
        cls._custom_state.set(None)
        cls._workload_access_token.set(None)

