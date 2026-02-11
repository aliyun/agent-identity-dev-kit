from setuptools import setup, find_packages
import os
import yaml
import uuid

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

def read_config():
    config_path = os.path.join(os.path.dirname(__file__), 'deploy_starter', 'config.yml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def read_readme():
    readme_files = ["README.md", "README.rst", "README.txt"]
    for filename in readme_files:
        if os.path.exists(filename):
            with open(filename, "r") as fh:
                return fh.read()
    return "A FastAPI application with AgentScope runtime"

config = read_config()

setup_package_name = config.get('SETUP_PACKAGE_NAME', 'deploy_starter')
setup_module_name = config.get('SETUP_MODULE_NAME', 'main')
setup_function_name = config.get('SETUP_FUNCTION_NAME', 'run_app')
setup_command_name = config.get('SETUP_COMMAND_NAME', 'agentdev-starter')

base_name = config.get('SETUP_NAME', 'agentDev-starter')
unique_name = f"{base_name}-{uuid.uuid4().hex[:8]}"

setup(
    name=unique_name,
    version=config.get('SETUP_VERSION', '0.1.0'),
    description=config.get('SETUP_DESCRIPTION', 'agentDev-starter'),
    long_description=config.get('SETUP_LONG_DESCRIPTION', 'agentDev-starter services, supporting both direct execution and uvicorn deployment'),
    packages=find_packages(include=['deploy_starter*']),
    package_dir={'deploy_starter': 'deploy_starter'},
    install_requires=requirements,
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
                f"{setup_command_name}={setup_package_name}.{setup_module_name}:{setup_function_name}",
        ],
    },
    include_package_data=True,
    package_data={
        'deploy_starter': ['*.yml'],
    },
)