import asyncio
import psutil
import logging
import signal
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path
import aiofiles
import yaml

logger = logging.getLogger(__name__)


class SystemManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.hibernation_threshold = config.get("hibernation_threshold", 0.1)  # 10% activity
        self.hibernation_period = config.get("hibernation_period", 300)  # 5 minutes
        self.last_activity = datetime.now()
        self.is_hibernating = False
        self.shutdown_requested = False
        self.failsafe_enabled = True
        self.state_file = Path(config.get("state_file", "system_state.json"))
        self.resource_limits = config.get(
            "resource_limits", {"cpu_percent": 80, "memory_percent": 80, "disk_percent": 90}
        )

    async def initialize(self):
        """Initialize system manager"""
        # Register signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        # Load previous state if exists
        await self.load_state()

        # Start monitoring tasks
        asyncio.create_task(self._monitor_resources())
        asyncio.create_task(self._check_hibernation())

        logger.info("System manager initialized")

    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        self.shutdown_requested = True
        if self.failsafe_enabled:
            asyncio.create_task(self.graceful_shutdown())

    async def graceful_shutdown(self):
        """Perform graceful shutdown"""
        logger.info("Initiating graceful shutdown...")

        try:
            # Save current state
            await self.save_state()

            # Stop all running tasks
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            for task in tasks:
                task.cancel()

            await asyncio.gather(*tasks, return_exceptions=True)

            # Cleanup resources
            await self.cleanup()

            logger.info("Graceful shutdown completed")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            sys.exit(1)

    async def cleanup(self):
        """Cleanup system resources"""
        try:
            # Close file handles
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)

            # Additional cleanup as needed
            pass

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def save_state(self):
        """Save system state to file"""
        state = {
            "timestamp": datetime.now().isoformat(),
            "is_hibernating": self.is_hibernating,
            "last_activity": self.last_activity.isoformat(),
            "failsafe_enabled": self.failsafe_enabled,
        }

        async with aiofiles.open(self.state_file, "w") as f:
            await f.write(json.dumps(state, indent=2))

    async def load_state(self):
        """Load system state from file"""
        try:
            if self.state_file.exists():
                async with aiofiles.open(self.state_file, "r") as f:
                    state = json.loads(await f.read())
                    self.is_hibernating = state.get("is_hibernating", False)
                    self.last_activity = datetime.fromisoformat(state["last_activity"])
                    self.failsafe_enabled = state.get("failsafe_enabled", True)
        except Exception as e:
            logger.error(f"Error loading state: {e}")

    async def _monitor_resources(self):
        """Monitor system resources"""
        while not self.shutdown_requested:
            try:
                cpu_percent = psutil.cpu_percent()
                memory_percent = psutil.virtual_memory().percent
                disk_percent = psutil.disk_usage("/").percent

                # Check resource limits
                if (
                    cpu_percent > self.resource_limits["cpu_percent"]
                    or memory_percent > self.resource_limits["memory_percent"]
                    or disk_percent > self.resource_limits["disk_percent"]
                ):
                    logger.warning("Resource limits exceeded!")
                    if self.failsafe_enabled:
                        await self.enter_hibernation()

                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error monitoring resources: {e}")
                await asyncio.sleep(5)

    async def _check_hibernation(self):
        """Check if system should hibernate"""
        while not self.shutdown_requested:
            try:
                if not self.is_hibernating:
                    time_since_activity = (datetime.now() - self.last_activity).total_seconds()
                    if time_since_activity > self.hibernation_period:
                        await self.enter_hibernation()

                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Error checking hibernation: {e}")
                await asyncio.sleep(5)

    async def enter_hibernation(self):
        """Enter hibernation mode"""
        if not self.is_hibernating:
            logger.info("Entering hibernation mode...")
            self.is_hibernating = True

            # Stop non-essential services
            # Reduce resource usage
            # Save state
            await self.save_state()

    async def exit_hibernation(self):
        """Exit hibernation mode"""
        if self.is_hibernating:
            logger.info("Exiting hibernation mode...")
            self.is_hibernating = False
            self.last_activity = datetime.now()

            # Restore services
            # Resume normal operation
            await self.save_state()

    async def record_activity(self):
        """Record system activity"""
        self.last_activity = datetime.now()
        if self.is_hibernating:
            await self.exit_hibernation()

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
            "is_hibernating": self.is_hibernating,
            "last_activity": self.last_activity.isoformat(),
            "failsafe_enabled": self.failsafe_enabled,
        }

    async def toggle_failsafe(self, enabled: bool):
        """Toggle failsafe system"""
        self.failsafe_enabled = enabled
        await self.save_state()
        logger.info(f"Failsafe {'enabled' if enabled else 'disabled'}")

    async def set_resource_limits(self, limits: Dict[str, float]):
        """Update resource limits"""
        self.resource_limits.update(limits)
        logger.info(f"Resource limits updated: {self.resource_limits}")


class SystemOperations(SystemManager):
    @staticmethod
    def get_system_info() -> Dict[str, str]:
        """Get basic system information."""
        return {
            "system": platform.system(),
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        }

    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """Get memory usage statistics."""
        memory = psutil.virtual_memory()
        return {
            "total": memory.total / (1024**3),  # GB
            "available": memory.available / (1024**3),  # GB
            "percent": memory.percent,
        }

    @staticmethod
    def get_disk_usage() -> Dict[str, float]:
        """Get disk usage statistics."""
        disk = psutil.disk_usage("/")
        return {
            "total": disk.total / (1024**3),  # GB
            "used": disk.used / (1024**3),  # GB
            "free": disk.free / (1024**3),  # GB
            "percent": disk.percent,
        }

    @staticmethod
    def get_running_processes() -> List[Dict[str, str]]:
        """Get list of running processes."""
        processes = []
        for proc in psutil.process_iter(["pid", "name", "status"]):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return processes

    @staticmethod
    def execute_command(command: str) -> Dict[str, str]:
        """Execute a system command."""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return {"stdout": result.stdout, "stderr": result.stderr, "return_code": str(result.returncode)}
        except Exception as e:
            return {"error": str(e)}
