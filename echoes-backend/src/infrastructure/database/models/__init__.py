"""Echoes Backend - Database models init."""
# Import all models so they are registered with Base.metadata for Alembic
from src.infrastructure.database.models.user_model import UserModel
from src.infrastructure.database.models.player_model import (
    PlayerModel,
    PlayerEquipmentLoadoutModel,
)
from src.infrastructure.database.models.item_model import (
    ItemBlueprintModel,
    WeaponBlueprintModel,
    EquipmentBlueprintModel,
    ConsumableBlueprintModel,
    ItemInstanceModel,
)
from src.infrastructure.database.models.spell_model import SpellModel
from src.infrastructure.database.models.monster_model import (
    LootTableModel,
    LootTableEntryModel,
    MonsterBlueprintModel,
    MonsterAbilityModel,
)
from src.infrastructure.database.models.combat_model import (
    CombatSessionModel,
    CombatSpellCooldownModel,
    CombatLogModel,
    StatusDefinitionModel,
)
from src.infrastructure.database.models.progression_model import (
    AchievementModel,
    PlayerAchievementModel,
    QuestModel,
    PlayerQuestModel,
    DungeonModel,
    DungeonMonsterSequenceModel,
    PlayerDungeonProgressModel,
    LeaderboardEntryModel,
)

__all__ = [
    "UserModel",
    "PlayerModel",
    "PlayerEquipmentLoadoutModel",
    "ItemBlueprintModel",
    "WeaponBlueprintModel",
    "EquipmentBlueprintModel",
    "ConsumableBlueprintModel",
    "ItemInstanceModel",
    "SpellModel",
    "LootTableModel",
    "LootTableEntryModel",
    "MonsterBlueprintModel",
    "MonsterAbilityModel",
    "CombatSessionModel",
    "CombatSpellCooldownModel",
    "CombatLogModel",
    "StatusDefinitionModel",
    "AchievementModel",
    "PlayerAchievementModel",
    "QuestModel",
    "PlayerQuestModel",
    "DungeonModel",
    "DungeonMonsterSequenceModel",
    "PlayerDungeonProgressModel",
    "LeaderboardEntryModel",
]
