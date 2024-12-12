import asyncio
import logging
from typing import Dict, Any, Optional

from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.jose import jwt
import httpx

class OpenIDConnectService:
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OpenID Connect Service
        
        Args:
            config (Dict[str, Any]): OpenID Connect configuration
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # OpenID Configuration
        self.discovery_url = config.get('discovery_url')
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.redirect_uri = config.get('redirect_uri')
        
        # Cached OpenID Configuration
        self._openid_config = None
        
        # HTTP Client
        self.client = AsyncOAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret
        )

    async def discover_configuration(self) -> Dict[str, Any]:
        """
        Discover OpenID Connect Provider Configuration
        
        Returns:
            Dict containing OpenID configuration
        """
        if self._openid_config:
            return self._openid_config
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.discovery_url)
                response.raise_for_status()
                self._openid_config = response.json()
                return self._openid_config
        except Exception as e:
            self.logger.error(f"OpenID configuration discovery failed: {e}")
            return None

    async def generate_authorization_url(self, scope: str = 'openid profile email') -> str:
        """
        Generate Authorization URL for OpenID Connect
        
        Args:
            scope (str, optional): OAuth scopes. Defaults to 'openid profile email'
        
        Returns:
            str: Authorization URL
        """
        try:
            config = await self.discover_configuration()
            authorization_endpoint = config.get('authorization_endpoint')
            
            authorization_url = self.client.create_authorization_url(
                authorization_endpoint,
                scope=scope,
                redirect_uri=self.redirect_uri,
                response_type='code'
            )
            return authorization_url
        except Exception as e:
            self.logger.error(f"Authorization URL generation failed: {e}")
            return None

    async def exchange_authorization_code(self, authorization_code: str) -> Dict[str, Any]:
        """
        Exchange Authorization Code for Tokens
        
        Args:
            authorization_code (str): Authorization code from provider
        
        Returns:
            Dict containing access token, ID token, and other details
        """
        try:
            config = await self.discover_configuration()
            token_endpoint = config.get('token_endpoint')
            
            token_response = await self.client.fetch_token(
                token_endpoint,
                grant_type='authorization_code',
                code=authorization_code,
                redirect_uri=self.redirect_uri
            )
            return token_response
        except Exception as e:
            self.logger.error(f"Token exchange failed: {e}")
            return None

    async def validate_id_token(self, id_token: str) -> Dict[str, Any]:
        """
        Validate ID Token
        
        Args:
            id_token (str): JWT ID token
        
        Returns:
            Dict containing decoded token payload
        """
        try:
            config = await self.discover_configuration()
            jwks_uri = config.get('jwks_uri')
            
            # Fetch JWKS (JSON Web Key Set)
            async with httpx.AsyncClient() as client:
                jwks_response = await client.get(jwks_uri)
                jwks_response.raise_for_status()
                jwks = jwks_response.json()
            
            # Decode and validate token
            claims = jwt.decode(id_token, jwks)
            claims.validate()
            
            return claims
        except Exception as e:
            self.logger.error(f"ID token validation failed: {e}")
            return None

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh Access Token
        
        Args:
            refresh_token (str): Refresh token
        
        Returns:
            Dict containing new access token
        """
        try:
            config = await self.discover_configuration()
            token_endpoint = config.get('token_endpoint')
            
            token_response = await self.client.fetch_token(
                token_endpoint,
                grant_type='refresh_token',
                refresh_token=refresh_token
            )
            return token_response
        except Exception as e:
            self.logger.error(f"Token refresh failed: {e}")
            return None

# Example usage and configuration
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    config = {
        'discovery_url': 'https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration',
        'client_id': os.getenv('AZURE_AD_CLIENT_ID'),
        'client_secret': os.getenv('AZURE_AD_CLIENT_SECRET'),
        'redirect_uri': 'http://localhost:8000/callback'
    }

    async def main():
        openid_service = OpenIDConnectService(config)
        
        # Generate Authorization URL
        auth_url = await openid_service.generate_authorization_url()
        print("Authorization URL:", auth_url)
        
        # Note: In a real scenario, you'd get the authorization code from user interaction
        # This is just a demonstration
        
        # Example token validation (mock token)
        mock_id_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        validated_token = await openid_service.validate_id_token(mock_id_token)
        print("Validated Token:", validated_token)

    asyncio.run(main())
