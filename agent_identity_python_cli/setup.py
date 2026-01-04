from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="agent_identity_cli",
    version="0.1.1",
    description="Agent Identity Toolkit CLI for managing AI Agent identities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="Apache-2.0",
    author="lingwu",
    author_email="yangzankai.yzk@alibaba-inc.com",
    url="https://github.com/aliyun/agent-identity-dev-kit",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "alibabacloud_credentials>=0.3.0",
        "alibabacloud_ram20150501>=1.0.0",
        "alibabacloud_sts20150401>=1.0.0",
        "alibabacloud_tea_openapi>=0.4.1,<1.0.0",
        "alibabacloud_agentidentity20250901>=0.0.1",
        "darabonba-core>=1.0.0,<2.0.0",
        "rich>=13.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "agent-identity-cli = agent_identity_cli.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords=["alibabacloud", "agent-identity", "cli", "ram", "workload-identity"],
)