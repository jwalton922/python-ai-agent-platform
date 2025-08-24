#!/usr/bin/env python3

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="ai-agent-platform",
    version="1.0.0",
    author="AI Agent Platform Team",
    description="A unified platform for creating, managing, and executing AI agents with workflows",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "sqlalchemy>=2.0.23",
        "alembic>=1.13.0",
        "python-multipart>=0.0.6",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "pytest>=7.4.3",
        "pytest-asyncio>=0.21.1",
        "httpx>=0.25.2",
        "python-dotenv>=1.0.0",
        "openai>=1.3.0",
        "anthropic>=0.7.8",
        "streamlit>=1.29.0",
        "pandas>=2.1.3",
        "plotly>=5.18.0",
        "streamlit-chat>=0.1.1",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-asyncio",
            "black",
            "flake8",
            "mypy",
        ],
    },
    entry_points={
        "console_scripts": [
            "ai-agent-platform=run_unified:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    project_urls={
        "Bug Reports": "https://github.com/your-org/ai-agent-platform/issues",
        "Source": "https://github.com/your-org/ai-agent-platform",
    },
)