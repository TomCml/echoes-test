"""
Echoes Backend - Repository Interfaces
Abstract interfaces for repositories (Ports in Clean Architecture).
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from uuid import UUID


class IUserRepository(ABC):
    """Interface for User repository."""
    
    @abstractmethod
    async def get_by_id(self, user_id: UUID):
        """Get a user by ID."""
        pass
    
    @abstractmethod
    async def get_by_twitch_id(self, twitch_id: str):
        """Get a user by Twitch ID."""
        pass
    
    @abstractmethod
    async def create(self, twitch_id: str, username: str):
        """Create a new user."""
        pass
    
    @abstractmethod
    async def get_or_create(self, twitch_id: str, username: str) -> Tuple:
        """Get or create a user."""
        pass


class IPlayerRepository(ABC):
    """Interface for Player repository."""
    
    @abstractmethod
    async def get_by_id(self, player_id: UUID):
        """Get a player by ID."""
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: UUID):
        """Get a player by user ID."""
        pass
    
    @abstractmethod
    async def create(self, user_id: UUID):
        """Create a new player."""
        pass
    
    @abstractmethod
    async def add_xp(self, player_id: UUID, amount: int) -> Tuple[int, int]:
        """Add XP, returns (level, levels_gained)."""
        pass
    
    @abstractmethod
    async def add_gold(self, player_id: UUID, amount: int) -> int:
        """Add gold, returns new total."""
        pass
    
    @abstractmethod
    async def spend_gold(self, player_id: UUID, amount: int) -> bool:
        """Spend gold, returns success."""
        pass


class IItemRepository(ABC):
    """Interface for Item repository."""
    
    @abstractmethod
    async def get_blueprint_by_id(self, blueprint_id: UUID):
        """Get an item blueprint."""
        pass
    
    @abstractmethod
    async def get_instance_by_id(self, instance_id: UUID):
        """Get an item instance."""
        pass
    
    @abstractmethod
    async def get_player_inventory(self, player_id: UUID) -> List:
        """Get player's inventory."""
        pass
    
    @abstractmethod
    async def create_instance(self, blueprint_id: UUID, owner_id: UUID):
        """Create a new item instance."""
        pass
    
    @abstractmethod
    async def equip_item(self, instance_id: UUID, slot):
        """Equip an item."""
        pass
    
    @abstractmethod
    async def unequip_item(self, instance_id: UUID):
        """Unequip an item."""
        pass
    
    @abstractmethod
    async def update_instance(self, item_instance):
        """Update an item instance."""
        pass


class IMonsterRepository(ABC):
    """Interface for Monster repository."""
    
    @abstractmethod
    async def get_blueprint_by_id(self, blueprint_id: UUID):
        """Get a monster blueprint."""
        pass
    
    @abstractmethod
    async def get_all_blueprints(self) -> List:
        """Get all monster blueprints."""
        pass
    
    @abstractmethod
    async def get_loot_table(self, loot_table_id: UUID):
        """Get a loot table."""
        pass


class ICombatRepository(ABC):
    """Interface for Combat repository."""
    
    @abstractmethod
    async def get_session_by_id(self, session_id: UUID):
        """Get a combat session."""
        pass
    
    @abstractmethod
    async def get_active_session_for_player(self, player_id: UUID):
        """Get active combat for a player."""
        pass
    
    @abstractmethod
    async def create_session(
        self,
        player_id: UUID,
        monster_blueprint_id: UUID,
        monster_level: int,
        player_max_hp: int,
        monster_max_hp: int,
    ):
        """Create a combat session."""
        pass
    
    @abstractmethod
    async def update_session(self, combat_session):
        """Update a combat session."""
        pass
    
    @abstractmethod
    async def get_all_status_definitions(self) -> List:
        """Get all status definitions."""
        pass


class IProgressionRepository(ABC):
    """Interface for Progression repository."""
    
    @abstractmethod
    async def get_all_achievements(self) -> List:
        """Get all achievements."""
        pass
    
    @abstractmethod
    async def get_player_achievements(self, player_id: UUID) -> List:
        """Get player's achievements."""
        pass
    
    @abstractmethod
    async def get_player_active_quests(self, player_id: UUID) -> List:
        """Get player's active quests."""
        pass
    
    @abstractmethod
    async def get_all_dungeons(self) -> List:
        """Get all dungeons."""
        pass
