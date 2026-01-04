#!/usr/bin/env python3
"""
Setup script for Opik MCP Server
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    requirements = [
        line.strip() 
        for line in requirements_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="opik-mcp-server",
    version="1.0.0",
    description="Production-ready MCP server for Opik evaluation framework with AI agent integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Tony Esposito",
    author_email="tony@mydataclub.com",
    url="https://github.com/anespo/opik-mcp-server",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "mypy>=1.5.0",
            "diagrams>=0.23.0"
        ]
    },
    entry_points={
        "console_scripts": [
            "opik-mcp-server=opik_mcp_server.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Monitoring",
    ],
    keywords="opik evaluation mcp server ai agents multi-agent aws agentcore",
    project_urls={
        "Bug Reports": "https://github.com/anespo/opik-mcp-server/issues",
        "Source": "https://github.com/anespo/opik-mcp-server",
        "Documentation": "https://github.com/anespo/opik-mcp-server/blob/main/README.md",
    },
    include_package_data=True,
    zip_safe=False,
)
