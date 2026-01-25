"""
Echoes Backend - Create Player Use Case
"""
from dataclasses import dataclass
from typing import Optional, Tuple
from uuid import UUID

from src.application.interfaces.repositories import IPlayerRepository, IUserRepository


@dataclass
class CreatePlayerInput:
    """Input for creating a player."""
    user_id: UUID


@dataclass
class CreatePlayerOutput:
    """Output from creating a player."""
    player_id: UUID
    level: int
    gold: int


class CreatePlayerUseCase:
    """
    Use case for creating a new player for a user.
    """
    
    def __init__(
        self,
        player_repository: IPlayerRepository,
        user_repository: IUserRepository,
    ):
        self.player_repo = player_repository
        self.user_repo = user_repository
    
    async def execute(self, input_data: CreatePlayerInput) -> Tuple[Optional[CreatePlayerOutput], Optional[str]]:
        """
        Create a new player for a user.
        
        Returns:
            Tuple of (output, error_message)
        """
        # Check user exists
        user = await self.user_repo.get_by_id(input_data.user_id)
        if not user:
            return None, "User not found"
        
        # Check player doesn't already exist
        existing = await self.player_repo.get_by_user_id(input_data.user_id)
        if existing:
            return None, "Player already exists for this user"
        
        # Create player
        player = await self.player_repo.create(user_id=input_data.user_id)
        
        if not player:
            return None, "Failed to create player"
        
        return CreatePlayerOutput(
            player_id=player.id,
            level=player.level,
            gold=player.gold,
        ), None
