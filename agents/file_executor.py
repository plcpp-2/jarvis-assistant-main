import asyncio
import aiofiles
import os
import shutil
from typing import Dict, List, Optional, Union, AsyncGenerator
import logging
from datetime import datetime
import hashlib
import magic
import aionotify
from pathlib import Path
import json
from prometheus_client import Counter, Gauge

class FileExecutor:
    def __init__(self):
        self.logger = logging.getLogger("FileExecutor")
        self.watchers: Dict[str, aionotify.Watcher] = {}
        
        # Metrics
        self.file_ops_counter = Counter(
            'file_operations_total',
            'Total number of file operations',
            ['operation', 'status']
        )
        self.watched_files_gauge = Gauge(
            'watched_files_total',
            'Number of files being watched'
        )

    async def read_file(
        self,
        path: Union[str, Path],
        chunk_size: Optional[int] = None,
        encoding: str = 'utf-8'
    ) -> Union[str, AsyncGenerator[bytes, None]]:
        """Read file contents"""
        try:
            path = Path(path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")

            if chunk_size:
                async def read_chunks():
                    async with aiofiles.open(path, 'rb') as f:
                        while chunk := await f.read(chunk_size):
                            yield chunk
                return read_chunks()
            else:
                async with aiofiles.open(path, 'r', encoding=encoding) as f:
                    return await f.read()

        except Exception as e:
            self.logger.error(f"File read failed: {str(e)}")
            self.file_ops_counter.labels(
                operation='read',
                status='error'
            ).inc()
            raise
        else:
            self.file_ops_counter.labels(
                operation='read',
                status='success'
            ).inc()

    async def write_file(
        self,
        path: Union[str, Path],
        content: Union[str, bytes],
        mode: str = 'w',
        encoding: Optional[str] = 'utf-8'
    ) -> Dict[str, Union[str, int]]:
        """Write content to file"""
        try:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(
                path,
                mode,
                encoding=encoding if 'b' not in mode else None
            ) as f:
                await f.write(content)

            stats = path.stat()
            return {
                'path': str(path),
                'size': stats.st_size,
                'modified': datetime.fromtimestamp(stats.st_mtime).isoformat()
            }

        except Exception as e:
            self.logger.error(f"File write failed: {str(e)}")
            self.file_ops_counter.labels(
                operation='write',
                status='error'
            ).inc()
            raise
        else:
            self.file_ops_counter.labels(
                operation='write',
                status='success'
            ).inc()

    async def copy_file(
        self,
        source: Union[str, Path],
        destination: Union[str, Path],
        overwrite: bool = False
    ) -> Dict[str, Union[str, int]]:
        """Copy file to destination"""
        try:
            source = Path(source)
            destination = Path(destination)

            if not source.exists():
                raise FileNotFoundError(f"Source file not found: {source}")

            if destination.exists() and not overwrite:
                raise FileExistsError(
                    f"Destination file already exists: {destination}"
                )

            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

            stats = destination.stat()
            return {
                'source': str(source),
                'destination': str(destination),
                'size': stats.st_size,
                'modified': datetime.fromtimestamp(stats.st_mtime).isoformat()
            }

        except Exception as e:
            self.logger.error(f"File copy failed: {str(e)}")
            self.file_ops_counter.labels(
                operation='copy',
                status='error'
            ).inc()
            raise
        else:
            self.file_ops_counter.labels(
                operation='copy',
                status='success'
            ).inc()

    async def move_file(
        self,
        source: Union[str, Path],
        destination: Union[str, Path],
        overwrite: bool = False
    ) -> Dict[str, Union[str, int]]:
        """Move file to destination"""
        try:
            source = Path(source)
            destination = Path(destination)

            if not source.exists():
                raise FileNotFoundError(f"Source file not found: {source}")

            if destination.exists() and not overwrite:
                raise FileExistsError(
                    f"Destination file already exists: {destination}"
                )

            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(source, destination)

            stats = destination.stat()
            return {
                'source': str(source),
                'destination': str(destination),
                'size': stats.st_size,
                'modified': datetime.fromtimestamp(stats.st_mtime).isoformat()
            }

        except Exception as e:
            self.logger.error(f"File move failed: {str(e)}")
            self.file_ops_counter.labels(
                operation='move',
                status='error'
            ).inc()
            raise
        else:
            self.file_ops_counter.labels(
                operation='move',
                status='success'
            ).inc()

    async def delete_file(
        self,
        path: Union[str, Path],
        secure: bool = False
    ) -> Dict[str, Union[str, int]]:
        """Delete file with optional secure deletion"""
        try:
            path = Path(path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")

            stats = path.stat()
            info = {
                'path': str(path),
                'size': stats.st_size,
                'deleted_at': datetime.now().isoformat()
            }

            if secure:
                # Secure deletion by overwriting with random data
                async with aiofiles.open(path, 'wb') as f:
                    size = stats.st_size
                    await f.write(os.urandom(size))
                    await f.flush()
                    os.fsync(f.fileno())

            path.unlink()
            return info

        except Exception as e:
            self.logger.error(f"File deletion failed: {str(e)}")
            self.file_ops_counter.labels(
                operation='delete',
                status='error'
            ).inc()
            raise
        else:
            self.file_ops_counter.labels(
                operation='delete',
                status='success'
            ).inc()

    async def get_file_info(
        self,
        path: Union[str, Path]
    ) -> Dict[str, Union[str, int]]:
        """Get detailed file information"""
        try:
            path = Path(path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")

            stats = path.stat()
            
            # Calculate file hash
            async with aiofiles.open(path, 'rb') as f:
                content = await f.read()
                md5_hash = hashlib.md5(content).hexdigest()
                sha256_hash = hashlib.sha256(content).hexdigest()

            # Detect mime type
            mime = magic.Magic(mime=True)
            mime_type = mime.from_file(str(path))

            return {
                'path': str(path),
                'size': stats.st_size,
                'created': datetime.fromtimestamp(stats.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                'accessed': datetime.fromtimestamp(stats.st_atime).isoformat(),
                'mime_type': mime_type,
                'md5': md5_hash,
                'sha256': sha256_hash,
                'permissions': oct(stats.st_mode)[-3:]
            }

        except Exception as e:
            self.logger.error(f"Failed to get file info: {str(e)}")
            raise

    async def watch_file(
        self,
        path: Union[str, Path],
        callback: callable,
        events: Optional[List[str]] = None
    ):
        """Watch file for changes"""
        try:
            path = Path(path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")

            watcher = aionotify.Watcher()
            
            # Configure events to watch
            flags = 0
            if events:
                for event in events:
                    if hasattr(aionotify, event.upper()):
                        flags |= getattr(aionotify, event.upper())
            else:
                # Watch all events by default
                flags = (
                    aionotify.ACCESSED |
                    aionotify.MODIFIED |
                    aionotify.CREATED |
                    aionotify.DELETED
                )

            watcher.watch(
                path=str(path),
                flags=flags
            )

            self.watchers[str(path)] = watcher
            self.watched_files_gauge.inc()

            await watcher.setup()
            
            while True:
                event = await watcher.get_event()
                await callback(event)

        except Exception as e:
            self.logger.error(f"File watching failed: {str(e)}")
            raise

    async def stop_watching(self, path: Union[str, Path]):
        """Stop watching a file"""
        try:
            path_str = str(Path(path))
            if path_str in self.watchers:
                watcher = self.watchers[path_str]
                watcher.close()
                del self.watchers[path_str]
                self.watched_files_gauge.dec()

        except Exception as e:
            self.logger.error(f"Failed to stop watching file: {str(e)}")
            raise

    async def find_files(
        self,
        directory: Union[str, Path],
        pattern: str = '*',
        recursive: bool = True
    ) -> List[Dict[str, Union[str, int]]]:
        """Find files matching pattern"""
        try:
            directory = Path(directory)
            if not directory.exists():
                raise FileNotFoundError(f"Directory not found: {directory}")

            files = []
            for path in directory.rglob(pattern) if recursive else directory.glob(pattern):
                if path.is_file():
                    stats = path.stat()
                    files.append({
                        'path': str(path),
                        'size': stats.st_size,
                        'modified': datetime.fromtimestamp(stats.st_mtime).isoformat()
                    })

            return files

        except Exception as e:
            self.logger.error(f"File search failed: {str(e)}")
            raise

if __name__ == "__main__":
    async def main():
        executor = FileExecutor()

        # Write a test file
        content = "Hello, World!"
        write_result = await executor.write_file(
            "test.txt",
            content
        )
        print("Write result:", json.dumps(write_result, indent=2))

        # Get file info
        info = await executor.get_file_info("test.txt")
        print("File info:", json.dumps(info, indent=2))

        # Watch for changes
        async def on_change(event):
            print(f"File changed: {event}")

        # Start watching in the background
        watch_task = asyncio.create_task(
            executor.watch_file("test.txt", on_change)
        )

        # Make some changes
        await asyncio.sleep(1)
        await executor.write_file("test.txt", "Updated content!")
        
        # Clean up
        await executor.stop_watching("test.txt")
        await executor.delete_file("test.txt")

    asyncio.run(main())
