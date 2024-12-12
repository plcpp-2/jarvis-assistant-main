from typing import List, Callable, Any, Optional
import asyncio
from datetime import datetime
import logging
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


@dataclass
class BatchConfig:
    max_size: int = 100
    max_wait_time: float = 1.0  # seconds
    workers: int = 4


class BatchProcessor:
    def __init__(self, config: BatchConfig = None):
        self.config = config or BatchConfig()
        self.batch_queue = asyncio.Queue()
        self.processing = False
        self.executor = ThreadPoolExecutor(max_workers=self.config.workers)
        self.current_batch: List[Any] = []
        self.last_process_time = datetime.now()

    async def start(self):
        """Start the batch processor"""
        self.processing = True
        asyncio.create_task(self._process_loop())
        logger.info("Batch processor started")

    async def stop(self):
        """Stop the batch processor"""
        self.processing = False
        if self.current_batch:
            await self._process_current_batch()
        self.executor.shutdown(wait=True)
        logger.info("Batch processor stopped")

    async def add_item(self, item: Any):
        """Add an item to the batch queue"""
        await self.batch_queue.put(item)

        if len(self.current_batch) >= self.config.max_size:
            await self._process_current_batch()

    async def _process_loop(self):
        """Main processing loop"""
        while self.processing:
            try:
                # Get item with timeout
                try:
                    item = await asyncio.wait_for(self.batch_queue.get(), timeout=self.config.max_wait_time)
                    self.current_batch.append(item)
                except asyncio.TimeoutError:
                    pass

                # Process batch if conditions are met
                if self._should_process_batch():
                    await self._process_current_batch()

            except Exception as e:
                logger.error(f"Error in batch processing loop: {e}")
                await asyncio.sleep(1)

    def _should_process_batch(self) -> bool:
        """Check if batch should be processed"""
        if not self.current_batch:
            return False

        current_time = datetime.now()
        time_since_last = (current_time - self.last_process_time).total_seconds()

        return len(self.current_batch) >= self.config.max_size or time_since_last >= self.config.max_wait_time

    async def _process_current_batch(self):
        """Process the current batch"""
        if not self.current_batch:
            return

        batch = self.current_batch
        self.current_batch = []
        self.last_process_time = datetime.now()

        try:
            # Process batch items in parallel using thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self.executor, self._process_batch_items, batch)
        except Exception as e:
            logger.error(f"Error processing batch: {e}")

    def _process_batch_items(self, items: List[Any]):
        """Process batch items (override this method)"""
        raise NotImplementedError


class TaskBatchProcessor(BatchProcessor):
    def __init__(self, process_func: Callable, config: Optional[BatchConfig] = None):
        super().__init__(config)
        self.process_func = process_func

    def _process_batch_items(self, items: List[Any]):
        """Process batch items using the provided function"""
        return self.process_func(items)
