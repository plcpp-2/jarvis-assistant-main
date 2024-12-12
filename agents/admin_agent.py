from typing import Dict, Any, List, Optional
import logging
import asyncio
from datetime import datetime, timedelta
import json
from pathlib import Path
from prometheus_client import Counter, Gauge, Histogram
from .base_agent import BaseAgent
from ..monitoring.metrics import MetricsManager
from ..system.system_ops import SystemManager

logger = logging.getLogger(__name__)


class AdminAgent(BaseAgent):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.system_manager = SystemManager(config)
        self.metrics_manager = MetricsManager()
        self.alert_thresholds = config.get(
            "alert_thresholds", {"cpu_percent": 90, "memory_percent": 90, "disk_percent": 95, "error_rate": 0.1}
        )

        # Initialize metrics
        self.system_metrics = {
            "cpu_usage": Gauge("system_cpu_usage", "CPU usage percentage"),
            "memory_usage": Gauge("system_memory_usage", "Memory usage percentage"),
            "disk_usage": Gauge("system_disk_usage", "Disk usage percentage"),
            "active_agents": Gauge("active_agents", "Number of active agents"),
            "error_count": Counter("system_errors", "Number of system errors"),
            "task_duration": Histogram("task_duration_seconds", "Task execution duration"),
        }

    async def initialize(self):
        """Initialize admin agent"""
        await super().initialize()
        await self.system_manager.initialize()

        # Start monitoring tasks
        asyncio.create_task(self._monitor_system())
        asyncio.create_task(self._monitor_agents())
        asyncio.create_task(self._monitor_tasks())

        logger.info("Admin agent initialized")

    async def _monitor_system(self):
        """Monitor system resources and health"""
        while True:
            try:
                # Get system status
                status = self.system_manager.get_system_status()

                # Update metrics
                self.system_metrics["cpu_usage"].set(status["cpu_percent"])
                self.system_metrics["memory_usage"].set(status["memory_percent"])
                self.system_metrics["disk_usage"].set(status["disk_percent"])

                # Check thresholds and alert if needed
                await self._check_alerts(status)

                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Error monitoring system: {e}")
                self.system_metrics["error_count"].inc()
                await asyncio.sleep(5)

    async def _monitor_agents(self):
        """Monitor agent health and performance"""
        while True:
            try:
                active_agents = await self._get_active_agents()
                self.system_metrics["active_agents"].set(len(active_agents))

                # Check agent health
                for agent in active_agents:
                    await self._check_agent_health(agent)

                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Error monitoring agents: {e}")
                self.system_metrics["error_count"].inc()
                await asyncio.sleep(5)

    async def _monitor_tasks(self):
        """Monitor task execution and performance"""
        while True:
            try:
                tasks = await self._get_running_tasks()
                for task in tasks:
                    # Record task metrics
                    self.system_metrics["task_duration"].observe(task.get("duration", 0))

                    # Check for long-running tasks
                    if task.get("duration", 0) > self.config.get("max_task_duration", 3600):
                        await self._handle_long_running_task(task)

                await asyncio.sleep(15)
            except Exception as e:
                logger.error(f"Error monitoring tasks: {e}")
                self.system_metrics["error_count"].inc()
                await asyncio.sleep(5)

    async def _check_alerts(self, status: Dict[str, Any]):
        """Check system metrics against thresholds"""
        alerts = []

        if status["cpu_percent"] > self.alert_thresholds["cpu_percent"]:
            alerts.append(f"High CPU usage: {status['cpu_percent']}%")

        if status["memory_percent"] > self.alert_thresholds["memory_percent"]:
            alerts.append(f"High memory usage: {status['memory_percent']}%")

        if status["disk_percent"] > self.alert_thresholds["disk_percent"]:
            alerts.append(f"High disk usage: {status['disk_percent']}%")

        if alerts:
            await self._send_alerts(alerts)

    async def _check_agent_health(self, agent: Dict[str, Any]):
        """Check health of an individual agent"""
        try:
            # Check last heartbeat
            last_heartbeat = datetime.fromisoformat(agent["last_heartbeat"])
            if datetime.now() - last_heartbeat > timedelta(minutes=5):
                await self._handle_unresponsive_agent(agent)

            # Check error rate
            error_rate = agent.get("error_rate", 0)
            if error_rate > self.alert_thresholds["error_rate"]:
                await self._handle_high_error_rate(agent)

        except Exception as e:
            logger.error(f"Error checking agent health: {e}")
            self.system_metrics["error_count"].inc()

    async def _handle_unresponsive_agent(self, agent: Dict[str, Any]):
        """Handle unresponsive agent"""
        logger.warning(f"Agent {agent['id']} is unresponsive")
        try:
            # Attempt to restart agent
            await self._restart_agent(agent)
        except Exception as e:
            logger.error(f"Error handling unresponsive agent: {e}")
            await self._send_alerts([f"Failed to restart agent {agent['id']}"])

    async def _handle_high_error_rate(self, agent: Dict[str, Any]):
        """Handle agent with high error rate"""
        logger.warning(f"High error rate for agent {agent['id']}")
        try:
            # Analyze error patterns
            error_analysis = await self._analyze_errors(agent)

            # Take corrective action
            await self._apply_corrective_action(agent, error_analysis)

        except Exception as e:
            logger.error(f"Error handling high error rate: {e}")
            await self._send_alerts([f"High error rate for agent {agent['id']}"])

    async def _handle_long_running_task(self, task: Dict[str, Any]):
        """Handle long-running task"""
        logger.warning(f"Long-running task detected: {task['id']}")
        try:
            # Check if task should be terminated
            if await self._should_terminate_task(task):
                await self._terminate_task(task)
                await self._send_alerts([f"Terminated long-running task {task['id']}"])
        except Exception as e:
            logger.error(f"Error handling long-running task: {e}")

    async def _send_alerts(self, alerts: List[str]):
        """Send system alerts"""
        try:
            # Log alerts
            for alert in alerts:
                logger.warning(f"System Alert: {alert}")

            # Send notifications (implement based on notification system)
            # await self.notification_manager.send_alerts(alerts)

        except Exception as e:
            logger.error(f"Error sending alerts: {e}")
            self.system_metrics["error_count"].inc()

    async def get_system_report(self) -> Dict[str, Any]:
        """Generate system status report"""
        try:
            return {
                "timestamp": datetime.now().isoformat(),
                "system_status": self.system_manager.get_system_status(),
                "active_agents": len(await self._get_active_agents()),
                "running_tasks": len(await self._get_running_tasks()),
                "error_count": self.system_metrics["error_count"]._value.get(),
                "metrics": {
                    "cpu_usage": self.system_metrics["cpu_usage"]._value.get(),
                    "memory_usage": self.system_metrics["memory_usage"]._value.get(),
                    "disk_usage": self.system_metrics["disk_usage"]._value.get(),
                },
            }
        except Exception as e:
            logger.error(f"Error generating system report: {e}")
            return {}
