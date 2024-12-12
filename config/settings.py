from dynaconf import Dynaconf
import os
import sys
import logging
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
import uuid

class JarvisConfigManager:
    def __init__(self, environment=None):
        """
        Comprehensive Configuration Management
        - Multi-environment support
        - Secure secret management
        - Dynamic configuration loading
        """
        # Determine environment
        self.env = environment or os.getenv("JARVIS_ENV", "development")
        
        # Setup logging
        self._setup_logging()
        
        # Load configuration
        self.settings = Dynaconf(
            envvar_prefix="JARVIS",
            settings_files=["config/base.yml", f"config/{self.env}.yml"],
            environments=True,
            load_dotenv=True,
        )
        
        # Initialize secret management
        self._secret_key = self._generate_secret_key()
        self._encryption_manager = self._setup_encryption()

    def _setup_logging(self):
        """Configure logging based on environment"""
        log_config = {
            'development': logging.DEBUG,
            'production': logging.WARNING,
            'testing': logging.INFO
        }
        
        logging.basicConfig(
            level=log_config.get(self.env, logging.INFO),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/jarvis_{self.env}.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    def _generate_secret_key(self) -> bytes:
        """Generate a secure secret key"""
        return Fernet.generate_key()

    def _setup_encryption(self):
        """Initialize encryption manager"""
        return Fernet(self._secret_key)

    def encrypt_secret(self, secret: str) -> str:
        """
        Encrypt a sensitive value
        
        Args:
            secret (str): Secret to encrypt
        
        Returns:
            str: Encrypted secret
        """
        try:
            return self._encryption_manager.encrypt(secret.encode()).decode()
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            return None

    def decrypt_secret(self, encrypted_secret: str) -> Optional[str]:
        """
        Decrypt a sensitive value
        
        Args:
            encrypted_secret (str): Encrypted secret
        
        Returns:
            Optional[str]: Decrypted secret
        """
        try:
            return self._encryption_manager.decrypt(encrypted_secret.encode()).decode()
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            return None

    def get_feature_flags(self) -> Dict[str, bool]:
        """Retrieve feature flags from configuration"""
        return {
            "monitoring_enabled": self.settings.get("features.monitoring", False),
            "ai_services": self.settings.get("features.ai_services", True),
            "blockchain_integration": self.settings.get("features.blockchain", False),
            "webhook_support": self.settings.get("features.webhooks", True),
        }

    def get_service_endpoints(self) -> Dict[str, str]:
        """Retrieve service endpoint configurations"""
        return {
            "core_api": self.settings.get("endpoints.core_api", "https://api.jarvis-assistant.com"),
            "ai_service": self.settings.get("endpoints.ai_service", "https://ai.jarvis-assistant.com"),
            "webhook_base": self.settings.get("endpoints.webhooks", "https://webhooks.jarvis-assistant.com"),
        }

    def get_database_config(self) -> Dict[str, Any]:
        """Retrieve database configuration"""
        return {
            "host": self.settings.get("database.host", "localhost"),
            "port": self.settings.get("database.port", 5432),
            "username": self.settings.get("database.username", ""),
            "database": self.settings.get("database.name", "jarvis_db"),
            "ssl_mode": self.settings.get("database.ssl_mode", "require"),
        }

    def get_logging_config(self) -> Dict[str, str]:
        """Retrieve logging configuration"""
        return {
            "level": self.settings.get("logging.level", "INFO"),
            "format": self.settings.get("logging.format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            "file_path": self.settings.get("logging.file_path", f"logs/jarvis_{self.env}.log"),
        }

    def get_security_config(self) -> Dict[str, Any]:
        """Retrieve security configurations"""
        return {
            "jwt_secret": self.decrypt_secret(self.settings.get("security.jwt_secret")),
            "webhook_secret": self.decrypt_secret(self.settings.get("security.webhook_secret")),
            "allowed_origins": self.settings.get("security.cors_origins", []),
            "rate_limit": self.settings.get("security.rate_limit", 100),
        }

    def generate_unique_identifier(self) -> str:
        """Generate a unique identifier"""
        return str(uuid.uuid4())

    def __getattr__(self, name):
        """Fallback method to access settings directly"""
        return getattr(self.settings, name, None)

# Singleton instance for global access
config_manager = JarvisConfigManager()

# Example usage
if __name__ == "__main__":
    # Demonstrate configuration access
    print("Feature Flags:", config_manager.get_feature_flags())
    print("Service Endpoints:", config_manager.get_service_endpoints())
    
    # Demonstrate secret encryption/decryption
    test_secret = "my_super_secret_password"
    encrypted = config_manager.encrypt_secret(test_secret)
    decrypted = config_manager.decrypt_secret(encrypted)
    print(f"Original: {test_secret}")
    print(f"Encrypted: {encrypted}")
    print(f"Decrypted: {decrypted}")
