import asyncio
import os
import psutil
import platform
import subprocess
from typing import Dict, List, Optional, Union
import logging
from datetime import datetime
import json


class SystemExecutor:
    def __init__(self):
        self.logger = logging.getLogger("SystemExecutor")
        self.running_processes: Dict[str, asyncio.subprocess.Process] = {}
        self.process_outputs: Dict[str, List[str]] = {}

    async def execute_command(
        self,
        command: Union[str, List[str]],
        process_id: str,
        shell: bool = False,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Union[int, str, List[str]]]:
        """Execute a system command asynchronously"""
        try:
            if isinstance(command, str) and not shell:
                command = command.split()

            # Create process
            process = await asyncio.create_subprocess_shell(
                command if shell else " ".join(command),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env,
            )

            self.running_processes[process_id] = process
            self.process_outputs[process_id] = []

            # Wait for process with timeout
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout)
            except asyncio.TimeoutError:
                process.terminate()
                await process.wait()
                raise TimeoutError(f"Command execution timed out after {timeout}s")

            # Store output
            output = []
            if stdout:
                output.extend(stdout.decode().splitlines())
            if stderr:
                output.extend(stderr.decode().splitlines())

            self.process_outputs[process_id] = output

            return {"process_id": process_id, "return_code": process.returncode, "output": output}

        except Exception as e:
            self.logger.error(f"Command execution failed: {str(e)}")
            raise

    async def execute_script(
        self,
        script_path: str,
        process_id: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Union[int, str, List[str]]]:
        """Execute a script file"""
        try:
            if not os.path.exists(script_path):
                raise FileNotFoundError(f"Script not found: {script_path}")

            # Determine interpreter based on file extension
            extension = os.path.splitext(script_path)[1].lower()
            interpreter = {".py": "python", ".sh": "bash", ".js": "node", ".ps1": "powershell"}.get(extension)

            if not interpreter:
                raise ValueError(f"Unsupported script type: {extension}")

            command = [interpreter, script_path]
            if args:
                command.extend(args)

            return await self.execute_command(command, process_id, shell=False, env=env, timeout=timeout)

        except Exception as e:
            self.logger.error(f"Script execution failed: {str(e)}")
            raise

    async def kill_process(self, process_id: str) -> bool:
        """Kill a running process"""
        try:
            process = self.running_processes.get(process_id)
            if not process:
                return False

            process.terminate()
            await process.wait()

            del self.running_processes[process_id]
            return True

        except Exception as e:
            self.logger.error(f"Failed to kill process {process_id}: {str(e)}")
            return False

    def get_system_info(self) -> Dict[str, Union[str, float, int]]:
        """Get system information"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": cpu_percent,
                "memory_total": memory.total,
                "memory_available": memory.available,
                "memory_percent": memory.percent,
                "disk_total": disk.total,
                "disk_free": disk.free,
                "disk_percent": disk.percent,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Failed to get system info: {str(e)}")
            raise

    def get_process_info(self, process_id: str) -> Optional[Dict[str, Union[str, float, int]]]:
        """Get information about a specific process"""
        try:
            process = self.running_processes.get(process_id)
            if not process:
                return None

            proc = psutil.Process(process.pid)

            return {
                "process_id": process_id,
                "pid": proc.pid,
                "status": proc.status(),
                "cpu_percent": proc.cpu_percent(),
                "memory_percent": proc.memory_percent(),
                "create_time": datetime.fromtimestamp(proc.create_time()).isoformat(),
                "command": " ".join(proc.cmdline()),
                "output": self.process_outputs.get(process_id, []),
            }

        except Exception as e:
            self.logger.error(f"Failed to get process info: {str(e)}")
            return None

    async def execute_parallel_commands(
        self, commands: List[Dict[str, Union[str, List[str]]]], timeout: Optional[float] = None
    ) -> List[Dict[str, Union[int, str, List[str]]]]:
        """Execute multiple commands in parallel"""
        try:
            tasks = []
            for cmd in commands:
                process_id = cmd.get("process_id", str(len(tasks)))
                command = cmd.get("command")
                shell = cmd.get("shell", False)
                cwd = cmd.get("cwd")
                env = cmd.get("env")

                task = self.execute_command(command, process_id, shell, cwd, env, timeout)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [result if not isinstance(result, Exception) else {"error": str(result)} for result in results]

        except Exception as e:
            self.logger.error(f"Parallel execution failed: {str(e)}")
            raise

    async def monitor_process_resources(
        self, process_id: str, interval: float = 1.0, duration: Optional[float] = None
    ) -> List[Dict[str, Union[float, str]]]:
        """Monitor process resource usage over time"""
        try:
            process = self.running_processes.get(process_id)
            if not process:
                raise ValueError(f"Process {process_id} not found")

            proc = psutil.Process(process.pid)
            measurements = []
            start_time = datetime.now()

            while True:
                if duration and (datetime.now() - start_time).total_seconds() > duration:
                    break

                measurements.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "cpu_percent": proc.cpu_percent(),
                        "memory_percent": proc.memory_percent(),
                        "status": proc.status(),
                    }
                )

                await asyncio.sleep(interval)

            return measurements

        except Exception as e:
            self.logger.error(f"Process monitoring failed: {str(e)}")
            raise


if __name__ == "__main__":

    async def main():
        executor = SystemExecutor()

        # Execute a simple command
        result = await executor.execute_command("echo 'Hello, World!'", "test1", shell=True)
        print("Command result:", json.dumps(result, indent=2))

        # Get system information
        system_info = executor.get_system_info()
        print("System info:", json.dumps(system_info, indent=2))

        # Execute parallel commands
        parallel_results = await executor.execute_parallel_commands(
            [{"command": "echo 'Command 1'", "shell": True}, {"command": "echo 'Command 2'", "shell": True}]
        )
        print("Parallel results:", json.dumps(parallel_results, indent=2))

    asyncio.run(main())
