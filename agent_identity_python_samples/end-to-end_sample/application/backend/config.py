import os

# Read config.yml file
def read_config(file_path: str = '../app.yml'):
    config_path = os.path.join(os.path.dirname(__file__), file_path)
    config = {}
    with open(config_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    if value.lower() == 'true':
                        value = True
                    elif value.lower() == 'false':
                        value = False
                    elif value.isdigit():
                        value = int(value)
                    config[key] = value
    return config

class GlobalConfig:
    """Global configuration class, prioritizes getting configuration from environment variables, then from config.yml file"""
    
    def __init__(self):
        self.config = read_config('../app.yml')
    
    def get(self, key: str, default=None):
        """Get configuration value, prioritizes getting from environment variables, then from configuration file, returns default value if neither exists"""
        # First try to get from environment variables
        env_value = os.getenv(key)
        if env_value is not None:
            return self._convert_value(env_value)
        
        # Then from configuration file
        if key in self.config:
            return self.config[key]
        
        # Return default value if neither exists (default is None)
        return default
    
    def _convert_value(self, value: str):
        """Convert environment variable value to appropriate type"""
        if value.lower() == 'true':
            return True
        elif value.lower() == 'false':
            return False
        elif value.isdigit():
            return int(value)
        else:
            # Try to convert to float
            try:
                return float(value)
            except ValueError:
                # If cannot convert to number, return original string
                return value

# Create global configuration instance
global_config = GlobalConfig()

def get_app_config_with_default(key: str, default=None):
    """Convenient function to get configuration, allows returning default value when configuration doesn't exist"""
    return global_config.get(key, default)

