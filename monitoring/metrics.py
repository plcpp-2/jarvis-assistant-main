from prometheus_client import Counter, Gauge, Histogram, Info
from typing import Dict
import time


class MetricsManager:
    def __init__(self):
        # Task metrics
        self.task_counter = Counter("jarvis_tasks_total", "Total number of tasks processed", ["type", "status"])

        self.task_duration = Histogram("jarvis_task_duration_seconds", "Task processing duration in seconds", ["type"])

        # Agent metrics
        self.active_agents = Gauge("jarvis_active_agents", "Number of active agents", ["role"])

        self.agent_performance = Gauge("jarvis_agent_performance", "Agent performance metrics", ["agent_id", "metric"])

        # System metrics
        self.system_resources = Gauge("jarvis_system_resources", "System resource usage", ["resource"])

        self.system_info = Info("jarvis_system", "System information")

        # Learning metrics
        self.model_accuracy = Gauge("jarvis_model_accuracy", "Model accuracy metrics", ["model_name"])

    def record_task(self, task_type: str, status: str):
        """Record task execution"""
        self.task_counter.labels(type=task_type, status=status).inc()

    def record_task_duration(self, task_type: str, duration: float):
        """Record task duration"""
        self.task_duration.labels(type=task_type).observe(duration)

    def update_agent_count(self, role: str, count: int):
        """Update active agent count"""
        self.active_agents.labels(role=role).set(count)

    def update_agent_metrics(self, agent_id: str, metrics: Dict[str, float]):
        """Update agent performance metrics"""
        for metric, value in metrics.items():
            self.agent_performance.labels(agent_id=agent_id, metric=metric).set(value)

    def update_system_resources(self, metrics: Dict[str, float]):
        """Update system resource metrics"""
        for resource, value in metrics.items():
            self.system_resources.labels(resource=resource).set(value)

    def update_system_info(self, info: Dict[str, str]):
        """Update system information"""
        self.system_info.info(info)

    def update_model_accuracy(self, model_name: str, accuracy: float):
        """Update model accuracy metrics"""
        self.model_accuracy.labels(model_name=model_name).set(accuracy)


class MetricsDecorator:
    def __init__(self, metrics_manager: MetricsManager):
        self.metrics = metrics_manager

    def track_task(self, task_type: str):
        """Decorator to track task execution"""

        def decorator(func):
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    self.metrics.record_task(task_type, "success")
                    return result
                except Exception as e:
                    self.metrics.record_task(task_type, "failure")
                    raise
                finally:
                    duration = time.time() - start_time
                    self.metrics.record_task_duration(task_type, duration)

            return wrapper

        return decorator
