from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="agent_identity_python_sdk",
    version="0.1.1",
    description="Python SDK for using Agent Identity Service",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="Apache-2.0",
    author="shaoheng",
    author_email="liuyuhao.lyh@alibaba-inc.com",
    url="https://github.com/aliyun/agent-identity-dev-kit",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "alibabacloud-agentidentity20250901>=1.0.1",
        "alibabacloud-agentidentitydata20251127>=1.0.2",
        "setuptools",
        "pydantic==2.11.7",
        "urllib3==2.3.0",
        "utils==1.0.2",
    ],
    extras_require={
        "dev": [
            "pytest>=8.4.1",
            "pytest-asyncio>=0.24.0",
            "pytest-cov>=6.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)