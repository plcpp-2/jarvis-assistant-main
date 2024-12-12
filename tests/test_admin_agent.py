import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from prometheus_client import CollectorRegistry
from jarvis_assistant.agents.admin_agent import AdminAgent
from jarvis_assistant.system.system_ops import SystemManager


@pytest.fixture
async def admin_agent():
    """Create an admin agent instance for testing"""
    config = {
        "monitoring_interval": 1,
        "alert_thresholds": {"cpu_percent": 80, "memory_percent": 80, "error_rate": 0.1},
        "metrics_prefix": "test_jarvis",
    }

    registry = CollectorRegistry()
    system_manager = SystemManager({})
    agent = AdminAgent(config, system_manager, registry)
    await agent.initialize()
    yield agent
    await agent.cleanup()


@pytest.mark.asyncio
async def test_agent_initialization(admin_agent):
    """Test admin agent initialization"""
    assert admin_agent.is_running
    assert admin_agent.metrics_registry is not None
    assert admin_agent.system_manager is not None


@pytest.mark.asyncio
async def test_metrics_collection(admin_agent):
    """Test metrics collection"""
    # Mock system metrics
    system_metrics = {
        "cpu_percent": 50,
        "memory_percent": 60,
        "disk_percent": 70,
        "network_io": {"bytes_sent": 1000, "bytes_recv": 2000},
        "error_count": 5,
        "active_tasks": 10,
    }

    with patch.object(admin_agent.system_manager, "get_system_status", return_value=system_metrics):
        # Collect metrics
        await admin_agent._collect_metrics()

        # Verify metrics were recorded
        metrics = {}
        for metric in admin_agent.metrics_registry.collect():
            for sample in metric.samples:
                metrics[sample.name] = sample.value

        assert metrics["test_jarvis_cpu_usage"] == 50
        assert metrics["test_jarvis_memory_usage"] == 60
        assert metrics["test_jarvis_disk_usage"] == 70
        assert metrics["test_jarvis_network_bytes_sent"] == 1000
        assert metrics["test_jarvis_network_bytes_received"] == 2000
        assert metrics["test_jarvis_error_count"] == 5
        assert metrics["test_jarvis_active_tasks"] == 10


@pytest.mark.asyncio
async def test_alert_generation(admin_agent):
    """Test alert generation"""
    # Mock high CPU usage
    system_metrics = {"cpu_percent": 90, "memory_percent": 50, "error_count": 0}

    with patch.object(admin_agent.system_manager, "get_system_status", return_value=system_metrics):
        # Check for alerts
        alerts = await admin_agent._check_alerts()

        assert len(alerts) == 1
        assert alerts[0]["type"] == "high_cpu_usage"
        assert alerts[0]["value"] == 90


@pytest.mark.asyncio
async def test_health_check(admin_agent):
    """Test health check functionality"""
    # Mock healthy system
    with patch.object(admin_agent.system_manager, "get_system_status", return_value={"error_count": 0}):
        health_status = await admin_agent.check_health()
        assert health_status["status"] == "healthy"

    # Mock unhealthy system
    with patch.object(admin_agent.system_manager, "get_system_status", return_value={"error_count": 100}):
        health_status = await admin_agent.check_health()
        assert health_status["status"] == "unhealthy"


@pytest.mark.asyncio
async def test_error_handling(admin_agent):
    """Test error handling"""
    # Mock system error
    error = Exception("Test error")
    with patch.object(admin_agent.system_manager, "get_system_status", side_effect=error):
        # Should not raise exception
        await admin_agent._collect_metrics()

        # Check error was recorded
        assert admin_agent.error_count > 0


@pytest.mark.asyncio
async def test_task_monitoring(admin_agent):
    """Test task monitoring"""
    # Create test tasks
    task1 = asyncio.create_task(asyncio.sleep(0.1))
    task2 = asyncio.create_task(asyncio.sleep(0.1))

    # Monitor tasks
    task_status = await admin_agent.monitor_tasks([task1, task2])

    assert len(task_status) == 2
    assert all(status["status"] == "running" for status in task_status)

    # Wait for tasks to complete
    await asyncio.gather(task1, task2)

    task_status = await admin_agent.monitor_tasks([task1, task2])
    assert all(status["status"] == "completed" for status in task_status)


@pytest.mark.asyncio
async def test_metric_history(admin_agent):
    """Test metric history tracking"""
    # Mock metrics over time
    metrics_sequence = [{"cpu_percent": 50}, {"cpu_percent": 60}, {"cpu_percent": 70}]

    for metrics in metrics_sequence:
        with patch.object(admin_agent.system_manager, "get_system_status", return_value=metrics):
            await admin_agent._collect_metrics()
            await asyncio.sleep(0.1)

    history = admin_agent.get_metric_history("cpu_percent")
    assert len(history) == 3
    assert history[-1] == 70


@pytest.mark.asyncio
async def test_alert_throttling(admin_agent):
    """Test alert throttling"""
    # Mock continuous high CPU
    with patch.object(admin_agent.system_manager, "get_system_status", return_value={"cpu_percent": 90}):
        # First alert should be generated
        alerts1 = await admin_agent._check_alerts()
        assert len(alerts1) == 1

        # Immediate second check should be throttled
        alerts2 = await admin_agent._check_alerts()
        assert len(alerts2) == 0

        # Wait for throttle period
        await asyncio.sleep(admin_agent.alert_throttle_period)

        # Should generate new alert
        alerts3 = await admin_agent._check_alerts()
        assert len(alerts3) == 1
