"""
Echoes Backend - Domain Enums
All game-related enumeration types.
"""
from enum import Enum, auto


class ItemType(str, Enum):
    """Type of item."""
    WEAPON = "WEAPON"
    HEAD = "HEAD"
    ARMOR = "ARMOR"
    ARTIFACT = "ARTIFACT"
    BLESSING = "BLESSING"
    CONSUMABLE = "CONSUMABLE"


class Rarity(str, Enum):
    """Item rarity levels."""
    COMMON = "COMMON"
    UNCOMMON = "UNCOMMON"
    RARE = "RARE"
    EPIC = "EPIC"
    LEGENDARY = "LEGENDARY"


class DamageType(str, Enum):
    """Types of damage that can be dealt."""
    PHYSICAL = "PHYSICAL"
    MAGIC = "MAGIC"
    TRUE = "TRUE"
    MIXED = "MIXED"
    STASIS = "STASIS"


class SpellType(str, Enum):
    """Type of spell ability."""
    BASIC = "BASIC"
    SKILL = "SKILL"
    ULTIMATE = "ULTIMATE"


class EquipmentSlot(str, Enum):
    """Equipment slots for items."""
    WEAPON_PRIMARY = "WEAPON_PRIMARY"
    WEAPON_SECONDARY = "WEAPON_SECONDARY"
    HEAD = "HEAD"
    ARMOR = "ARMOR"
    ARTIFACT = "ARTIFACT"
    BLESSING = "BLESSING"
    CONSUMABLE = "CONSUMABLE"


class CombatStatus(str, Enum):
    """Status of a combat session."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    PLAYER_TURN = "PLAYER_TURN"
    MONSTER_TURN = "MONSTER_TURN"
    VICTORY = "VICTORY"
    DEFEAT = "DEFEAT"
    ABANDONED = "ABANDONED"


class TickTrigger(str, Enum):
    """When a status effect tick is triggered."""
    ON_TURN_START = "ON_TURN_START"
    ON_TURN_END = "ON_TURN_END"
    ON_HIT = "ON_HIT"
    ON_DAMAGED = "ON_DAMAGED"
    IMMEDIATE = "IMMEDIATE"


class QuestType(str, Enum):
    """Type of quest."""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    STORY = "STORY"
    EVENT = "EVENT"


class AchievementCategory(str, Enum):
    """Category of achievement."""
    COMBAT = "COMBAT"
    EXPLORATION = "EXPLORATION"
    COLLECTION = "COLLECTION"
    SOCIAL = "SOCIAL"
    MASTERY = "MASTERY"


class LeaderboardType(str, Enum):
    """Type of leaderboard."""
    GLOBAL_LEVEL = "GLOBAL_LEVEL"
    ACHIEVEMENTS_COUNT = "ACHIEVEMENTS_COUNT"
    BOSS_SPEEDRUN = "BOSS_SPEEDRUN"
    TOTAL_MONSTERS_KILLED = "TOTAL_MONSTERS_KILLED"


class AIBehavior(str, Enum):
    """Monster AI behavior patterns."""
    BASIC = "basic"
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    HEALER = "healer"
    BALANCED = "balanced"
    BOSS = "boss"
