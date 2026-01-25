"""
Echoes Backend - Get Current User Use Case
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple
from uuid import UUID

from src.application.interfaces.repositories import IUserRepository, IPlayerRepository


@dataclass
class CurrentUserOutput:
    """Output for current user."""
    user_id: UUID
    twitch_id: str
    username: str
    is_profile_public: bool
    created_at: datetime
    player_id: Optional[UUID] = None
    player_level: Optional[int] = None


class GetCurrentUserUseCase:
    """
    Use case for getting the currently authenticated user.
    """
    
    def __init__(
        self,
        user_repository: IUserRepository,
        player_repository: IPlayerRepository,
    ):
        self.user_repo = user_repository
        self.player_repo = player_repository
    
    async def execute(self, user_id: UUID) -> Tuple[Optional[CurrentUserOutput], Optional[str]]:
        """
        Get the current user and their player data.
        
        Args:
            user_id: The authenticated user's ID
            
        Returns:
            Tuple of (output, error_message)
        """
        # Get user
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return None, "User not found"
        
        # Get player (optional, user may not have a player yet)
        player = await self.player_repo.get_by_user_id(user_id)
        
        return CurrentUserOutput(
            user_id=user.id,
            twitch_id=user.twitch_id,
            username=user.username,
            is_profile_public=user.is_profile_public,
            created_at=user.created_at,
            player_id=player.id if player else None,
            player_level=player.level if player else None,
        ), None
