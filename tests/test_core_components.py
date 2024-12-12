import pytest
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.settings import JarvisConfigManager


class TestCoreComponents:
    def test_config_manager_initialization(self):
        """Test configuration manager basic initialization"""
        config_manager = JarvisConfigManager()
        assert config_manager is not None, "Configuration manager should be initialized"

    def test_config_environment_loading(self):
        """Test loading different environment configurations"""
        dev_config = JarvisConfigManager(environment="development")
        prod_config = JarvisConfigManager(environment="production")

        assert dev_config is not None, "Development configuration should load"
        assert prod_config is not None, "Production configuration should load"

    def test_config_feature_flags(self):
        """Test configuration feature flag retrieval"""
        config_manager = JarvisConfigManager()

        # Check if key feature flags exist
        feature_flags = config_manager.get_feature_flags()
        assert isinstance(feature_flags, dict), "Feature flags should be a dictionary"

        # Add specific feature flag checks
        expected_flags = ["monitoring_enabled", "portfolio_optimization", "risk_assessment"]

        for flag in expected_flags:
            assert flag in feature_flags, f"{flag} feature flag should exist"

    def test_config_database_settings(self):
        """Test database configuration settings"""
        config_manager = JarvisConfigManager()

        db_config = config_manager.get_database_config()
        assert isinstance(db_config, dict), "Database configuration should be a dictionary"

        required_keys = ["host", "port", "username", "database"]
        for key in required_keys:
            assert key in db_config, f"{key} should be in database configuration"

    def test_logging_configuration(self):
        """Test logging configuration settings"""
        config_manager = JarvisConfigManager()

        logging_config = config_manager.get_logging_config()
        assert isinstance(logging_config, dict), "Logging configuration should be a dictionary"

        required_log_keys = ["level", "format", "file_path"]
        for key in required_log_keys:
            assert key in logging_config, f"{key} should be in logging configuration"


if __name__ == "__main__":
    pytest.main([__file__])
