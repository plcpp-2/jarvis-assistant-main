import asyncio
import json
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import websockets
import logging
from concurrent.futures import ThreadPoolExecutor
from queue import PriorityQueue
import traceback


@dataclass
class TaskContext:
    task_id: str
    priority: int
    dependencies: List[str]
    timeout: Optional[int]
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = datetime.now()


class TaskExecutor:
    def __init__(self):
        self.task_queue = PriorityQueue()
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_results: Dict[str, any] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.ws = None
        self.logger = logging.getLogger("TaskExecutor")

    async def connect_websocket(self):
        try:
            self.ws = await websockets.connect("ws://localhost:8000/ws/task-executor/agents")
            asyncio.create_task(self.listen_for_commands())
        except Exception as e:
            self.logger.error(f"WebSocket connection failed: {e}")

    async def listen_for_commands(self):
        while True:
            try:
                message = await self.ws.recv()
                data = json.loads(message)
                if data["message_type"] == "task_request":
                    await self.handle_task_request(data["content"])
                elif data["message_type"] == "task_cancel":
                    await self.cancel_task(data["content"]["task_id"])
            except Exception as e:
                self.logger.error(f"Error in command listener: {e}")
                await asyncio.sleep(5)

    async def handle_task_request(self, content: Dict):
        context = TaskContext(
            task_id=content["task_id"],
            priority=content.get("priority", 5),
            dependencies=content.get("dependencies", []),
            timeout=content.get("timeout"),
        )

        # Check dependencies
        for dep in context.dependencies:
            if dep not in self.task_results:
                await self.send_status_update(context.task_id, "waiting_dependencies")
                return

        await self.execute_task(content["task_type"], content["parameters"], context)

    async def execute_task(self, task_type: str, parameters: Dict, context: TaskContext):
        try:
            # Create task wrapper
            task = asyncio.create_task(self._execute_task_with_timeout(task_type, parameters, context))
            self.active_tasks[context.task_id] = task

            # Wait for task completion
            await task

        except asyncio.TimeoutError:
            await self.send_status_update(
                context.task_id, "timeout", error=f"Task exceeded timeout of {context.timeout}s"
            )
        except Exception as e:
            if context.retry_count < context.max_retries:
                context.retry_count += 1
                await self.execute_task(task_type, parameters, context)
            else:
                await self.send_status_update(context.task_id, "failed", error=str(e), traceback=traceback.format_exc())

    async def _execute_task_with_timeout(self, task_type: str, parameters: Dict, context: TaskContext):
        await self.send_status_update(context.task_id, "started")

        try:
            # Execute task based on type
            if task_type == "browser_action":
                result = await self._execute_browser_task(parameters)
            elif task_type == "file_operation":
                result = await self._execute_file_task(parameters)
            elif task_type == "api_call":
                result = await self._execute_api_task(parameters)
            elif task_type == "ml_inference":
                result = await self._execute_ml_task(parameters)
            else:
                raise ValueError(f"Unknown task type: {task_type}")

            # Store and report results
            self.task_results[context.task_id] = result
            await self.send_status_update(context.task_id, "completed", result=result)

        except Exception as e:
            raise

    async def _execute_browser_task(self, parameters: Dict) -> Dict:
        # Send command to browser extension
        await self.ws.send(json.dumps({"message_type": "browser_command", "content": parameters}))

        # Wait for response
        response = await self.ws.recv()
        return json.loads(response)["content"]

    async def _execute_file_task(self, parameters: Dict) -> Dict:
        operation = parameters["operation"]
        path = parameters["path"]

        if operation == "read":
            with open(path, "r") as f:
                content = f.read()
            return {"content": content}
        elif operation == "write":
            with open(path, "w") as f:
                f.write(parameters["content"])
            return {"success": True}
        else:
            raise ValueError(f"Unknown file operation: {operation}")

    async def _execute_api_task(self, parameters: Dict) -> Dict:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            method = parameters["method"].lower()
            url = parameters["url"]

            async with getattr(session, method)(
                url, json=parameters.get("data"), headers=parameters.get("headers", {})
            ) as response:
                return {"status": response.status, "data": await response.json()}

    async def _execute_ml_task(self, parameters: Dict) -> Dict:
        # Execute in thread pool to avoid blocking
        model_name = parameters["model"]
        input_data = parameters["input"]

        def run_inference(model_name: str, data: Union[str, Dict]):
            # Import ML libraries lazily
            import torch
            from transformers import pipeline

            # Load model and run inference
            pipe = pipeline(model_name)
            return pipe(data)

        result = await asyncio.get_event_loop().run_in_executor(self.executor, run_inference, model_name, input_data)

        return {"result": result}

    async def cancel_task(self, task_id: str):
        if task_id in self.active_tasks:
            self.active_tasks[task_id].cancel()
            await self.send_status_update(task_id, "cancelled")

    async def send_status_update(self, task_id: str, status: str, **kwargs):
        if self.ws:
            await self.ws.send(
                json.dumps(
                    {
                        "message_type": "task_status",
                        "content": {
                            "task_id": task_id,
                            "status": status,
                            "timestamp": datetime.now().isoformat(),
                            **kwargs,
                        },
                    }
                )
            )


if __name__ == "__main__":
    executor = TaskExecutor()
    asyncio.run(executor.connect_websocket())
