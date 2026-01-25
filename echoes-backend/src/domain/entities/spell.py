"""
Echoes Backend - Spell Domain Entity
"""
from dataclasses import dataclass, field
from typing import List
from uuid import UUID

from src.domain.enums.types import SpellType
from src.domain.value_objects.effect import EffectPayload


@dataclass
class Spell:
    """
    Spell entity - an ability attached to a weapon.
    Each weapon provides up to 3 spells (2 skills + 1 ultimate per weapon).
    """
    id: UUID
    weapon_blueprint_id: UUID
    name: str
    description: str
    spell_type: SpellType
    spell_order: int  # 1-3 for primary weapon, 4-6 for secondary
    cooldown_turns: int = 0
    echo_cost: int = 0  # Echo required to cast (0 for non-ultimates)
    effects: List[EffectPayload] = field(default_factory=list)
    
    @property
    def is_ultimate(self) -> bool:
        """Check if this is an ultimate ability."""
        return self.spell_type == SpellType.ULTIMATE
    
    @property
    def is_basic(self) -> bool:
        """Check if this is a basic attack."""
        return self.spell_type == SpellType.BASIC
    
    @property
    def has_cooldown(self) -> bool:
        """Check if this spell has a cooldown."""
        return self.cooldown_turns > 0
    
    @property
    def requires_echo(self) -> bool:
        """Check if this spell requires Echo to cast."""
        return self.echo_cost > 0
    
    @classmethod
    def from_dict(cls, data: dict) -> "Spell":
        """Create a Spell from a dictionary."""
        effects = [
            EffectPayload.from_dict(e) if isinstance(e, dict) else e
            for e in data.get("effects", [])
        ]
        
        return cls(
            id=data["id"],
            weapon_blueprint_id=data["weapon_blueprint_id"],
            name=data["name"],
            description=data.get("description", ""),
            spell_type=SpellType(data["spell_type"]),
            spell_order=data.get("spell_order", 1),
            cooldown_turns=data.get("cooldown_turns", 0),
            echo_cost=data.get("echo_cost", 0),
            effects=effects,
        )
