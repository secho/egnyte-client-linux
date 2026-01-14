#!/usr/bin/env python3
"""Setup script for Egnyte Desktop Client"""

from setuptools import setup, find_packages
import os

# Read README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="egnyte-desktop",
    version="1.0.0",
    author="Egnyte Desktop Client Team",
    description="Native Linux desktop client for Egnyte with GUI and CLI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/egnyte-desktop",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: System :: Filesystems",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "watchdog>=3.0.0",
        "click>=8.1.0",
        "cryptography>=41.0.0",
        "keyring>=24.2.0",
        "python-dateutil>=2.8.2",
        "aiohttp>=3.9.0",
        "asyncio-throttle>=1.0.2",
    ],
    entry_points={
        "console_scripts": [
            "egnyte-desktop=egnyte_desktop.gui.main:main",
            "egnyte-cli=egnyte_desktop.cli.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

