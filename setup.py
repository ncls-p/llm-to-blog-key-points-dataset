#!/usr/bin/env python
"""
Setup script for the LLM Key Points Dataset Generator package.
"""

from setuptools import setup, find_packages

# Read the requirements from the requirements.txt file
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="llm-key-points",
    version="0.1.0",  # Updated to match CHANGELOG.md
    description="A tool for generating and managing datasets of key points extracted from web content",
    author="Ncls-p",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "llm-key-points=llm_key_points.interfaces.cli:run",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
