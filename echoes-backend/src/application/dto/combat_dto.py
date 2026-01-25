"""
Echoes Backend - Combat DTOs
Data Transfer Objects for combat operations.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from uuid import UUID

from src.domain.enums.types import CombatStatus, DamageType


@dataclass
class StartCombatInput:
    """Input for starting combat."""
    player_id: UUID
    monster_blueprint_id: UUID
    monster_level: Optional[int] = None  # Uses base_level if not specified


@dataclass
class CombatActionInput:
    """Input for executing a combat action."""
    session_id: UUID
    action_type: str  # "spell", "basic_attack", "consumable"
    spell_id: Optional[UUID] = None


@dataclass
class EntityStateDTO:
    """Combat entity state snapshot."""
    name: str
    current_hp: int
    max_hp: int
    statuses: Dict[str, int] = field(default_factory=dict)  # code -> stacks
    shield: int = 0


@dataclass
class PlayerStateDTO(EntityStateDTO):
    """Player combat state snapshot."""
    echo_current: int = 0
    echo_max: int = 100
    spell_cooldowns: Dict[UUID, int] = field(default_factory=dict)
    consumable_uses: int = 1


@dataclass
class CombatStateDTO:
    """Complete combat state snapshot."""
    session_id: UUID
    status: CombatStatus
    turn_count: int
    current_turn: str  # "player" or "monster"
    player: PlayerStateDTO
    monster: EntityStateDTO
    logs: List[str] = field(default_factory=list)


@dataclass
class CombatActionResultDTO:
    """Result of a combat action."""
    success: bool
    message: str
    combat_state: Optional[CombatStateDTO] = None
    combat_ended: bool = False
    result: Optional[str] = None  # "victory", "defeat", "fled"


@dataclass
class CombatRewardDTO:
    """Rewards from combat victory."""
    xp_gained: int
    gold_gained: int
    levels_gained: int = 0
    items_dropped: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class DamageLogDTO:
    """Damage event log entry."""
    source_name: str
    target_name: str
    damage_amount: int
    damage_type: DamageType
    was_critical: bool = False
    ability_name: Optional[str] = None
