# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages

PACKAGE = "alibabacloud_agentidentity20250901_inner"
NAME = "alibabacloud_agentidentity20250901_inner"
VERSION = "1.0.1.dev0"
REQUIRES = [
    "alibabacloud_tea_util>=0.3.14, <1.0.0",
    "alibabacloud_tea_openapi>=0.3.16, <1.0.0",
    "alibabacloud_openapi_util>=0.2.4, <1.0.0",
    "alibabacloud_endpoint_util>=0.0.4, <1.0.0",
]

setup(
    name=NAME,
    version=VERSION,
    description="Alibaba Cloud AgentIdentity (20250901) SDK Library for Python (Inner)",
    packages=[PACKAGE],
    package_dir={PACKAGE: "."},
    install_requires=REQUIRES,
    python_requires=">=3.6",
)
