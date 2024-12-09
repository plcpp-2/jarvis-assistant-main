import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil
from typing import Generator, AsyncGenerator

from ..config import ConfigManager, SystemConfig, AgentConfig
from ..agents.base_agent import Agent
from ..agents.models import AgentRole

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)

@pytest.fixture
def config(temp_dir: Path) -> SystemConfig:
    """Create a test configuration"""
    return SystemConfig(
        data_dir=temp_dir / "data",
        log_level="DEBUG",
        dashboard_port=8081,  # Different from production
        max_agents=5,
        agent_config=AgentConfig(
            max_concurrent_tasks=2,
            learning_batch_size=5,
            model_update_frequency=50,
            resource_threshold=0.8
        )
    )

@pytest.fixture
async def test_agent(config: SystemConfig) -> AsyncGenerator[Agent, None]:
    """Create a test agent"""
    agent = Agent(None, "test-agent", "Test Agent", AgentRole.ANALYZER)
    yield agent
    # Cleanup
    await agent.task_queue.join()
    
@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
