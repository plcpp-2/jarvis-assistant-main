from dynaconf import Dynaconf
import os

class JarvisConfigManager:
    def __init__(self, environment=None):
        """
        Comprehensive Configuration Management
        - Multi-environment support
        - Secure secret management
        - Dynamic configuration loading
        """
        # Determine environment
        env = environment or os.getenv('JARVIS_ENV', 'development')
        
        # Load configuration
        self.settings = Dynaconf(
            envvar_prefix="JARVIS",
            settings_files=[
                'config/base.yml',
                f'config/{env}.yml',
                '.secrets.yml'  # Gitignored secrets file
            ],
            environments=True,
            load_dotenv=True
        )

    def get_database_config(self):
        """Retrieve database configuration"""
        return {
            'host': self.settings.DATABASE.HOST,
            'port': self.settings.DATABASE.PORT,
            'name': self.settings.DATABASE.NAME,
            'user': self.settings.DATABASE.USER,
            'password': self.settings.DATABASE.PASSWORD
        }

    def get_api_credentials(self, service_name):
        """Retrieve API credentials securely"""
        return {
            'api_key': self.settings.get(f'{service_name.upper()}_API_KEY'),
            'api_secret': self.settings.get(f'{service_name.upper()}_API_SECRET')
        }

    def get_feature_flags(self):
        """Retrieve feature flags"""
        return {
            'ml_optimization_enabled': self.settings.FEATURES.ML_OPTIMIZATION,
            'advanced_trading_enabled': self.settings.FEATURES.ADVANCED_TRADING
        }
