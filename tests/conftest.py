# Minimal conftest.py for testing
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil
from typing import Generator, AsyncGenerator

# Comment out or remove problematic imports
# from ..config import ConfigManager, SystemConfig, AgentConfig
# from ..agents.base_agent import Agent
# from ..agents.models import AgentRole


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests"""
    temp_path = Path(tempfile.mkdtemp())
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path)


# Minimal configuration fixture
@pytest.fixture
def config(temp_dir: Path):
    return {"temp_dir": temp_dir, "environment": "test"}


# Minimal event loop fixture
@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
