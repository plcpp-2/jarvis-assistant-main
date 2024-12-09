from setuptools import setup, find_packages

setup(
    name="jarvis_assistant",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pytest>=8.3.4",
        "pytest-asyncio>=0.24.0",
        "networkx>=3.4.2",
        "graphviz>=0.20.3",
        "aiohttp>=3.9.3",
        "websockets>=12.0",
        "prometheus_client>=0.20.0",
        "sqlalchemy>=2.0.28",
        "redis>=5.0.2",
        "aiofiles>=23.2.1",
        "pydantic>=2.5.2",
        "python-dotenv>=1.0.0",
        "psutil>=5.9.6"
    ],
    python_requires=">=3.9",
)
