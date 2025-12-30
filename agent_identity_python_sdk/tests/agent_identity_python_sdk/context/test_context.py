"""Tests for the AgentIdentityContext class."""
import os
import asyncio
from unittest.mock import patch
import pytest
from agent_identity_python_sdk.context import AgentIdentityContext


class TestAgentIdentityContext:
    """Test cases for AgentIdentityContext class."""

    def test_set_and_get_user_id(self):
        """Test setting and getting user ID."""
        # Clear context first
        AgentIdentityContext.clear()
        
        # Test setting and getting user ID
        AgentIdentityContext.set_user_id("test-user-id")
        assert AgentIdentityContext.get_user_id() == "test-user-id"
        
        # Test getting user ID when not set (should return None)
        AgentIdentityContext.clear()
        assert AgentIdentityContext.get_user_id() is None

    def test_set_and_get_user_token(self):
        """Test setting and getting user token."""
        # Clear context first
        AgentIdentityContext.clear()
        
        # Test setting and getting user token
        AgentIdentityContext.set_user_token("test-user-token")
        assert AgentIdentityContext.get_user_token() == "test-user-token"
        
        # Test getting user token when not set (should return None)
        AgentIdentityContext.clear()
        assert AgentIdentityContext.get_user_token() is None

    def test_set_and_get_custom_state(self):
        """Test setting and getting custom state."""
        # Clear context first
        AgentIdentityContext.clear()
        
        # Test setting and getting custom state
        AgentIdentityContext.set_custom_state("test-custom-state")
        assert AgentIdentityContext.get_custom_state() == "test-custom-state"
        
        # Test getting custom state when not set (should return None)
        AgentIdentityContext.clear()
        assert AgentIdentityContext.get_custom_state() is None

    def test_set_and_get_workload_access_token_from_context(self):
        """Test setting and getting workload access token from context."""
        # Clear context first
        AgentIdentityContext.clear()
        
        # Remove environment variable to ensure test isolation
        env_backup = os.environ.get("AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN")
        if "AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN" in os.environ:
            del os.environ["AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN"]
        
        try:
            # Test setting and getting workload access token from context
            AgentIdentityContext.set_workload_access_token("test-workload-token")
            assert AgentIdentityContext.get_workload_access_token() == "test-workload-token"
            
            # Test getting workload access token when not set (should return None)
            AgentIdentityContext.clear()
            assert AgentIdentityContext.get_workload_access_token() is None
        finally:
            # Restore environment variable if it was present
            if env_backup is not None:
                os.environ["AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN"] = env_backup

    def test_get_workload_access_token_from_environment(self):
        """Test getting workload access token from environment variable."""
        # Clear context first
        AgentIdentityContext.clear()
        
        # Test getting workload access token from environment when context is None
        with patch.dict(os.environ, {"AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN": "env-workload-token"}):
            # Set context to None explicitly to trigger environment lookup
            AgentIdentityContext.set_workload_access_token(None)
            assert AgentIdentityContext.get_workload_access_token() == "env-workload-token"

    def test_get_workload_access_token_from_environment_when_not_in_context(self):
        """Test getting workload access token from environment variable when not in context."""
        # Clear context first
        AgentIdentityContext.clear()
        
        with patch.dict(os.environ, {"AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN": "env-workload-token"}):
            assert AgentIdentityContext.get_workload_access_token() == "env-workload-token"

    def test_get_workload_access_token_none_when_both_absent(self):
        """Test getting workload access token returns None when both context and env are absent."""
        # Clear context first
        AgentIdentityContext.clear()
        
        # Remove environment variable if it exists
        env_backup = os.environ.get("AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN")
        if "AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN" in os.environ:
            del os.environ["AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN"]
        
        try:
            assert AgentIdentityContext.get_workload_access_token() is None
        finally:
            # Restore environment variable if it was present
            if env_backup is not None:
                os.environ["AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN"] = env_backup

    def test_clear_method(self):
        """Test clearing all context variables."""
        # Remove environment variable to ensure test isolation
        env_backup = os.environ.get("AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN")
        if "AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN" in os.environ:
            del os.environ["AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN"]
        
        try:
            # Set all context variables
            AgentIdentityContext.set_user_id("test-user-id")
            AgentIdentityContext.set_user_token("test-user-token")
            AgentIdentityContext.set_custom_state("test-custom-state")
            AgentIdentityContext.set_workload_access_token("test-workload-token")
            
            # Verify they are set
            assert AgentIdentityContext.get_user_id() == "test-user-id"
            assert AgentIdentityContext.get_user_token() == "test-user-token"
            assert AgentIdentityContext.get_custom_state() == "test-custom-state"
            assert AgentIdentityContext.get_workload_access_token() == "test-workload-token"
            
            # Clear all context variables
            AgentIdentityContext.clear()
            
            # Verify they are all None
            assert AgentIdentityContext.get_user_id() is None
            assert AgentIdentityContext.get_user_token() is None
            assert AgentIdentityContext.get_custom_state() is None
            assert AgentIdentityContext.get_workload_access_token() is None
        finally:
            # Restore environment variable if it was present
            if env_backup is not None:
                os.environ["AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN"] = env_backup

    def test_context_isolation_with_different_values(self):
        """Test context isolation with different values."""
        # Clear context first
        AgentIdentityContext.clear()
        
        # Set values
        AgentIdentityContext.set_user_id("user1")
        AgentIdentityContext.set_user_token("token1")
        first_user_id = AgentIdentityContext.get_user_id()
        first_user_token = AgentIdentityContext.get_user_token()
        
        assert first_user_id == "user1"
        assert first_user_token == "token1"
        
        # Update values
        AgentIdentityContext.set_user_id("user2")
        AgentIdentityContext.set_user_token("token2")
        second_user_id = AgentIdentityContext.get_user_id()
        second_user_token = AgentIdentityContext.get_user_token()
        
        assert second_user_id == "user2"
        assert second_user_token == "token2"

    def test_get_user_id_when_not_set_uses_lookup_error_handling(self):
        """Test that get_user_id handles LookupError when context variable is never set."""
        # Reset context
        AgentIdentityContext.clear()
        # This should trigger the LookupError handling in get_user_id
        result = AgentIdentityContext.get_user_id()
        assert result is None

    def test_get_user_token_when_not_set_uses_lookup_error_handling(self):
        """Test that get_user_token handles LookupError when context variable is never set."""
        # Reset context
        AgentIdentityContext.clear()
        # This should trigger the LookupError handling in get_user_token
        result = AgentIdentityContext.get_user_token()
        assert result is None

    def test_get_custom_state_when_not_set_uses_lookup_error_handling(self):
        """Test that get_custom_state handles LookupError when context variable is never set."""
        # Reset context
        AgentIdentityContext.clear()
        # This should trigger the LookupError handling in get_custom_state
        result = AgentIdentityContext.get_custom_state()
        assert result is None

    def test_get_workload_access_token_when_not_set_uses_lookup_error_handling(self):
        """Test that get_workload_access_token handles LookupError when context variable is never set."""
        # Remove environment variable to ensure test isolation
        env_backup = os.environ.get("AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN")
        if "AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN" in os.environ:
            del os.environ["AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN"]
        
        try:
            # Reset context
            AgentIdentityContext.clear()
            # This should trigger the LookupError handling in get_workload_access_token
            result = AgentIdentityContext.get_workload_access_token()
            assert result is None
        finally:
            # Restore environment variable if it was present
            if env_backup is not None:
                os.environ["AGENT_IDENTITY_WORKLOAD_ACCESS_TOKEN"] = env_backup

    def test_lookup_error_handling_with_monkey_patch(self):
        """Test LookupError handling by temporarily patching the get methods to raise LookupError."""
        from contextvars import ContextVar
        
        # Create new context variables to replace the class variables
        new_user_id_var = ContextVar("user_id")
        new_user_token_var = ContextVar("user_token")
        new_custom_state_var = ContextVar("custom_state")
        new_workload_access_token_var = ContextVar("workload_access_token")
        
        # Save original context vars
        original_user_id = AgentIdentityContext._user_id
        original_user_token = AgentIdentityContext._user_token
        original_custom_state = AgentIdentityContext._custom_state
        original_workload_access_token = AgentIdentityContext._workload_access_token
        
        try:
            # Replace with new context vars that have never been set
            AgentIdentityContext._user_id = new_user_id_var
            AgentIdentityContext._user_token = new_user_token_var
            AgentIdentityContext._custom_state = new_custom_state_var
            AgentIdentityContext._workload_access_token = new_workload_access_token_var
            
            # Test that all get methods handle LookupError correctly when vars are never set
            assert AgentIdentityContext.get_user_id() is None
            assert AgentIdentityContext.get_user_token() is None
            assert AgentIdentityContext.get_custom_state() is None
            assert AgentIdentityContext.get_workload_access_token() is None
            
        finally:
            # Restore original context vars
            AgentIdentityContext._user_id = original_user_id
            AgentIdentityContext._user_token = original_user_token
            AgentIdentityContext._custom_state = original_custom_state
            AgentIdentityContext._workload_access_token = original_workload_access_token


class TestAgentIdentityContextAsync:
    """Test cases for AgentIdentityContext class in async context."""

    async def set_context_in_task(self, user_id, delay=0.1):
        """Helper method to set context in a separate task."""
        await asyncio.sleep(delay)  # Small delay to allow task switching
        AgentIdentityContext.set_user_id(user_id)
        AgentIdentityContext.set_user_token(f"token-{user_id}")
        return {
            "user_id": AgentIdentityContext.get_user_id(),
            "user_token": AgentIdentityContext.get_user_token()
        }

    @pytest.mark.asyncio
    async def test_context_isolation_in_async_tasks(self):
        """Test context isolation in async tasks."""
        # Clear context first
        AgentIdentityContext.clear()
        
        # Create concurrent tasks that set and get context values
        task1 = asyncio.create_task(self.set_context_in_task("user1", 0.1))
        task2 = asyncio.create_task(self.set_context_in_task("user2", 0.15))
        task3 = asyncio.create_task(self.set_context_in_task("user3", 0.05))
        
        results = await asyncio.gather(task1, task2, task3)
        
        # Each task should have its own isolated context
        assert results[0]["user_id"] == "user1"
        assert results[0]["user_token"] == "token-user1"
        assert results[1]["user_id"] == "user2"
        assert results[1]["user_token"] == "token-user2"
        assert results[2]["user_id"] == "user3"
        assert results[2]["user_token"] == "token-user3"
        
        # Main context should remain unaffected (or None if not explicitly set)
        main_context_user_id = AgentIdentityContext.get_user_id()
        assert main_context_user_id is None  # Should be None as no value was explicitly set in main context after clear

    @pytest.mark.asyncio
    async def test_context_preservation_across_async_await(self):
        """Test that context is preserved across async/await boundaries in the same task."""
        # Clear context first
        AgentIdentityContext.clear()
        
        # Set context in main task
        AgentIdentityContext.set_user_id("main-task-user")
        AgentIdentityContext.set_user_token("main-task-token")
        
        # Verify initial values
        assert AgentIdentityContext.get_user_id() == "main-task-user"
        assert AgentIdentityContext.get_user_token() == "main-task-token"
        
        # Wait a bit to test preservation across await
        await asyncio.sleep(0.01)
        
        # Context should still be preserved
        assert AgentIdentityContext.get_user_id() == "main-task-user"
        assert AgentIdentityContext.get_user_token() == "main-task-token"
        
        # Simulate a complex async operation
        async def complex_operation():
            await asyncio.sleep(0.01)
            return {
                "user_id": AgentIdentityContext.get_user_id(),
                "user_token": AgentIdentityContext.get_user_token()
            }
        
        result = await complex_operation()
        assert result["user_id"] == "main-task-user"
        assert result["user_token"] == "main-task-token"

    @pytest.mark.asyncio
    async def test_context_with_nested_async_calls(self):
        """Test context behavior with nested async calls."""
        # Clear context first
        AgentIdentityContext.clear()
        
        # In the same async task, context variables are shared, not isolated
        async def nested_async_call(user_suffix):
            AgentIdentityContext.set_user_id(f"nested-{user_suffix}")
            await asyncio.sleep(0.01)
            return AgentIdentityContext.get_user_id()
        
        async def outer_async_call(user_suffix):
            AgentIdentityContext.set_user_id(f"outer-{user_suffix}")
            # Capture the outer context before calling nested function
            outer_context_before_nested = AgentIdentityContext.get_user_id()
            nested_result = await nested_async_call(user_suffix)
            # After nested call, the context will have the value set by nested function
            current_context_after_nested = AgentIdentityContext.get_user_id()
            return {
                "outer_before_nested": outer_context_before_nested,
                "nested": nested_result,
                "outer_after_nested": current_context_after_nested
            }
        
        # This shows how context is shared in the same async task
        result = await outer_async_call("test")
        assert result["outer_before_nested"] == "outer-test"
        assert result["nested"] == "nested-test"
        assert result["outer_after_nested"] == "nested-test"  # This will be the value set by nested function