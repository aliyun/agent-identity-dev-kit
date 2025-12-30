"""Tests for the config module."""
import json
import os
import tempfile
from pathlib import Path
from agent_identity_python_sdk.utils.config import (
    write_local_config, read_local_config, local_config_file
)


class TestConfigModule:
    """Test cases for the config module."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Clean up any existing default config file
        if Path(local_config_file).exists():
            Path(local_config_file).unlink()

    def teardown_method(self):
        """Clean up after each test method."""
        # Remove test files
        config_files = [f for f in os.listdir(self.test_dir) if f.endswith('.json')]
        for config_file in config_files:
            file_path = Path(self.test_dir) / config_file
            if file_path.exists():
                file_path.unlink()
        
        # Change back to original directory and remove temp directory
        os.chdir(self.original_cwd)
        os.rmdir(self.test_dir)

    def test_write_and_read_config_success(self):
        """Test writing and reading a configuration successfully."""
        # Write a config value
        write_local_config("test_key", "test_value")
        
        # Read the config value
        result = read_local_config("test_key")
        
        # Verify the value was written and read correctly
        assert result == "test_value"

    def test_read_nonexistent_key(self):
        """Test reading a key that doesn't exist in the config."""
        # Write a config value
        write_local_config("existing_key", "existing_value")
        
        # Try to read a non-existent key
        result = read_local_config("nonexistent_key")
        
        # Should return None
        assert result is None

    def test_read_nonexistent_file(self):
        """Test reading from a config file that doesn't exist."""
        result = read_local_config("any_key", "nonexistent_file.json")
        
        # Should return None
        assert result is None

    def test_write_multiple_configs(self):
        """Test writing multiple configuration values."""
        # Write multiple config values
        write_local_config("key1", "value1")
        write_local_config("key2", "value2")
        write_local_config("key3", "value3")
        
        # Read all values back
        assert read_local_config("key1") == "value1"
        assert read_local_config("key2") == "value2"
        assert read_local_config("key3") == "value3"

    def test_overwrite_existing_config(self):
        """Test overwriting an existing configuration value."""
        # Write initial value
        write_local_config("test_key", "initial_value")
        assert read_local_config("test_key") == "initial_value"
        
        # Overwrite with new value
        write_local_config("test_key", "new_value")
        assert read_local_config("test_key") == "new_value"

    def test_write_and_read_with_custom_file_path(self):
        """Test writing and reading with a custom file path."""
        custom_file = "custom_config.json"
        
        # Write to custom file
        write_local_config("custom_key", "custom_value", custom_file)
        
        # Read from custom file
        result = read_local_config("custom_key", custom_file)
        
        assert result == "custom_value"
        
        # Verify default file is not affected
        default_result = read_local_config("custom_key")
        assert default_result is None

    def test_empty_config_file_handling(self):
        """Test handling of an empty configuration file."""
        # Create an empty config file
        empty_file = "empty_config.json"
        Path(empty_file).touch()
        
        # Try to read from empty file
        result = read_local_config("any_key", empty_file)
        assert result is None
        
        # Write to the empty file
        write_local_config("new_key", "new_value", empty_file)
        result = read_local_config("new_key", empty_file)
        assert result == "new_value"

    def test_invalid_json_file_handling(self):
        """Test handling of a file with invalid JSON content."""
        # Create a file with invalid JSON
        invalid_json_file = "invalid_config.json"
        with open(invalid_json_file, 'w', encoding='utf-8') as f:
            f.write("this is not valid json")
        
        # Try to read from invalid JSON file
        result = read_local_config("any_key", invalid_json_file)
        assert result is None
        
        # Try to write to the invalid JSON file (should work)
        write_local_config("valid_key", "valid_value", invalid_json_file)
        result = read_local_config("valid_key", invalid_json_file)
        assert result == "valid_value"

    def test_special_characters_in_values(self):
        """Test handling of special characters in config values."""
        special_value = 'Value with "quotes", {braces}, and [brackets]'
        
        # Write value with special characters
        write_local_config("special_key", special_value)
        
        # Read it back
        result = read_local_config("special_key")
        assert result == special_value

    def test_unicode_characters_in_values(self):
        """Test handling of Unicode characters in config values."""
        unicode_value = "Hello 世界 🌍 中文"
        
        # Write value with Unicode characters
        write_local_config("unicode_key", unicode_value)
        
        # Read it back
        result = read_local_config("unicode_key")
        assert result == unicode_value

    def test_config_file_format(self):
        """Test that config file is written in proper JSON format."""
        # Write a config value
        write_local_config("format_test_key", "format_test_value")
        
        # Read the file directly to check JSON format
        with open(local_config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the content to verify it's valid JSON
        parsed = json.loads(content)
        assert parsed["format_test_key"] == "format_test_value"
        
        # Verify the JSON is properly formatted with indent
        lines = content.split('\n')
        # The value should be indented (at least 2 spaces at start of value line)
        assert any('  "' in line and 'format_test_value' in line for line in lines)

    def test_json_decode_error_in_read_local_config(self):
        """Test read_local_config handles JSONDecodeError properly."""
        # Create a file with malformed JSON that will cause JSONDecodeError when reading
        malformed_json_file = "malformed_config.json"
        with open(malformed_json_file, 'w', encoding='utf-8') as f:
            f.write('{"key": "value"')  # Missing closing brace to make it invalid JSON
        
        # Try to read from malformed JSON file
        result = read_local_config("any_key", malformed_json_file)
        assert result is None

    def test_json_decode_error_with_non_empty_invalid_content(self):
        """Test handling of invalid JSON in non-empty file."""
        # Create a file with invalid JSON content (not empty but invalid)
        invalid_file = "invalid_content.json"
        with open(invalid_file, 'w', encoding='utf-8') as f:
            f.write('{"key": "unclosed string}')
        
        # Should handle gracefully and return None
        result = read_local_config("any_key", invalid_file)
        assert result is None
        
        # Should be able to write after reading invalid content
        write_local_config("after_invalid_key", "after_invalid_value", invalid_file)
        result = read_local_config("after_invalid_key", invalid_file)
        assert result == "after_invalid_value"

    def test_read_with_empty_file_content(self):
        """Test read_local_config behavior with file that has empty content."""
        # Create a file with just whitespace
        empty_content_file = "empty_content.json"
        with open(empty_content_file, 'w', encoding='utf-8') as f:
            f.write('   \n\t  ')  # Just whitespace
        
        # Should handle gracefully and return None
        result = read_local_config("any_key", empty_content_file)
        assert result is None
        
        # Should be able to write to this file
        write_local_config("whitespace_key", "whitespace_value", empty_content_file)
        result = read_local_config("whitespace_key", empty_content_file)
        assert result == "whitespace_value"