"""
Echoes Backend - Login with Twitch Use Case
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID

from jose import jwt

from src.config import get_settings
from src.application.interfaces.repositories import IUserRepository, IPlayerRepository
from src.infrastructure.external.twitch_auth import TwitchAuthService

settings = get_settings()


@dataclass
class LoginTwitchInput:
    """Input for Twitch login."""
    authorization_code: str


@dataclass
class LoginTwitchOutput:
    """Output from Twitch login."""
    access_token: str
    token_type: str
    expires_in: int
    user_id: UUID
    username: str
    is_new_user: bool


class LoginTwitchUseCase:
    """
    Use case for logging in with Twitch OAuth.
    
    Flow:
    1. Exchange authorization code for Twitch tokens
    2. Get user info from Twitch
    3. Create or update user in database
    4. Create player if new user
    5. Generate JWT token
    """
    
    def __init__(
        self,
        user_repository: IUserRepository,
        player_repository: IPlayerRepository,
        twitch_service: TwitchAuthService,
    ):
        self.user_repo = user_repository
        self.player_repo = player_repository
        self.twitch_service = twitch_service
    
    async def execute(self, input_data: LoginTwitchInput) -> Tuple[Optional[LoginTwitchOutput], Optional[str]]:
        """
        Execute the Twitch login flow.
        
        Returns:
            Tuple of (output, error_message)
        """
        # Step 1 & 2: Exchange code and get user info from Twitch
        token_data, user_data = await self.twitch_service.authenticate(input_data.authorization_code)
        
        if not token_data or not user_data:
            return None, "Failed to authenticate with Twitch"
        
        twitch_id = user_data.get("id")
        username = user_data.get("display_name") or user_data.get("login")
        
        if not twitch_id or not username:
            return None, "Invalid user data from Twitch"
        
        # Step 3: Get or create user
        user, is_new = await self.user_repo.get_or_create(
            twitch_id=twitch_id,
            username=username,
        )
        
        if not user:
            return None, "Failed to create or retrieve user"
        
        # Step 4: Create player if new user
        if is_new:
            await self.player_repo.create(user_id=user.id)
        
        # Step 5: Generate JWT
        jwt_token = self._create_jwt_token(user.id)
        
        return LoginTwitchOutput(
            access_token=jwt_token,
            token_type="bearer",
            expires_in=settings.jwt_expire_minutes * 60,
            user_id=user.id,
            username=user.username,
            is_new_user=is_new,
        ), None
    
    def _create_jwt_token(self, user_id: UUID) -> str:
        """Create a JWT token for the user."""
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
        
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        
        return jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
