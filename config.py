from pathlib import Path
from typing import Dict, Any
import yaml
import os
from dataclasses import dataclass


@dataclass
class AgentConfig:
    max_concurrent_tasks: int = 5
    learning_batch_size: int = 10
    model_update_frequency: int = 100
    resource_threshold: float = 0.7


@dataclass
class SystemConfig:
    data_dir: Path
    log_level: str
    dashboard_port: int
    max_agents: int
    agent_config: AgentConfig


class ConfigManager:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self) -> SystemConfig:
        """Load configuration from YAML file with environment variable support"""
        if not os.path.exists(self.config_path):
            return self.create_default_config()

        with open(self.config_path, "r") as f:
            config_data = yaml.safe_load(f)

        # Support environment variable overrides
        for key, value in config_data.items():
            env_value = os.getenv(f"JARVIS_{key.upper()}")
            if env_value:
                config_data[key] = env_value

        return SystemConfig(
            data_dir=Path(config_data.get("data_dir", "data")),
            log_level=config_data.get("log_level", "INFO"),
            dashboard_port=int(config_data.get("dashboard_port", 8080)),
            max_agents=int(config_data.get("max_agents", 10)),
            agent_config=AgentConfig(**config_data.get("agent_config", {})),
        )

    def create_default_config(self) -> SystemConfig:
        """Create and save default configuration"""
        config = SystemConfig(
            data_dir=Path("data"), log_level="INFO", dashboard_port=8080, max_agents=10, agent_config=AgentConfig()
        )

        # Save default config
        self.save_config(config)
        return config

    def save_config(self, config: SystemConfig):
        """Save configuration to YAML file"""
        config_dict = {
            "data_dir": str(config.data_dir),
            "log_level": config.log_level,
            "dashboard_port": config.dashboard_port,
            "max_agents": config.max_agents,
            "agent_config": {
                "max_concurrent_tasks": config.agent_config.max_concurrent_tasks,
                "learning_batch_size": config.agent_config.learning_batch_size,
                "model_update_frequency": config.agent_config.model_update_frequency,
                "resource_threshold": config.agent_config.resource_threshold,
            },
        }

        with open(self.config_path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False)
