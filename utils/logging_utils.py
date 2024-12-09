import logging
import sys
from pathlib import Path
from typing import Optional
from functools import wraps
import traceback
import time

class CustomFormatter(logging.Formatter):
    """Custom formatter with colors and structured output"""
    
    COLORS = {
        'DEBUG': '\033[94m',    # Blue
        'INFO': '\033[92m',     # Green
        'WARNING': '\033[93m',  # Yellow
        'ERROR': '\033[91m',    # Red
        'CRITICAL': '\033[95m', # Magenta
        'RESET': '\033[0m'      # Reset
    }

    def format(self, record):
        if hasattr(record, 'color'):
            record.color = self.COLORS.get(record.levelname, '')
            record.reset = self.COLORS['RESET']
        else:
            record.color = ''
            record.reset = ''
        return super().format(record)

def setup_logging(log_dir: Path, level: str = "INFO", service_name: str = "jarvis"):
    """Setup structured logging with file and console output"""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{service_name}.log"
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
    )
    console_formatter = CustomFormatter(
        '%(color)s%(asctime)s | %(levelname)-8s | %(name)s | %(message)s%(reset)s'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger

def log_execution_time(logger: Optional[logging.Logger] = None):
    """Decorator to log function execution time"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = None
            error = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                end_time = time.time()
                execution_time = end_time - start_time
                
                log = logger or logging.getLogger(func.__module__)
                
                if error:
                    log.error(
                        f"Function {func.__name__} failed after {execution_time:.2f}s: {error}\n"
                        f"Traceback:\n{traceback.format_exc()}"
                    )
                else:
                    log.info(f"Function {func.__name__} completed in {execution_time:.2f}s")
        
        return wrapper
    return decorator

def log_async_execution_time(logger: Optional[logging.Logger] = None):
    """Decorator to log async function execution time"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            result = None
            error = None
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                end_time = time.time()
                execution_time = end_time - start_time
                
                log = logger or logging.getLogger(func.__module__)
                
                if error:
                    log.error(
                        f"Async function {func.__name__} failed after {execution_time:.2f}s: {error}\n"
                        f"Traceback:\n{traceback.format_exc()}"
                    )
                else:
                    log.info(f"Async function {func.__name__} completed in {execution_time:.2f}s")
        
        return wrapper
    return decorator
