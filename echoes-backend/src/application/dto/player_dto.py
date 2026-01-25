"""
Echoes Backend - Player DTOs
Data Transfer Objects for player operations.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from uuid import UUID


@dataclass
class PlayerProfileDTO:
    """Player profile information."""
    id: UUID
    username: str
    level: int
    current_xp: int
    xp_to_next_level: int
    gold: int
    stat_points_available: int
    is_public: bool = True


@dataclass
class PlayerStatsDTO:
    """Player combat stats (calculated from equipment)."""
    max_hp: int
    ad: int
    ap: int
    armor: int
    mr: int
    speed: int
    crit_chance: float
    crit_damage: float


@dataclass
class EquipmentLoadoutDTO:
    """Player's equipped items."""
    weapon_primary: Optional["ItemInstanceDTO"] = None
    weapon_secondary: Optional["ItemInstanceDTO"] = None
    head: Optional["ItemInstanceDTO"] = None
    armor: Optional["ItemInstanceDTO"] = None
    artifact: Optional["ItemInstanceDTO"] = None
    blessing: Optional["ItemInstanceDTO"] = None
    consumable: Optional["ItemInstanceDTO"] = None


@dataclass
class SpellDTO:
    """Spell information."""
    id: UUID
    name: str
    description: str
    spell_type: str
    cooldown_turns: int
    echo_cost: int
    is_ultimate: bool


@dataclass
class ItemInstanceDTO:
    """Item instance information."""
    id: UUID
    blueprint_id: UUID
    name: str
    description: str
    item_type: str
    rarity: str
    item_level: int
    item_xp: int
    item_xp_to_next_level: int
    is_equipped: bool
    equipped_slot: Optional[str] = None
    spells: List[SpellDTO] = field(default_factory=list)


@dataclass
class InventoryDTO:
    """Player's inventory."""
    items: List[ItemInstanceDTO]
    total_count: int


@dataclass
class CreatePlayerInput:
    """Input for creating a new player."""
    user_id: UUID


@dataclass
class EquipItemInput:
    """Input for equipping an item."""
    player_id: UUID
    item_instance_id: UUID
    slot: str


@dataclass
class UpgradeItemInput:
    """Input for upgrading an item."""
    player_id: UUID
    item_instance_id: UUID
    xp_amount: int
