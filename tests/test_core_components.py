import pytest
from src.core.secret_manager import SecretManager
from src.core.authentication import AdvancedAuthenticationSystem
from src.core.error_handler import JarvisErrorHandler

class TestJarvisCoreComponents:
    def test_secret_manager(self):
        """Test secret management functionality"""
        secret_manager = SecretManager(master_password='test_password')
        
        # Store and retrieve secret
        secret_manager.store_secret('test_key', 'test_secret')
        retrieved_secret = secret_manager.retrieve_secret('test_key')
        
        assert retrieved_secret == 'test_secret'

    def test_authentication_system(self):
        """Test advanced authentication mechanisms"""
        auth_system = AdvancedAuthenticationSystem()
        
        # Test password hashing
        password = 'secure_password_123'
        hashed_password = auth_system.hash_password(password)
        
        assert auth_system.verify_password(hashed_password, password) is True
        assert auth_system.verify_password(hashed_password, 'wrong_password') is False

    def test_jwt_token_generation(self):
        """Test JWT token generation and validation"""
        auth_system = AdvancedAuthenticationSystem()
        
        # Generate token
        user_id = 'user_123'
        roles = ['investor', 'trader']
        token = auth_system.generate_jwt_token(user_id, roles)
        
        # Validate token
        decoded_payload = auth_system.validate_jwt_token(token)
        
        assert decoded_payload is not None
        assert decoded_payload['user_id'] == user_id
        assert decoded_payload['roles'] == roles

    @pytest.mark.parametrize("max_attempts,expected_calls", [
        (3, 3),
        (5, 5)
    ])
    def test_retry_decorator(self, max_attempts, expected_calls):
        """Test retry mechanism with different configurations"""
        calls = 0

        @JarvisErrorHandler.retry(max_attempts=max_attempts)
        def flaky_function():
            nonlocal calls
            calls += 1
            if calls < max_attempts:
                raise ValueError("Simulated failure")
            return "Success"

        result = flaky_function()
        assert result == "Success"
        assert calls == expected_calls
