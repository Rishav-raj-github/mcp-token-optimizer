from setuptools import setup, find_packages

setup(
    name="token_forge",
    version="1.0.0",
    description="The Ultimate LLM Token Optimization Suite & MCP Server",
    author="Rishabh",
    packages=find_packages(),
    install_requires=[
        "mcp>=0.1.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.22.0",
        "tiktoken>=0.5.0",
        "jinja2>=3.0.0"
    ],
    entry_points={
        "console_scripts": [
            "tokenforge-mcp=token_forge.mcp_server:main",
            "tokenforge-dashboard=token_forge.dashboard.app:main"
        ]
    },
    python_requires=">=3.10",
)
