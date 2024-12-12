"""Task DAG implementation for managing task dependencies and execution flow."""

import asyncio
from typing import Dict, List, Optional, Set, Any, Callable
import logging
from datetime import datetime
import networkx as nx
from prometheus_client import Counter, Gauge, Histogram


class Task:
    def __init__(
        self,
        task_id: str,
        func: Callable,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None,
        dependencies: Optional[Set[str]] = None,
        timeout: Optional[float] = None,
        retries: int = 0,
        retry_delay: float = 1.0,
    ):
        self.task_id = task_id
        self.func = func
        self.args = args or []
        self.kwargs = kwargs or {}
        self.dependencies = dependencies or set()
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay
        self.status = "pending"
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None
        self.retry_count = 0


class TaskDAG:
    def __init__(self):
        self.logger = logging.getLogger("TaskDAG")
        self.graph = nx.DiGraph()
        self.tasks: Dict[str, Task] = {}

        # Metrics
        self.task_counter = Counter("task_dag_tasks_total", "Total number of tasks", ["status"])
        self.active_tasks = Gauge("task_dag_active_tasks", "Number of currently active tasks")
        self.task_duration = Histogram("task_dag_task_duration_seconds", "Task duration in seconds", ["task_id"])

    def add_task(self, task: Task) -> None:
        """Add a task to the DAG"""
        if task.task_id in self.tasks:
            raise ValueError(f"Task {task.task_id} already exists")

        self.tasks[task.task_id] = task
        self.graph.add_node(task.task_id)

        for dep in task.dependencies:
            if dep not in self.tasks:
                raise ValueError(f"Dependency {dep} not found")
            self.graph.add_edge(dep, task.task_id)

        # Verify no cycles
        if not nx.is_directed_acyclic_graph(self.graph):
            self.graph.remove_node(task.task_id)
            del self.tasks[task.task_id]
            raise ValueError("Adding this task would create a cycle")

        self.task_counter.labels(status="pending").inc()

    async def execute_task(self, task: Task) -> Any:
        """Execute a single task with retries and timeout"""
        task.start_time = datetime.now()
        task.status = "running"
        self.task_counter.labels(status="running").inc()
        self.active_tasks.inc()

        try:
            while task.retry_count <= task.retries:
                try:
                    if task.timeout:
                        result = await asyncio.wait_for(self._run_task(task), timeout=task.timeout)
                    else:
                        result = await self._run_task(task)

                    task.result = result
                    task.status = "completed"
                    task.end_time = datetime.now()

                    duration = (task.end_time - task.start_time).total_seconds()
                    self.task_duration.labels(task_id=task.task_id).observe(duration)

                    self.task_counter.labels(status="completed").inc()
                    return result

                except Exception as e:
                    task.error = str(e)
                    task.retry_count += 1

                    if task.retry_count <= task.retries:
                        await asyncio.sleep(task.retry_delay)
                    else:
                        task.status = "failed"
                        task.end_time = datetime.now()
                        self.task_counter.labels(status="failed").inc()
                        raise

        finally:
            self.active_tasks.dec()

    async def _run_task(self, task: Task) -> Any:
        """Internal method to run a task"""
        if asyncio.iscoroutinefunction(task.func):
            return await task.func(*task.args, **task.kwargs)
        else:
            return task.func(*task.args, **task.kwargs)

    async def execute_dag(self) -> Dict[str, Any]:
        """Execute the entire DAG"""
        try:
            start_time = datetime.now()
            results = {}

            # Get execution order
            try:
                execution_order = list(nx.topological_sort(self.graph))
            except nx.NetworkXUnfeasible:
                raise ValueError("DAG contains cycles")

            # Execute tasks in order
            for task_id in execution_order:
                task = self.tasks[task_id]

                # Wait for dependencies
                for dep in task.dependencies:
                    dep_task = self.tasks[dep]
                    if dep_task.status != "completed":
                        raise RuntimeError(f"Dependency {dep} failed or not completed")

                    # Pass dependency results to task
                    task.kwargs["dep_results"] = {dep: dep_task.result for dep in task.dependencies}

                results[task_id] = await self.execute_task(task)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            return {
                "results": results,
                "duration": duration,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
            }

        except Exception as e:
            self.logger.error(f"DAG execution failed: {str(e)}")
            raise

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a specific task"""
        task = self.tasks.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        return {
            "task_id": task.task_id,
            "status": task.status,
            "start_time": task.start_time.isoformat() if task.start_time else None,
            "end_time": task.end_time.isoformat() if task.end_time else None,
            "duration": (
                (task.end_time - task.start_time).total_seconds() if task.end_time and task.start_time else None
            ),
            "retry_count": task.retry_count,
            "error": task.error,
        }

    def get_dag_status(self) -> Dict[str, Any]:
        """Get status of the entire DAG"""
        task_counts = {"pending": 0, "running": 0, "completed": 0, "failed": 0}

        for task in self.tasks.values():
            task_counts[task.status] += 1

        return {
            "task_counts": task_counts,
            "total_tasks": len(self.tasks),
            "is_running": any(t.status == "running" for t in self.tasks.values()),
            "has_failed": any(t.status == "failed" for t in self.tasks.values()),
        }

    def visualize_dag(self) -> str:
        """Generate a DOT representation of the DAG"""
        try:
            import graphviz

            dot = graphviz.Digraph(comment="Task DAG")

            # Add nodes
            for task_id, task in self.tasks.items():
                color = {"pending": "gray", "running": "yellow", "completed": "green", "failed": "red"}.get(
                    task.status, "gray"
                )

                dot.node(task_id, task_id, color=color)

            # Add edges
            for task_id, task in self.tasks.items():
                for dep in task.dependencies:
                    dot.edge(dep, task_id)

            return dot.source

        except ImportError:
            self.logger.warning("graphviz package not installed")
            return ""
