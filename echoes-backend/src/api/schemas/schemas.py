"""
Echoes Backend - Pydantic Schemas
Request/Response schemas for API endpoints.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# Common
# =============================================================================

class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    code: str
    details: Optional[Dict[str, Any]] = None


# =============================================================================
# Auth
# =============================================================================

class TwitchCallbackRequest(BaseModel):
    """Twitch OAuth callback request."""
    code: str


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """User information response."""
    id: UUID
    twitch_id: str
    username: str
    is_profile_public: bool
    created_at: datetime


# =============================================================================
# Player
# =============================================================================

class PlayerProfileResponse(BaseModel):
    """Player profile response."""
    id: UUID
    username: str
    level: int
    current_xp: int
    xp_to_next_level: int
    xp_progress_percent: float
    gold: int
    stat_points_available: int


class PlayerStatsResponse(BaseModel):
    """Player combat stats."""
    max_hp: int
    ad: int
    ap: int
    armor: int
    mr: int
    speed: int
    crit_chance: float
    crit_damage: float


class SpellResponse(BaseModel):
    """Spell information."""
    id: UUID
    name: str
    description: str
    spell_type: str
    spell_order: int
    cooldown_turns: int
    echo_cost: int


class ItemInstanceResponse(BaseModel):
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
    stats: Dict[str, Any]
    spells: List[SpellResponse] = []


class InventoryResponse(BaseModel):
    """Player inventory."""
    items: List[ItemInstanceResponse]
    total_count: int


class EquipItemRequest(BaseModel):
    """Request to equip an item."""
    item_instance_id: UUID
    slot: str


class UpgradeItemRequest(BaseModel):
    """Request to upgrade an item."""
    xp_amount: int


# =============================================================================
# Combat
# =============================================================================

class StartCombatRequest(BaseModel):
    """Request to start combat."""
    monster_blueprint_id: UUID
    monster_level: Optional[int] = None


class CombatActionRequest(BaseModel):
    """Request to perform a combat action."""
    action_type: str = Field(..., pattern="^(spell|basic_attack|consumable)$")
    spell_id: Optional[UUID] = None


class EntityStateResponse(BaseModel):
    """Combat entity state."""
    name: str
    current_hp: int
    max_hp: int
    hp_percent: float
    statuses: Dict[str, int] = {}
    shield: int = 0


class PlayerCombatStateResponse(EntityStateResponse):
    """Player combat state."""
    echo_current: int
    echo_max: int
    spell_cooldowns: Dict[str, int] = {}
    consumable_uses: int


class CombatStateResponse(BaseModel):
    """Full combat state."""
    session_id: UUID
    status: str
    turn_count: int
    current_turn: str
    player: PlayerCombatStateResponse
    monster: EntityStateResponse
    available_actions: List[str]
    logs: List[str] = []


class CombatRewardResponse(BaseModel):
    """Combat rewards."""
    xp_gained: int
    gold_gained: int
    levels_gained: int = 0
    items_dropped: List[Dict[str, Any]] = []


class CombatResultResponse(BaseModel):
    """Combat action result."""
    success: bool
    message: str
    combat_state: Optional[CombatStateResponse] = None
    combat_ended: bool = False
    result: Optional[str] = None
    rewards: Optional[CombatRewardResponse] = None


# =============================================================================
# Monsters
# =============================================================================

class MonsterBlueprintResponse(BaseModel):
    """Monster blueprint information."""
    id: UUID
    name: str
    description: str
    base_level: int
    is_boss: bool
    sprite_key: str
    base_stats: Dict[str, Any]


class MonsterListResponse(BaseModel):
    """List of monsters."""
    monsters: List[MonsterBlueprintResponse]
    total_count: int


# =============================================================================
# Dungeons
# =============================================================================

class DungeonResponse(BaseModel):
    """Dungeon information."""
    id: UUID
    name: str
    description: str
    level_requirement: int
    recommended_level: int
    is_unlocked: bool = False
    best_clear_time_ms: Optional[int] = None
    clear_count: int = 0


class DungeonListResponse(BaseModel):
    """List of dungeons."""
    dungeons: List[DungeonResponse]


# =============================================================================
# Leaderboard
# =============================================================================

class LeaderboardEntryResponse(BaseModel):
    """Leaderboard entry."""
    rank: int
    player_id: UUID
    username: str
    score: int


class LeaderboardResponse(BaseModel):
    """Leaderboard data."""
    leaderboard_type: str
    entries: List[LeaderboardEntryResponse]
    total_entries: int


class PlayerRankResponse(BaseModel):
    """Player's rank on a leaderboard."""
    leaderboard_type: str
    rank: int
    score: int
    percentile: float
