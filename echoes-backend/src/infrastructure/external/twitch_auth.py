"""
Echoes Backend - Twitch OAuth External Service
"""
from typing import Optional, Tuple
import httpx

from src.config import get_settings

settings = get_settings()


class TwitchAuthService:
    """Service for Twitch OAuth authentication."""
    
    TOKEN_URL = "https://id.twitch.tv/oauth2/token"
    VALIDATE_URL = "https://id.twitch.tv/oauth2/validate"
    USERS_URL = "https://api.twitch.tv/helix/users"
    
    def __init__(self):
        self.client_id = settings.twitch_client_id
        self.client_secret = settings.twitch_client_secret
        self.redirect_uri = settings.twitch_redirect_uri
    
    async def exchange_code_for_token(self, code: str) -> Optional[dict]:
        """
        Exchange authorization code for access token.
        Returns token data or None on failure.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.TOKEN_URL,
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "code": code,
                        "grant_type": "authorization_code",
                        "redirect_uri": self.redirect_uri,
                    },
                )
                
                if response.status_code == 200:
                    return response.json()
                return None
            except Exception:
                return None
    
    async def validate_token(self, access_token: str) -> Optional[dict]:
        """
        Validate a Twitch access token.
        Returns validation data or None if invalid.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.VALIDATE_URL,
                    headers={"Authorization": f"OAuth {access_token}"},
                )
                
                if response.status_code == 200:
                    return response.json()
                return None
            except Exception:
                return None
    
    async def get_user_info(self, access_token: str) -> Optional[dict]:
        """
        Get Twitch user information.
        Returns user data or None on failure.
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.USERS_URL,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Client-Id": self.client_id,
                    },
                )
                
                if response.status_code == 200:
                    data = response.json()
                    users = data.get("data", [])
                    return users[0] if users else None
                return None
            except Exception:
                return None
    
    async def authenticate(self, code: str) -> Tuple[Optional[dict], Optional[dict]]:
        """
        Complete authentication flow.
        Returns (token_data, user_data) or (None, None) on failure.
        """
        # Exchange code for token
        token_data = await self.exchange_code_for_token(code)
        if not token_data:
            return None, None
        
        access_token = token_data.get("access_token")
        if not access_token:
            return None, None
        
        # Get user info
        user_data = await self.get_user_info(access_token)
        if not user_data:
            return None, None
        
        return token_data, user_data


def get_twitch_auth_service() -> TwitchAuthService:
    """Get Twitch auth service instance."""
    return TwitchAuthService()
