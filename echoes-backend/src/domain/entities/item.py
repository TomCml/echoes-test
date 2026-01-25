"""
Echoes Backend - Item Domain Entities
Blueprints (static definitions) and Instances (player-owned).
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from src.domain.enums.types import DamageType, EquipmentSlot, ItemType, Rarity
from src.domain.value_objects.effect import EffectPayload
from src.domain.value_objects.stats import StatsBlock, StatsScaling


@dataclass
class ItemBlueprint:
    """
    Base blueprint for all items.
    Static data loaded from database.
    """
    id: UUID
    name: str
    description: str
    item_type: ItemType
    rarity: Rarity
    level_requirement: int = 1
    max_level: int = 100
    is_tradeable: bool = True
    
    # Base stats
    base_stats: StatsBlock = field(default_factory=StatsBlock.zero)
    
    # Scaling per item level
    scaling: StatsScaling = field(default_factory=StatsScaling.zero)
    
    def get_stats_at_level(self, level: int) -> StatsBlock:
        """Calculate stats at a specific item level."""
        return self.base_stats.scale(level, self.scaling)


@dataclass
class WeaponBlueprint(ItemBlueprint):
    """
    Blueprint for weapon items.
    Weapons have a damage type and provide spells.
    """
    damage_type: DamageType = DamageType.PHYSICAL
    
    def __post_init__(self):
        self.item_type = ItemType.WEAPON


@dataclass
class EquipmentBlueprint(ItemBlueprint):
    """
    Blueprint for equipment items (head, armor, artifact, blessing).
    Equipment has passive effects.
    """
    slot: EquipmentSlot = EquipmentSlot.ARMOR
    passive_effects: List[EffectPayload] = field(default_factory=list)


@dataclass
class ConsumableBlueprint(ItemBlueprint):
    """
    Blueprint for consumable items.
    Consumables have effects and limited uses per combat.
    """
    effects: List[EffectPayload] = field(default_factory=list)
    uses_per_combat: int = 1
    
    def __post_init__(self):
        self.item_type = ItemType.CONSUMABLE


@dataclass
class ItemInstance:
    """
    Instance of an item owned by a player.
    Has its own level and XP progression.
    """
    id: UUID
    blueprint_id: UUID
    owner_id: UUID
    item_level: int = 1
    item_xp: int = 0
    item_xp_to_next_level: int = 100
    is_equipped: bool = False
    equipped_slot: Optional[EquipmentSlot] = None
    acquired_at: datetime = field(default_factory=datetime.utcnow)
    
    # Cached reference to blueprint (not persisted)
    _blueprint: Optional[ItemBlueprint] = field(default=None, repr=False)
    
    @classmethod
    def create(cls, blueprint_id: UUID, owner_id: UUID) -> "ItemInstance":
        """Create a new item instance."""
        return cls(
            id=uuid4(),
            blueprint_id=blueprint_id,
            owner_id=owner_id,
        )
    
    def add_xp(self, amount: int) -> int:
        """
        Add XP to the item.
        Returns the number of levels gained.
        """
        self.item_xp += amount
        levels_gained = 0
        
        max_level = 100  # Default, should come from blueprint
        if self._blueprint:
            max_level = self._blueprint.max_level
        
        while self.item_xp >= self.item_xp_to_next_level and self.item_level < max_level:
            self.item_xp -= self.item_xp_to_next_level
            self.item_level += 1
            levels_gained += 1
            self.item_xp_to_next_level = self._calculate_xp_for_level(self.item_level + 1)
        
        return levels_gained
    
    def _calculate_xp_for_level(self, level: int) -> int:
        """Calculate XP required for next item level."""
        return int(50 * (level ** 1.3))
    
    def equip(self, slot: EquipmentSlot) -> None:
        """Mark the item as equipped in a slot."""
        self.is_equipped = True
        self.equipped_slot = slot
    
    def unequip(self) -> None:
        """Mark the item as unequipped."""
        self.is_equipped = False
        self.equipped_slot = None
    
    def get_current_stats(self) -> StatsBlock:
        """Get stats based on current item level."""
        if self._blueprint:
            return self._blueprint.get_stats_at_level(self.item_level)
        return StatsBlock.zero()
