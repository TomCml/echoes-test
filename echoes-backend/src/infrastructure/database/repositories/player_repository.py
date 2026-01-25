"""
Echoes Backend - Player Repository
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infrastructure.database.models.user_model import UserModel
from src.infrastructure.database.models.player_model import (
    PlayerModel,
    PlayerEquipmentLoadoutModel,
)


class PlayerRepository:
    """Repository for Player data access."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, player_id: UUID) -> Optional[PlayerModel]:
        """Get a player by ID."""
        result = await self.session.execute(
            select(PlayerModel)
            .where(PlayerModel.id == player_id)
            .options(
                selectinload(PlayerModel.equipment_loadout),
                selectinload(PlayerModel.user),
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_id(self, user_id: UUID) -> Optional[PlayerModel]:
        """Get a player by user ID."""
        result = await self.session.execute(
            select(PlayerModel)
            .where(PlayerModel.user_id == user_id)
            .options(
                selectinload(PlayerModel.equipment_loadout),
                selectinload(PlayerModel.user),
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_twitch_id(self, twitch_id: str) -> Optional[PlayerModel]:
        """Get a player by Twitch ID (via User)."""
        result = await self.session.execute(
            select(PlayerModel)
            .join(UserModel)
            .where(UserModel.twitch_id == twitch_id)
            .options(selectinload(PlayerModel.equipment_loadout))
        )
        return result.scalar_one_or_none()
    
    async def create(self, user_id: UUID) -> PlayerModel:
        """Create a new player for a user."""
        player = PlayerModel(user_id=user_id)
        self.session.add(player)
        await self.session.flush()
        
        # Create equipment loadout
        loadout = PlayerEquipmentLoadoutModel(player_id=player.id)
        self.session.add(loadout)
        await self.session.flush()
        
        return player
    
    async def update(self, player: PlayerModel) -> PlayerModel:
        """Update a player."""
        await self.session.flush()
        return player
    
    async def add_xp(self, player_id: UUID, amount: int) -> tuple[int, int]:
        """
        Add XP to a player.
        Returns (new_level, levels_gained).
        """
        player = await self.get_by_id(player_id)
        if not player:
            raise ValueError(f"Player {player_id} not found")
        
        player.current_xp += amount
        levels_gained = 0
        
        while player.current_xp >= player.xp_to_next_level:
            player.current_xp -= player.xp_to_next_level
            player.level += 1
            levels_gained += 1
            player.stat_points_available += 5
            player.xp_to_next_level = int(100 * (player.level ** 1.5))
        
        await self.session.flush()
        return player.level, levels_gained
    
    async def add_gold(self, player_id: UUID, amount: int) -> int:
        """Add gold to a player. Returns new total."""
        player = await self.get_by_id(player_id)
        if not player:
            raise ValueError(f"Player {player_id} not found")
        
        player.gold += amount
        await self.session.flush()
        return player.gold
    
    async def spend_gold(self, player_id: UUID, amount: int) -> bool:
        """Spend gold. Returns True if successful."""
        player = await self.get_by_id(player_id)
        if not player:
            raise ValueError(f"Player {player_id} not found")
        
        if player.gold < amount:
            return False
        
        player.gold -= amount
        await self.session.flush()
        return True


class UserRepository:
    """Repository for User data access."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, user_id: UUID) -> Optional[UserModel]:
        """Get a user by ID."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_twitch_id(self, twitch_id: str) -> Optional[UserModel]:
        """Get a user by Twitch ID."""
        result = await self.session.execute(
            select(UserModel).where(UserModel.twitch_id == twitch_id)
        )
        return result.scalar_one_or_none()
    
    async def create(self, twitch_id: str, username: str) -> UserModel:
        """Create a new user."""
        user = UserModel(
            twitch_id=twitch_id,
            username=username,
        )
        self.session.add(user)
        await self.session.flush()
        return user
    
    async def update(self, user: UserModel) -> UserModel:
        """Update a user."""
        await self.session.flush()
        return user
    
    async def get_or_create(self, twitch_id: str, username: str) -> tuple[UserModel, bool]:
        """
        Get existing user or create new one.
        Returns (user, created) where created is True if new.
        """
        user = await self.get_by_twitch_id(twitch_id)
        if user:
            # Update username if changed
            if user.username != username:
                user.username = username
                await self.session.flush()
            return user, False
        
        user = await self.create(twitch_id, username)
        return user, True
