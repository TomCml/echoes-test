"""
Echoes Backend - Effect Value Objects
Data structures for spell effects and status instances.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class EffectPayload:
    """
    Immutable payload describing an effect to execute.
    Stored in JSONB columns for spells and abilities.
    """
    opcode: str
    params: Dict[str, Any] = field(default_factory=dict)
    order: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EffectPayload":
        """Create from dictionary (e.g., from JSON)."""
        return cls(
            opcode=data["opcode"],
            params=data.get("params", {}),
            order=data.get("order", 0),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "opcode": self.opcode,
            "params": self.params,
            "order": self.order,
        }


@dataclass
class StatusInstance:
    """
    Instance of an active status effect on an entity.
    Mutable because duration decreases over time.
    """
    remaining: int  # Turns remaining
    stacks: int = 1
    
    def tick(self) -> bool:
        """
        Decrement remaining turns.
        Returns True if the status should be removed.
        """
        self.remaining -= 1
        return self.remaining <= 0
    
    def add_stacks(self, amount: int, max_stacks: Optional[int] = None) -> None:
        """Add stacks, respecting optional maximum."""
        self.stacks += amount
        if max_stacks is not None:
            self.stacks = min(self.stacks, max_stacks)
    
    def remove_stacks(self, amount: int) -> bool:
        """
        Remove stacks.
        Returns True if all stacks are removed.
        """
        self.stacks -= amount
        return self.stacks <= 0


@dataclass(frozen=True)
class StatusDefinition:
    """
    Definition of a status effect type.
    Loaded from database status_definitions table.
    """
    code: str
    display_name: str
    description: str
    icon_key: str
    is_debuff: bool = False
    is_stackable: bool = False
    max_stacks: int = 1
    tick_trigger: str = "ON_TURN_END"  # TickTrigger enum value
    tick_effect: Optional[EffectPayload] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StatusDefinition":
        """Create from dictionary."""
        tick_effect = None
        if data.get("tick_effect"):
            tick_effect = EffectPayload.from_dict(data["tick_effect"])
        
        return cls(
            code=data["code"],
            display_name=data["display_name"],
            description=data.get("description", ""),
            icon_key=data.get("icon_key", ""),
            is_debuff=data.get("is_debuff", False),
            is_stackable=data.get("is_stackable", False),
            max_stacks=data.get("max_stacks", 1),
            tick_trigger=data.get("tick_trigger", "ON_TURN_END"),
            tick_effect=tick_effect,
        )
