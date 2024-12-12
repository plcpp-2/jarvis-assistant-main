import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Callable, Any
import json
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor


class TaskScheduler:
    def __init__(self, redis_url: str):
        self.logger = logging.getLogger("TaskScheduler")

        # Configure job stores
        jobstores = {
            "default": RedisJobStore(
                jobs_key="jarvis_scheduler.jobs", run_times_key="jarvis_scheduler.run_times", host=redis_url
            )
        }

        # Configure executors
        executors = {"default": ThreadPoolExecutor(20), "processpool": ProcessPoolExecutor(5)}

        # Create scheduler
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults={"coalesce": False, "max_instances": 3, "misfire_grace_time": 30},
        )

    async def start(self):
        """Start the scheduler"""
        self.scheduler.start()
        self.logger.info("Scheduler started")

    async def shutdown(self):
        """Shutdown the scheduler"""
        self.scheduler.shutdown()
        self.logger.info("Scheduler shutdown")

    async def schedule_task(
        self,
        task_id: str,
        func: Callable,
        trigger_type: str,
        trigger_args: Dict[str, Any],
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None,
        executor: str = "default",
        **job_kwargs,
    ) -> str:
        """Schedule a new task"""
        try:
            # Create trigger based on type
            if trigger_type == "date":
                trigger = DateTrigger(**trigger_args)
            elif trigger_type == "interval":
                trigger = IntervalTrigger(**trigger_args)
            elif trigger_type == "cron":
                trigger = CronTrigger(**trigger_args)
            else:
                raise ValueError(f"Invalid trigger type: {trigger_type}")

            # Add job to scheduler
            job = self.scheduler.add_job(
                func, trigger=trigger, args=args or [], kwargs=kwargs or {}, id=task_id, executor=executor, **job_kwargs
            )

            self.logger.info(f"Scheduled task {task_id} with trigger {trigger_type}")
            return job.id

        except Exception as e:
            self.logger.error(f"Failed to schedule task {task_id}: {str(e)}")
            raise

    async def schedule_recurring_task(
        self,
        task_id: str,
        func: Callable,
        interval: Union[int, timedelta],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None,
        executor: str = "default",
        **job_kwargs,
    ) -> str:
        """Schedule a recurring task with interval trigger"""
        try:
            if isinstance(interval, int):
                interval = timedelta(seconds=interval)

            trigger_args = {"interval": interval, "start_date": start_date, "end_date": end_date}

            return await self.schedule_task(
                task_id, func, "interval", trigger_args, args, kwargs, executor, **job_kwargs
            )

        except Exception as e:
            self.logger.error(f"Failed to schedule recurring task {task_id}: {str(e)}")
            raise

    async def schedule_cron_task(
        self,
        task_id: str,
        func: Callable,
        cron_expression: str,
        args: Optional[List] = None,
        kwargs: Optional[Dict] = None,
        executor: str = "default",
        **job_kwargs,
    ) -> str:
        """Schedule a task with cron trigger"""
        try:
            # Parse cron expression
            cron_fields = cron_expression.split()
            trigger_args = {}

            if len(cron_fields) == 5:
                trigger_args.update(
                    {
                        "minute": cron_fields[0],
                        "hour": cron_fields[1],
                        "day": cron_fields[2],
                        "month": cron_fields[3],
                        "day_of_week": cron_fields[4],
                    }
                )
            else:
                raise ValueError("Invalid cron expression")

            return await self.schedule_task(task_id, func, "cron", trigger_args, args, kwargs, executor, **job_kwargs)

        except Exception as e:
            self.logger.error(f"Failed to schedule cron task {task_id}: {str(e)}")
            raise

    async def pause_task(self, task_id: str):
        """Pause a scheduled task"""
        try:
            self.scheduler.pause_job(task_id)
            self.logger.info(f"Paused task {task_id}")
        except Exception as e:
            self.logger.error(f"Failed to pause task {task_id}: {str(e)}")
            raise

    async def resume_task(self, task_id: str):
        """Resume a paused task"""
        try:
            self.scheduler.resume_job(task_id)
            self.logger.info(f"Resumed task {task_id}")
        except Exception as e:
            self.logger.error(f"Failed to resume task {task_id}: {str(e)}")
            raise

    async def remove_task(self, task_id: str):
        """Remove a scheduled task"""
        try:
            self.scheduler.remove_job(task_id)
            self.logger.info(f"Removed task {task_id}")
        except Exception as e:
            self.logger.error(f"Failed to remove task {task_id}: {str(e)}")
            raise

    async def get_task_info(self, task_id: str) -> Dict[str, Any]:
        """Get information about a scheduled task"""
        try:
            job = self.scheduler.get_job(task_id)
            if not job:
                raise ValueError(f"Task {task_id} not found")

            return {
                "id": job.id,
                "name": job.name,
                "trigger": str(job.trigger),
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "executor": job.executor,
                "status": "paused" if job.next_run_time is None else "active",
            }

        except Exception as e:
            self.logger.error(f"Failed to get task info for {task_id}: {str(e)}")
            raise

    async def list_tasks(self) -> List[Dict[str, Any]]:
        """List all scheduled tasks"""
        try:
            jobs = self.scheduler.get_jobs()
            return [
                {
                    "id": job.id,
                    "name": job.name,
                    "trigger": str(job.trigger),
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                    "executor": job.executor,
                    "status": "paused" if job.next_run_time is None else "active",
                }
                for job in jobs
            ]

        except Exception as e:
            self.logger.error(f"Failed to list tasks: {str(e)}")
            raise

    async def modify_task(
        self,
        task_id: str,
        trigger_type: Optional[str] = None,
        trigger_args: Optional[Dict[str, Any]] = None,
        **job_kwargs,
    ):
        """Modify an existing task's schedule"""
        try:
            job = self.scheduler.get_job(task_id)
            if not job:
                raise ValueError(f"Task {task_id} not found")

            if trigger_type and trigger_args:
                if trigger_type == "date":
                    trigger = DateTrigger(**trigger_args)
                elif trigger_type == "interval":
                    trigger = IntervalTrigger(**trigger_args)
                elif trigger_type == "cron":
                    trigger = CronTrigger(**trigger_args)
                else:
                    raise ValueError(f"Invalid trigger type: {trigger_type}")

                job_kwargs["trigger"] = trigger

            self.scheduler.modify_job(task_id, **job_kwargs)
            self.logger.info(f"Modified task {task_id}")

        except Exception as e:
            self.logger.error(f"Failed to modify task {task_id}: {str(e)}")
            raise


if __name__ == "__main__":

    async def example_task(name: str):
        print(f"Running task: {name} at {datetime.now()}")

    async def main():
        scheduler = TaskScheduler("redis://localhost:6379/0")
        await scheduler.start()

        # Schedule different types of tasks
        await scheduler.schedule_recurring_task("recurring_task", example_task, interval=30, args=["Recurring Task"])

        await scheduler.schedule_cron_task(
            "cron_task", example_task, "*/5 * * * *", args=["Cron Task"]  # Every 5 minutes
        )

        # List all tasks
        tasks = await scheduler.list_tasks()
        print("Scheduled tasks:", json.dumps(tasks, indent=2))

        # Keep the scheduler running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await scheduler.shutdown()

    asyncio.run(main())
