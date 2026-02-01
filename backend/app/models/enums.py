from enum import StrEnum


class SpellType(StrEnum):
    BASIC = "basic"
    SKILL = "skill"
    ULTIMATE = "ultimate"


class EquipmentSlot(StrEnum):
    WEAPON_PRIMARY = "weapon_primary"
    WEAPON_SECONDARY = "weapon_secondary"
    HEAD = "head"
    ARMOR = "armor"
    ARTIFACT = "artifact"
    BLESSING = "blessing"
    CONSUMABLE = "consumable"


class Rarity(StrEnum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class CombatStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PLAYER_TURN = "player_turn"
    MONSTER_TURN = "monster_turn"
    VICTORY = "victory"
    DEFEAT = "defeat"
    ABANDONED = "abandoned"


class TickTrigger(StrEnum):
    ON_TURN_START = "on_turn_start"
    ON_TURN_END = "on_turn_end"
    ON_HIT = "on_hit"
    ON_DAMAGED = "on_damaged"
    IMMEDIATE = "immediate"
