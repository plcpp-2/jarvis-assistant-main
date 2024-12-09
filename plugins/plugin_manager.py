from typing import Dict, List, Any, Optional, Type
import importlib
import inspect
import logging
from pathlib import Path
import yaml
from abc import ABC, abstractmethod
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class PluginBase(ABC):
    """Base class for all plugins"""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the plugin"""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the plugin's main functionality"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> bool:
        """Cleanup plugin resources"""
        pass

class PluginMetadata:
    """Plugin metadata container"""
    def __init__(self, data: Dict[str, Any]):
        self.name = data['name']
        self.version = data['version']
        self.description = data['description']
        self.author = data['author']
        self.dependencies = data.get('dependencies', [])
        self.config_schema = data.get('config_schema', {})
        self.enabled = data.get('enabled', True)

class PluginManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.plugins: Dict[str, PluginBase] = {}
        self.metadata: Dict[str, PluginMetadata] = {}
        self.executor = ThreadPoolExecutor(max_workers=config.get('max_workers', 4))

    async def load_plugins(self, plugins_dir: Path):
        """Load all plugins from directory"""
        try:
            for plugin_dir in plugins_dir.iterdir():
                if plugin_dir.is_dir() and (plugin_dir / 'metadata.yaml').exists():
                    await self.load_plugin(plugin_dir)
            return True
        except Exception as e:
            logger.error(f"Error loading plugins: {e}")
            return False

    async def load_plugin(self, plugin_dir: Path):
        """Load a single plugin"""
        try:
            # Load metadata
            metadata = self._load_metadata(plugin_dir / 'metadata.yaml')
            if not metadata.enabled:
                return False

            # Check dependencies
            if not await self._check_dependencies(metadata.dependencies):
                logger.error(f"Plugin dependencies not met: {metadata.name}")
                return False

            # Import plugin module
            module = importlib.import_module(f"plugins.{plugin_dir.name}.plugin")
            plugin_class = self._find_plugin_class(module)
            
            if not plugin_class:
                logger.error(f"No plugin class found in {plugin_dir.name}")
                return False

            # Initialize plugin
            plugin = plugin_class()
            if await plugin.initialize():
                self.plugins[metadata.name] = plugin
                self.metadata[metadata.name] = metadata
                return True

            return False
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_dir.name}: {e}")
            return False

    def _load_metadata(self, metadata_path: Path) -> PluginMetadata:
        """Load plugin metadata from YAML"""
        with open(metadata_path) as f:
            return PluginMetadata(yaml.safe_load(f))

    async def _check_dependencies(self, dependencies: List[str]) -> bool:
        """Check if all plugin dependencies are met"""
        try:
            for dep in dependencies:
                try:
                    importlib.import_module(dep)
                except ImportError:
                    logger.error(f"Missing dependency: {dep}")
                    return False
            return True
        except Exception as e:
            logger.error(f"Error checking dependencies: {e}")
            return False

    def _find_plugin_class(self, module) -> Optional[Type[PluginBase]]:
        """Find the plugin class in module"""
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, PluginBase) and 
                obj != PluginBase):
                return obj
        return None

    async def execute_plugin(
        self,
        plugin_name: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Execute a plugin"""
        try:
            if plugin_name not in self.plugins:
                logger.error(f"Plugin not found: {plugin_name}")
                return None

            plugin = self.plugins[plugin_name]
            return await plugin.execute(**kwargs)
        except Exception as e:
            logger.error(f"Error executing plugin {plugin_name}: {e}")
            return None

    async def execute_plugins_parallel(
        self,
        plugin_names: List[str],
        **kwargs
    ) -> Dict[str, Any]:
        """Execute multiple plugins in parallel"""
        tasks = []
        for name in plugin_names:
            if name in self.plugins:
                tasks.append(self.execute_plugin(name, **kwargs))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {
            name: result for name, result in zip(plugin_names, results)
            if not isinstance(result, Exception)
        }

    async def cleanup_plugins(self):
        """Cleanup all plugins"""
        try:
            for name, plugin in self.plugins.items():
                try:
                    await plugin.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up plugin {name}: {e}")
            self.plugins.clear()
            self.metadata.clear()
            return True
        except Exception as e:
            logger.error(f"Error cleaning up plugins: {e}")
            return False

    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get plugin information"""
        if plugin_name not in self.metadata:
            return None
            
        metadata = self.metadata[plugin_name]
        return {
            'name': metadata.name,
            'version': metadata.version,
            'description': metadata.description,
            'author': metadata.author,
            'dependencies': metadata.dependencies,
            'config_schema': metadata.config_schema,
            'enabled': metadata.enabled
        }

    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all loaded plugins"""
        return [
            self.get_plugin_info(name)
            for name in self.plugins.keys()
        ]
