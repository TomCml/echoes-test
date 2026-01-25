"""
Echoes Backend - Monster Domain Entities
"""
from dataclasses import dataclass, field
from typing import List, Optional
from uuid import UUID

from src.domain.enums.types import AIBehavior
from src.domain.value_objects.effect import EffectPayload
from src.domain.value_objects.stats import StatsBlock, StatsScaling


@dataclass
class MonsterAbility:
    """
    An ability that a monster can use.
    """
    id: UUID
    monster_blueprint_id: UUID
    name: str
    cooldown: int = 0
    priority: int = 1  # Higher priority = more likely to use
    condition_expr: Optional[str] = None  # e.g., "T_HP_PERCENT < 0.5"
    effects: List[EffectPayload] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: dict) -> "MonsterAbility":
        """Create from dictionary."""
        effects = [
            EffectPayload.from_dict(e) if isinstance(e, dict) else e
            for e in data.get("effects", [])
        ]
        
        return cls(
            id=data["id"],
            monster_blueprint_id=data["monster_blueprint_id"],
            name=data["name"],
            cooldown=data.get("cooldown", 0),
            priority=data.get("priority", 1),
            condition_expr=data.get("condition_expr"),
            effects=effects,
        )


@dataclass
class MonsterBlueprint:
    """
    Blueprint for a monster type.
    Static data - monsters are instantiated from blueprints during combat.
    """
    id: UUID
    name: str
    description: str
    base_level: int
    ai_behavior: AIBehavior = AIBehavior.BASIC
    loot_table_id: Optional[UUID] = None
    xp_reward: int = 0
    gold_reward_min: int = 0
    gold_reward_max: int = 0
    is_boss: bool = False
    sprite_key: str = ""
    
    # Base stats
    base_stats: StatsBlock = field(default_factory=StatsBlock.zero)
    
    # Scaling per level
    scaling: StatsScaling = field(default_factory=StatsScaling.zero)
    
    # Abilities
    abilities: List[MonsterAbility] = field(default_factory=list)
    
    def get_stats_at_level(self, level: int) -> StatsBlock:
        """Calculate stats at a specific monster level."""
        level_diff = level - self.base_level
        return self.base_stats.scale(level_diff, self.scaling)
    
    def get_hp_at_level(self, level: int) -> int:
        """Get max HP at a specific level."""
        stats = self.get_stats_at_level(level)
        return stats.max_hp


@dataclass
class LootTable:
    """
    Loot table containing possible drops.
    """
    id: UUID
    name: str
    entries: List["LootTableEntry"] = field(default_factory=list)


@dataclass
class LootTableEntry:
    """
    Single entry in a loot table.
    """
    id: UUID
    loot_table_id: UUID
    item_blueprint_id: UUID
    weight: int = 100  # Higher weight = more likely to drop
    min_quantity: int = 1
    max_quantity: int = 1
    min_player_level: int = 1
