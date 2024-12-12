import asyncio
import logging
from pathlib import Path
from typing import Dict, Set, Optional, Callable, Any
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
import aiofiles
import hashlib
import mimetypes
from datetime import datetime

logger = logging.getLogger(__name__)


class FileEventHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[FileSystemEvent], None]):
        self.callback = callback
        super().__init__()

    def on_any_event(self, event: FileSystemEvent):
        if not event.is_directory:
            self.callback(event)


class FileWatcher:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.watch_paths: Set[Path] = set()
        self.observer = Observer()
        self.file_hashes: Dict[str, str] = {}
        self.processing_queue = asyncio.Queue()
        self.is_running = False

    async def start(self):
        """Start the file watcher"""
        if self.is_running:
            return

        self.is_running = True

        # Start the observer
        self.observer.start()

        # Start processing queue
        asyncio.create_task(self._process_queue())

        logger.info("File watcher started")

    async def stop(self):
        """Stop the file watcher"""
        self.is_running = False
        self.observer.stop()
        self.observer.join()
        logger.info("File watcher stopped")

    def add_watch_path(self, path: Path):
        """Add a path to watch"""
        if path not in self.watch_paths:
            handler = FileEventHandler(self._handle_event)
            self.observer.schedule(handler, str(path), recursive=True)
            self.watch_paths.add(path)
            logger.info(f"Added watch path: {path}")

    def remove_watch_path(self, path: Path):
        """Remove a watched path"""
        if path in self.watch_paths:
            self.observer.unschedule(str(path))
            self.watch_paths.remove(path)
            logger.info(f"Removed watch path: {path}")

    def _handle_event(self, event: FileSystemEvent):
        """Handle file system events"""
        asyncio.create_task(self._queue_event(event))

    async def _queue_event(self, event: FileSystemEvent):
        """Queue an event for processing"""
        await self.processing_queue.put(event)

    async def _process_queue(self):
        """Process queued events"""
        while self.is_running:
            try:
                event = await self.processing_queue.get()
                await self._process_event(event)
                self.processing_queue.task_done()
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                await asyncio.sleep(1)

    async def _process_event(self, event: FileSystemEvent):
        """Process a file system event"""
        try:
            file_path = Path(event.src_path)

            # Skip if file doesn't exist or is temporary
            if not file_path.exists() or file_path.name.startswith("."):
                return

            # Get file info
            file_info = await self._get_file_info(file_path)

            if event.event_type in ("created", "modified"):
                await self._handle_file_change(file_path, file_info)
            elif event.event_type == "deleted":
                await self._handle_file_deletion(file_path)

        except Exception as e:
            logger.error(f"Error processing event for {event.src_path}: {e}")

    async def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get file information"""
        try:
            stats = file_path.stat()
            mime_type, _ = mimetypes.guess_type(str(file_path))

            async with aiofiles.open(file_path, "rb") as f:
                content = await f.read()
                file_hash = hashlib.md5(content).hexdigest()

            return {
                "path": str(file_path),
                "name": file_path.name,
                "size": stats.st_size,
                "modified": datetime.fromtimestamp(stats.st_mtime),
                "mime_type": mime_type,
                "hash": file_hash,
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return {}

    async def _handle_file_change(self, file_path: Path, file_info: Dict[str, Any]):
        """Handle file creation or modification"""
        try:
            # Check if file has actually changed
            if str(file_path) in self.file_hashes:
                if self.file_hashes[str(file_path)] == file_info["hash"]:
                    return

            # Update hash
            self.file_hashes[str(file_path)] = file_info["hash"]

            # Process file based on type
            if file_info.get("mime_type"):
                if file_info["mime_type"].startswith("text"):
                    await self._process_text_file(file_path)
                elif file_info["mime_type"].startswith("image"):
                    await self._process_image_file(file_path)
                elif file_info["mime_type"].startswith("video"):
                    await self._process_video_file(file_path)

            logger.info(f"Processed file change: {file_path}")

        except Exception as e:
            logger.error(f"Error handling file change for {file_path}: {e}")

    async def _handle_file_deletion(self, file_path: Path):
        """Handle file deletion"""
        try:
            # Remove from hash cache
            self.file_hashes.pop(str(file_path), None)

            # Additional deletion handling
            logger.info(f"Processed file deletion: {file_path}")

        except Exception as e:
            logger.error(f"Error handling file deletion for {file_path}: {e}")

    async def _process_text_file(self, file_path: Path):
        """Process text file"""
        try:
            async with aiofiles.open(file_path, "r") as f:
                content = await f.read()
                # Process text content
                # Add to knowledge base, analyze, etc.
        except Exception as e:
            logger.error(f"Error processing text file {file_path}: {e}")

    async def _process_image_file(self, file_path: Path):
        """Process image file"""
        try:
            # Process image
            # Extract metadata, analyze content, etc.
            pass
        except Exception as e:
            logger.error(f"Error processing image file {file_path}: {e}")

    async def _process_video_file(self, file_path: Path):
        """Process video file"""
        try:
            # Process video
            # Extract metadata, analyze content, etc.
            pass
        except Exception as e:
            logger.error(f"Error processing video file {file_path}: {e}")

    def get_watched_paths(self) -> Set[Path]:
        """Get list of watched paths"""
        return self.watch_paths.copy()

    async def scan_directory(self, path: Path):
        """Scan directory for existing files"""
        try:
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    file_info = await self._get_file_info(file_path)
                    await self._handle_file_change(file_path, file_info)
        except Exception as e:
            logger.error(f"Error scanning directory {path}: {e}")

    async def get_file_status(self) -> Dict[str, Any]:
        """Get status of watched files"""
        return {
            "watched_paths": list(map(str, self.watch_paths)),
            "tracked_files": len(self.file_hashes),
            "queue_size": self.processing_queue.qsize(),
        }
