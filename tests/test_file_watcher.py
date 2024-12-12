import pytest
import asyncio
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch
from jarvis_assistant.file_management.file_watcher import FileWatcher, FileEventHandler
from watchdog.events import FileCreatedEvent, FileModifiedEvent, FileDeletedEvent


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing"""
    return tmp_path


@pytest.fixture
async def file_watcher(temp_dir):
    """Create a file watcher instance for testing"""
    config = {"watch_paths": [str(temp_dir)], "ignore_patterns": ["*.tmp", ".*"], "processing_delay": 0.1}
    watcher = FileWatcher(config)
    await watcher.start()
    yield watcher
    await watcher.stop()


@pytest.mark.asyncio
async def test_watcher_initialization(file_watcher, temp_dir):
    """Test file watcher initialization"""
    assert file_watcher.is_running
    assert temp_dir in file_watcher.watch_paths


@pytest.mark.asyncio
async def test_file_creation(file_watcher, temp_dir):
    """Test file creation detection"""
    # Create a test file
    test_file = temp_dir / "test.txt"
    test_file.write_text("Test content")

    # Wait for processing
    await asyncio.sleep(0.2)

    # Check if file was detected
    assert str(test_file) in file_watcher.file_hashes


@pytest.mark.asyncio
async def test_file_modification(file_watcher, temp_dir):
    """Test file modification detection"""
    # Create and modify a test file
    test_file = temp_dir / "test.txt"
    test_file.write_text("Initial content")
    await asyncio.sleep(0.2)

    initial_hash = file_watcher.file_hashes[str(test_file)]

    test_file.write_text("Modified content")
    await asyncio.sleep(0.2)

    modified_hash = file_watcher.file_hashes[str(test_file)]
    assert initial_hash != modified_hash


@pytest.mark.asyncio
async def test_file_deletion(file_watcher, temp_dir):
    """Test file deletion detection"""
    # Create and delete a test file
    test_file = temp_dir / "test.txt"
    test_file.write_text("Test content")
    await asyncio.sleep(0.2)

    test_file.unlink()
    await asyncio.sleep(0.2)

    assert str(test_file) not in file_watcher.file_hashes


@pytest.mark.asyncio
async def test_directory_scanning(file_watcher, temp_dir):
    """Test directory scanning"""
    # Create test files
    (temp_dir / "file1.txt").write_text("Content 1")
    (temp_dir / "file2.txt").write_text("Content 2")
    (temp_dir / "subdir").mkdir()
    (temp_dir / "subdir" / "file3.txt").write_text("Content 3")

    # Scan directory
    await file_watcher.scan_directory(temp_dir)
    await asyncio.sleep(0.2)

    assert len(file_watcher.file_hashes) == 3


@pytest.mark.asyncio
async def test_file_type_handling(file_watcher, temp_dir):
    """Test handling of different file types"""
    # Create different types of files
    text_file = temp_dir / "test.txt"
    text_file.write_text("Text content")

    image_file = temp_dir / "test.jpg"
    image_file.write_bytes(b"Fake image content")

    video_file = temp_dir / "test.mp4"
    video_file.write_bytes(b"Fake video content")

    await asyncio.sleep(0.2)

    # Check if all files were processed
    assert str(text_file) in file_watcher.file_hashes
    assert str(image_file) in file_watcher.file_hashes
    assert str(video_file) in file_watcher.file_hashes


@pytest.mark.asyncio
async def test_ignore_patterns(file_watcher, temp_dir):
    """Test ignore patterns"""
    # Create files that should be ignored
    temp_file = temp_dir / "test.tmp"
    temp_file.write_text("Temporary content")

    hidden_file = temp_dir / ".hidden"
    hidden_file.write_text("Hidden content")

    await asyncio.sleep(0.2)

    assert str(temp_file) not in file_watcher.file_hashes
    assert str(hidden_file) not in file_watcher.file_hashes


@pytest.mark.asyncio
async def test_watch_path_management(file_watcher, temp_dir):
    """Test adding and removing watch paths"""
    new_dir = temp_dir / "new_dir"
    new_dir.mkdir()

    # Add new watch path
    file_watcher.add_watch_path(new_dir)
    assert new_dir in file_watcher.watch_paths

    # Remove watch path
    file_watcher.remove_watch_path(new_dir)
    assert new_dir not in file_watcher.watch_paths


@pytest.mark.asyncio
async def test_queue_processing(file_watcher, temp_dir):
    """Test event queue processing"""
    # Create multiple files rapidly
    for i in range(5):
        test_file = temp_dir / f"test{i}.txt"
        test_file.write_text(f"Content {i}")
        await asyncio.sleep(0.01)

    # Wait for processing
    await asyncio.sleep(0.5)

    # Check if all files were processed
    assert len(file_watcher.file_hashes) == 5


@pytest.mark.asyncio
async def test_error_handling(file_watcher, temp_dir):
    """Test error handling during file processing"""
    # Mock file processing to raise an error
    with patch.object(file_watcher, "_process_text_file", side_effect=Exception("Test error")):
        test_file = temp_dir / "error_test.txt"
        test_file.write_text("Test content")

        # Should not raise exception
        await asyncio.sleep(0.2)

        # File should still be tracked
        assert str(test_file) in file_watcher.file_hashes


@pytest.mark.asyncio
async def test_file_status(file_watcher, temp_dir):
    """Test file status reporting"""
    # Create some test files
    for i in range(3):
        test_file = temp_dir / f"status_test{i}.txt"
        test_file.write_text(f"Content {i}")

    await asyncio.sleep(0.2)

    status = await file_watcher.get_file_status()
    assert status["tracked_files"] == 3
    assert len(status["watched_paths"]) == 1
