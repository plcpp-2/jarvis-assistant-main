import pytest
import asyncio
import networkx as nx
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from jarvis_assistant.agents.task_dag import TaskDAG, Task

@pytest.fixture
async def task_dag():
    """Create a TaskDAG instance for testing"""
    return TaskDAG()

async def dummy_task():
    """Dummy task for testing"""
    await asyncio.sleep(0.1)
    return "dummy result"

async def failing_task():
    """Task that fails for testing"""
    raise ValueError("Task failed")

@pytest.mark.asyncio
async def test_add_task(task_dag):
    """Test adding tasks to the DAG"""
    task = Task("task1", dummy_task)
    task_dag.add_task(task)
    
    assert "task1" in task_dag.tasks
    assert task_dag.graph.has_node("task1")
    
    # Test adding task with dependencies
    task2 = Task("task2", dummy_task, dependencies={"task1"})
    task_dag.add_task(task2)
    
    assert task_dag.graph.has_edge("task1", "task2")
    
    # Test cycle detection
    task3 = Task("task3", dummy_task, dependencies={"task2"})
    task_dag.add_task(task3)
    
    with pytest.raises(ValueError):
        task1_cyclic = Task("task1", dummy_task, dependencies={"task3"})
        task_dag.add_task(task1_cyclic)

@pytest.mark.asyncio
async def test_execute_task(task_dag):
    """Test executing a single task"""
    task = Task("task1", dummy_task)
    task_dag.add_task(task)
    
    result = await task_dag.execute_task(task)
    assert result == "dummy result"
    assert task.status == "completed"
    assert task.result == "dummy result"
    assert task.error is None

@pytest.mark.asyncio
async def test_task_retry(task_dag):
    """Test task retry mechanism"""
    attempt_count = 0
    
    async def retry_task():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ValueError("Temporary failure")
        return "success"
    
    task = Task(
        "retry_task",
        retry_task,
        retries=3,
        retry_delay=0.1
    )
    task_dag.add_task(task)
    
    result = await task_dag.execute_task(task)
    assert result == "success"
    assert task.status == "completed"
    assert attempt_count == 3

@pytest.mark.asyncio
async def test_task_timeout(task_dag):
    """Test task timeout"""
    async def slow_task():
        await asyncio.sleep(0.5)
        return "done"
    
    task = Task(
        "slow_task",
        slow_task,
        timeout=0.1
    )
    task_dag.add_task(task)
    
    with pytest.raises(asyncio.TimeoutError):
        await task_dag.execute_task(task)
    
    assert task.status == "failed"

@pytest.mark.asyncio
async def test_execute_dag(task_dag):
    """Test executing the entire DAG"""
    # Create a simple DAG
    task1 = Task("task1", dummy_task)
    task2 = Task("task2", dummy_task, dependencies={"task1"})
    task3 = Task("task3", dummy_task, dependencies={"task1"})
    task4 = Task("task4", dummy_task, dependencies={"task2", "task3"})
    
    for task in [task1, task2, task3, task4]:
        task_dag.add_task(task)
    
    result = await task_dag.execute_dag()
    
    assert all(task.status == "completed" for task in task_dag.tasks.values())
    assert all(isinstance(r, str) for r in result['results'].values())
    assert result['duration'] > 0

@pytest.mark.asyncio
async def test_dag_error_handling(task_dag):
    """Test DAG error handling"""
    task1 = Task("task1", dummy_task)
    task2 = Task("task2", failing_task, dependencies={"task1"})
    task3 = Task("task3", dummy_task, dependencies={"task1"})
    
    for task in [task1, task2, task3]:
        task_dag.add_task(task)
    
    with pytest.raises(RuntimeError):
        await task_dag.execute_dag()
    
    assert task1.status == "completed"
    assert task2.status == "failed"
    assert task3.status == "completed"

@pytest.mark.asyncio
async def test_get_task_status(task_dag):
    """Test getting task status"""
    task = Task("task1", dummy_task)
    task_dag.add_task(task)
    
    await task_dag.execute_task(task)
    status = task_dag.get_task_status("task1")
    
    assert status['task_id'] == "task1"
    assert status['status'] == "completed"
    assert status['error'] is None
    assert status['duration'] > 0

@pytest.mark.asyncio
async def test_get_dag_status(task_dag):
    """Test getting DAG status"""
    task1 = Task("task1", dummy_task)
    task2 = Task("task2", failing_task)
    
    for task in [task1, task2]:
        task_dag.add_task(task)
    
    try:
        await task_dag.execute_dag()
    except:
        pass
    
    status = task_dag.get_dag_status()
    
    assert status['total_tasks'] == 2
    assert status['task_counts']['completed'] == 1
    assert status['task_counts']['failed'] == 1
    assert status['has_failed'] is True

@pytest.mark.asyncio
async def test_visualize_dag(task_dag):
    """Test DAG visualization"""
    task1 = Task("task1", dummy_task)
    task2 = Task("task2", dummy_task, dependencies={"task1"})
    task3 = Task("task3", dummy_task, dependencies={"task1"})
    
    for task in [task1, task2, task3]:
        task_dag.add_task(task)
    
    dot = task_dag.visualize_dag()
    
    assert isinstance(dot, str)
    assert "task1" in dot
    assert "task2" in dot
    assert "task3" in dot
