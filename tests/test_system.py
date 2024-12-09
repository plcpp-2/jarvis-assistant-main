import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from jarvis_assistant.system.system_ops import SystemManager

@pytest.fixture
async def system_manager():
    """Create a system manager instance for testing"""
    config = {
        'hibernation_threshold': 0.1,
        'hibernation_period': 5,
        'resource_limits': {
            'cpu_percent': 80,
            'memory_percent': 80,
            'disk_percent': 90
        }
    }
    manager = SystemManager(config)
    await manager.initialize()
    yield manager
    await manager.cleanup()

@pytest.mark.asyncio
async def test_system_initialization(system_manager):
    """Test system manager initialization"""
    assert not system_manager.is_hibernating
    assert system_manager.failsafe_enabled
    assert isinstance(system_manager.last_activity, datetime)

@pytest.mark.asyncio
async def test_hibernation(system_manager):
    """Test hibernation functionality"""
    # Set last activity to trigger hibernation
    system_manager.last_activity = datetime.now() - timedelta(seconds=10)
    
    # Wait for hibernation check
    await asyncio.sleep(1)
    
    assert system_manager.is_hibernating

@pytest.mark.asyncio
async def test_resource_monitoring(system_manager):
    """Test resource monitoring"""
    with patch('psutil.cpu_percent', return_value=90), \
         patch('psutil.virtual_memory', return_value=Mock(percent=85)), \
         patch('psutil.disk_usage', return_value=Mock(percent=95)):
        
        # Get system status
        status = system_manager.get_system_status()
        
        assert status['cpu_percent'] == 90
        assert status['memory_percent'] == 85
        assert status['disk_percent'] == 95
        
        # Wait for monitoring to trigger hibernation
        await asyncio.sleep(1)
        assert system_manager.is_hibernating

@pytest.mark.asyncio
async def test_failsafe(system_manager):
    """Test failsafe system"""
    # Disable failsafe
    await system_manager.toggle_failsafe(False)
    assert not system_manager.failsafe_enabled
    
    # Simulate high resource usage
    with patch('psutil.cpu_percent', return_value=90):
        await asyncio.sleep(1)
        assert not system_manager.is_hibernating  # Should not hibernate with failsafe off
    
    # Enable failsafe
    await system_manager.toggle_failsafe(True)
    assert system_manager.failsafe_enabled
    
    # Simulate high resource usage again
    with patch('psutil.cpu_percent', return_value=90):
        await asyncio.sleep(1)
        assert system_manager.is_hibernating  # Should hibernate with failsafe on

@pytest.mark.asyncio
async def test_state_persistence(system_manager, tmp_path):
    """Test state saving and loading"""
    # Set custom state
    system_manager.is_hibernating = True
    system_manager.failsafe_enabled = False
    system_manager.state_file = tmp_path / "test_state.json"
    
    # Save state
    await system_manager.save_state()
    
    # Create new manager with same state file
    new_manager = SystemManager({'state_file': system_manager.state_file})
    await new_manager.load_state()
    
    assert new_manager.is_hibernating == system_manager.is_hibernating
    assert new_manager.failsafe_enabled == system_manager.failsafe_enabled

@pytest.mark.asyncio
async def test_graceful_shutdown(system_manager):
    """Test graceful shutdown process"""
    # Create some test tasks
    task1 = asyncio.create_task(asyncio.sleep(1))
    task2 = asyncio.create_task(asyncio.sleep(1))
    
    # Trigger shutdown
    await system_manager.graceful_shutdown()
    
    # Check if tasks were cancelled
    assert task1.cancelled()
    assert task2.cancelled()
    
    # Check if state was saved
    assert system_manager.state_file.exists()

@pytest.mark.asyncio
async def test_resource_limits(system_manager):
    """Test resource limits configuration"""
    new_limits = {
        'cpu_percent': 70,
        'memory_percent': 70,
        'disk_percent': 80
    }
    
    await system_manager.set_resource_limits(new_limits)
    assert system_manager.resource_limits == new_limits
    
    # Test with new limits
    with patch('psutil.cpu_percent', return_value=75):
        await asyncio.sleep(1)
        assert system_manager.is_hibernating  # Should hibernate with new lower limit
