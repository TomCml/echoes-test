"""
Echoes Backend - User and Player Domain Entities
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class User:
    """
    User entity - represents a Twitch user account.
    Contains authentication data, not game data.
    """
    id: UUID
    twitch_id: str
    username: str
    is_profile_public: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def create(cls, twitch_id: str, username: str) -> "User":
        """Create a new User."""
        return cls(
            id=uuid4(),
            twitch_id=twitch_id,
            username=username,
        )


@dataclass
class Player:
    """
    Player entity - represents the game character.
    Contains progression and gameplay data.
    """
    id: UUID
    user_id: UUID
    level: int = 1
    current_xp: int = 0
    xp_to_next_level: int = 100
    gold: int = 0
    stat_points_available: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def create(cls, user_id: UUID) -> "Player":
        """Create a new Player for a User."""
        return cls(
            id=uuid4(),
            user_id=user_id,
        )
    
    def add_xp(self, amount: int) -> int:
        """
        Add XP to the player.
        Returns the number of levels gained.
        """
        self.current_xp += amount
        levels_gained = 0
        
        while self.current_xp >= self.xp_to_next_level:
            self.current_xp -= self.xp_to_next_level
            self.level += 1
            levels_gained += 1
            self.stat_points_available += 5
            # XP curve: each level requires more XP
            self.xp_to_next_level = self._calculate_xp_for_level(self.level + 1)
        
        return levels_gained
    
    def add_gold(self, amount: int) -> None:
        """Add gold to the player."""
        self.gold += amount
    
    def spend_gold(self, amount: int) -> bool:
        """
        Spend gold. Returns True if successful.
        """
        if self.gold >= amount:
            self.gold -= amount
            return True
        return False
    
    def _calculate_xp_for_level(self, level: int) -> int:
        """Calculate XP required to reach a level."""
        # Formula: 100 * level^1.5
        return int(100 * (level ** 1.5))
    
    @property
    def xp_progress_percent(self) -> float:
        """Get XP progress as a percentage."""
        if self.xp_to_next_level == 0:
            return 100.0
        return (self.current_xp / self.xp_to_next_level) * 100


@dataclass
class PlayerEquipmentLoadout:
    """
    Player's equipped items.
    References to ItemInstance IDs.
    """
    id: UUID
    player_id: UUID
    weapon_primary_id: Optional[UUID] = None
    weapon_secondary_id: Optional[UUID] = None
    head_id: Optional[UUID] = None
    armor_id: Optional[UUID] = None
    artifact_id: Optional[UUID] = None
    blessing_id: Optional[UUID] = None
    consumable_id: Optional[UUID] = None
    
    @classmethod
    def create(cls, player_id: UUID) -> "PlayerEquipmentLoadout":
        """Create an empty loadout for a player."""
        return cls(
            id=uuid4(),
            player_id=player_id,
        )
