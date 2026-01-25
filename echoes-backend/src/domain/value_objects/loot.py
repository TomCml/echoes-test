"""
Echoes Backend - Loot Value Objects
Data structures for loot drops and rewards.
"""
from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class LootDrop:
    """
    Represents a single loot drop result.
    """
    item_blueprint_id: UUID
    quantity: int = 1
    
    @classmethod
    def from_dict(cls, data: dict) -> "LootDrop":
        """Create from dictionary."""
        return cls(
            item_blueprint_id=UUID(data["item_blueprint_id"]),
            quantity=data.get("quantity", 1),
        )


@dataclass(frozen=True)
class CombatReward:
    """
    Complete rewards from winning a combat.
    """
    xp_gained: int
    gold_gained: int
    loot_drops: tuple[LootDrop, ...] = ()
    echo_gained: int = 0
    
    @property
    def has_loot(self) -> bool:
        """Check if there are any loot drops."""
        return len(self.loot_drops) > 0


@dataclass(frozen=True)
class QuestReward:
    """
    Rewards from completing a quest.
    """
    xp: int = 0
    gold: int = 0
    item_blueprint_id: Optional[UUID] = None
