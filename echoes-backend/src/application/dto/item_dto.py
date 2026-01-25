"""
Echoes Backend - Item DTOs
Data Transfer Objects for item operations.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID


@dataclass
class ItemBlueprintDTO:
    """Item blueprint information."""
    id: UUID
    name: str
    description: str
    item_type: str
    rarity: str
    level_requirement: int
    max_level: int
    base_stats: Dict[str, Any]


@dataclass
class WeaponBlueprintDTO(ItemBlueprintDTO):
    """Weapon blueprint with spells."""
    damage_type: str
    spells: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class EquipmentBlueprintDTO(ItemBlueprintDTO):
    """Equipment blueprint with passive effects."""
    slot: str
    passive_effects: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ConsumableBlueprintDTO(ItemBlueprintDTO):
    """Consumable blueprint with effects."""
    effects: List[Dict[str, Any]] = field(default_factory=list)
    uses_per_combat: int = 1
