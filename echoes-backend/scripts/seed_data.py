"""
Echoes Backend - Seed Data Script
Seeds the database with initial game content.
"""
import asyncio
import json
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import async_session_factory, engine
from src.infrastructure.database.models import (
    ItemBlueprintModel,
    WeaponBlueprintModel,
    EquipmentBlueprintModel,
    ConsumableBlueprintModel,
    SpellModel,
    MonsterBlueprintModel,
    MonsterAbilityModel,
    LootTableModel,
    LootTableEntryModel,
    DungeonModel,
    DungeonMonsterSequenceModel,
    StatusDefinitionModel,
    AchievementModel,
    QuestModel,
)
from src.domain.enums.types import (
    ItemType,
    Rarity,
    DamageType,
    SpellType,
    EquipmentSlot,
    AchievementCategory,
    QuestType,
)


# =============================================================================
# Status Definitions
# =============================================================================
STATUS_DEFINITIONS = [
    {
        "code": "BURN",
        "display_name": "Burning",
        "description": "Taking fire damage each turn",
        "is_debuff": True,
        "is_stackable": True,
        "max_stacks": 5,
        "tick_trigger": "ON_TURN_START",
        "tick_effect": {
            "opcode": "damage",
            "params": {"formula": "20", "damage_type": "MAGIC", "label": "burn"}
        },
    },
    {
        "code": "POISON",
        "display_name": "Poisoned",
        "description": "Taking poison damage each turn",
        "is_debuff": True,
        "is_stackable": True,
        "max_stacks": 10,
        "tick_trigger": "ON_TURN_END",
        "tick_effect": {
            "opcode": "damage",
            "params": {"formula": "10", "damage_type": "TRUE", "label": "poison"}
        },
    },
    {
        "code": "BLEED",
        "display_name": "Bleeding",
        "description": "Physical damage over time",
        "is_debuff": True,
        "is_stackable": True,
        "max_stacks": 3,
        "tick_trigger": "ON_TURN_END",
        "tick_effect": {
            "opcode": "damage_percent_max_hp",
            "params": {"percent": 0.02, "damage_type": "PHYSICAL", "label": "bleed"}
        },
    },
    {
        "code": "REGEN",
        "display_name": "Regeneration",
        "description": "Healing each turn",
        "is_debuff": False,
        "is_stackable": False,
        "max_stacks": 1,
        "tick_trigger": "ON_TURN_END",
        "tick_effect": {
            "opcode": "heal_percent_max_hp",
            "params": {"percent": 0.05, "label": "regeneration"}
        },
    },
    {
        "code": "BLOSSOM",
        "display_name": "Spirit Blossom",
        "description": "Marked by spirit energy, takes bonus damage",
        "is_debuff": True,
        "is_stackable": True,
        "max_stacks": 3,
        "tick_trigger": "ON_DAMAGED",
        "tick_effect": None,
    },
]


# =============================================================================
# Weapons & Spells
# =============================================================================
def create_weapons():
    """Create starter weapons with spells."""
    weapons = []
    
    # Spirit Blade (AD weapon)
    spirit_blade_id = uuid4()
    weapons.append({
        "blueprint": ItemBlueprintModel(
            id=spirit_blade_id,
            name="Spirit Blade",
            description="A blade infused with spirit energy",
            item_type=ItemType.WEAPON,
            rarity=Rarity.COMMON,
            level_requirement=1,
            base_ad=15,
            base_speed=5,
            scaling_ad_per_level=1.5,
        ),
        "weapon": WeaponBlueprintModel(
            id=spirit_blade_id,
            damage_type=DamageType.PHYSICAL,
        ),
        "spells": [
            SpellModel(
                id=uuid4(),
                weapon_blueprint_id=spirit_blade_id,
                name="Quick Strike",
                description="A swift attack",
                spell_type=SpellType.BASIC,
                spell_order=1,
                cooldown_turns=0,
                echo_cost=0,
                effects=[{
                    "opcode": "damage",
                    "params": {"formula": "AD * 1.0", "damage_type": "PHYSICAL", "can_crit": True}
                }],
            ),
            SpellModel(
                id=uuid4(),
                weapon_blueprint_id=spirit_blade_id,
                name="Blossom Slash",
                description="Slash marking the target with spirit energy",
                spell_type=SpellType.SKILL,
                spell_order=2,
                cooldown_turns=3,
                echo_cost=0,
                effects=[
                    {"opcode": "damage", "params": {"formula": "AD * 1.5", "damage_type": "PHYSICAL"}},
                    {"opcode": "apply_status", "params": {"status_code": "BLOSSOM", "duration_turns": 2}}
                ],
            ),
            SpellModel(
                id=uuid4(),
                weapon_blueprint_id=spirit_blade_id,
                name="Spirit Rend",
                description="Unleash spirit energy for massive damage",
                spell_type=SpellType.ULTIMATE,
                spell_order=3,
                cooldown_turns=0,
                echo_cost=100,
                effects=[
                    {"opcode": "damage", "params": {"formula": "AD * 3.0", "damage_type": "PHYSICAL", "can_crit": True}},
                    {"opcode": "bonus_damage_if_target_has_status", "params": {
                        "status_code": "BLOSSOM",
                        "formula": "AD * 0.5 * T_STACKS_BLOSSOM",
                        "damage_type": "TRUE",
                        "consume_status": True
                    }}
                ],
            ),
        ],
    })
    
    # Spirit Staff (AP weapon)
    spirit_staff_id = uuid4()
    weapons.append({
        "blueprint": ItemBlueprintModel(
            id=spirit_staff_id,
            name="Spirit Staff",
            description="A staff channeling spirit magic",
            item_type=ItemType.WEAPON,
            rarity=Rarity.COMMON,
            level_requirement=1,
            base_ap=15,
            base_speed=3,
            scaling_ap_per_level=1.5,
        ),
        "weapon": WeaponBlueprintModel(
            id=spirit_staff_id,
            damage_type=DamageType.MAGIC,
        ),
        "spells": [
            SpellModel(
                id=uuid4(),
                weapon_blueprint_id=spirit_staff_id,
                name="Spirit Bolt",
                description="Fire a bolt of spirit energy",
                spell_type=SpellType.BASIC,
                spell_order=1,
                cooldown_turns=0,
                echo_cost=0,
                effects=[{
                    "opcode": "damage",
                    "params": {"formula": "AP * 0.8", "damage_type": "MAGIC"}
                }],
            ),
            SpellModel(
                id=uuid4(),
                weapon_blueprint_id=spirit_staff_id,
                name="Burning Blossom",
                description="Set the target ablaze with spirit fire",
                spell_type=SpellType.SKILL,
                spell_order=2,
                cooldown_turns=2,
                echo_cost=0,
                effects=[
                    {"opcode": "damage", "params": {"formula": "AP * 0.6", "damage_type": "MAGIC"}},
                    {"opcode": "apply_status", "params": {"status_code": "BURN", "duration_turns": 3, "stacks": 2}}
                ],
            ),
            SpellModel(
                id=uuid4(),
                weapon_blueprint_id=spirit_staff_id,
                name="Spirit Inferno",
                description="Unleash devastating spirit fire",
                spell_type=SpellType.ULTIMATE,
                spell_order=3,
                cooldown_turns=0,
                echo_cost=100,
                effects=[
                    {"opcode": "damage", "params": {"formula": "AP * 2.5 + T_STACKS_BURN * 50", "damage_type": "MAGIC"}},
                    {"opcode": "remove_status", "params": {"status_code": "BURN"}}
                ],
            ),
        ],
    })
    
    return weapons


# =============================================================================
# Equipment
# =============================================================================
def create_equipment():
    """Create starter equipment."""
    equipment = []
    
    # Spirit Hood (Head)
    hood_id = uuid4()
    equipment.append({
        "blueprint": ItemBlueprintModel(
            id=hood_id,
            name="Spirit Hood",
            description="A hood woven with spirit threads",
            item_type=ItemType.ARMOR,
            rarity=Rarity.COMMON,
            level_requirement=1,
            base_mr=5,
            base_max_hp=20,
            scaling_mr_per_level=0.3,
            scaling_hp_per_level=2,
        ),
        "equipment": EquipmentBlueprintModel(
            id=hood_id,
            slot=EquipmentSlot.HEAD,
            passive_effects=[],
        ),
    })
    
    # Spirit Robe (Armor)
    robe_id = uuid4()
    equipment.append({
        "blueprint": ItemBlueprintModel(
            id=robe_id,
            name="Spirit Robe",
            description="A robe infused with protective spirits",
            item_type=ItemType.ARMOR,
            rarity=Rarity.COMMON,
            level_requirement=1,
            base_armor=5,
            base_mr=5,
            base_max_hp=50,
            scaling_armor_per_level=0.5,
            scaling_mr_per_level=0.5,
            scaling_hp_per_level=5,
        ),
        "equipment": EquipmentBlueprintModel(
            id=robe_id,
            slot=EquipmentSlot.ARMOR,
            passive_effects=[],
        ),
    })
    
    return equipment


# =============================================================================
# Consumables
# =============================================================================
def create_consumables():
    """Create consumable items."""
    consumables = []
    
    # Health Potion
    potion_id = uuid4()
    consumables.append({
        "blueprint": ItemBlueprintModel(
            id=potion_id,
            name="Spirit Essence",
            description="Restores 30% of max HP",
            item_type=ItemType.CONSUMABLE,
            rarity=Rarity.COMMON,
            level_requirement=1,
        ),
        "consumable": ConsumableBlueprintModel(
            id=potion_id,
            effects=[{
                "opcode": "heal_percent_max_hp",
                "params": {"percent": 0.3, "label": "Spirit Essence"}
            }],
            uses_per_combat=1,
        ),
    })
    
    return consumables


# =============================================================================
# Monsters
# =============================================================================
def create_monsters():
    """Create monster blueprints."""
    monsters = []
    
    # Spirit Wisp (Easy)
    wisp_id = uuid4()
    monsters.append({
        "blueprint": MonsterBlueprintModel(
            id=wisp_id,
            name="Spirit Wisp",
            description="A small, wandering spirit",
            base_level=1,
            ai_behavior="basic",
            xp_reward=25,
            gold_reward_min=5,
            gold_reward_max=15,
            is_boss=False,
            sprite_key="wisp",
            base_max_hp=80,
            base_ad=8,
            base_ap=5,
            base_armor=2,
            base_mr=2,
            base_speed=8,
            scaling_hp_per_level=15,
            scaling_ad_per_level=1.0,
        ),
        "abilities": [
            MonsterAbilityModel(
                id=uuid4(),
                monster_blueprint_id=wisp_id,
                name="Spirit Touch",
                cooldown=0,
                priority=1,
                effects=[{"opcode": "damage", "params": {"formula": "AD * 1.0", "damage_type": "MAGIC"}}],
            ),
        ],
    })
    
    # Blossom Guardian (Medium)
    guardian_id = uuid4()
    monsters.append({
        "blueprint": MonsterBlueprintModel(
            id=guardian_id,
            name="Blossom Guardian",
            description="A spirit protecting the sacred groves",
            base_level=5,
            ai_behavior="balanced",
            xp_reward=75,
            gold_reward_min=20,
            gold_reward_max=40,
            is_boss=False,
            sprite_key="guardian",
            base_max_hp=200,
            base_ad=15,
            base_ap=10,
            base_armor=8,
            base_mr=8,
            base_speed=10,
            scaling_hp_per_level=25,
            scaling_ad_per_level=1.5,
        ),
        "abilities": [
            MonsterAbilityModel(
                id=uuid4(),
                monster_blueprint_id=guardian_id,
                name="Branch Strike",
                cooldown=0,
                priority=1,
                effects=[{"opcode": "damage", "params": {"formula": "AD * 1.2", "damage_type": "PHYSICAL"}}],
            ),
            MonsterAbilityModel(
                id=uuid4(),
                monster_blueprint_id=guardian_id,
                name="Entangling Roots",
                cooldown=3,
                priority=2,
                effects=[
                    {"opcode": "damage", "params": {"formula": "AD * 0.8", "damage_type": "PHYSICAL"}},
                    {"opcode": "apply_status", "params": {"status_code": "BLEED", "duration_turns": 2}}
                ],
            ),
        ],
    })
    
    # Spirit Lord (Boss)
    lord_id = uuid4()
    monsters.append({
        "blueprint": MonsterBlueprintModel(
            id=lord_id,
            name="Spirit Lord",
            description="An ancient spirit of immense power",
            base_level=10,
            ai_behavior="boss",
            xp_reward=500,
            gold_reward_min=100,
            gold_reward_max=200,
            is_boss=True,
            sprite_key="spirit_lord",
            base_max_hp=800,
            base_ad=30,
            base_ap=30,
            base_armor=15,
            base_mr=15,
            base_speed=12,
            scaling_hp_per_level=50,
            scaling_ad_per_level=3.0,
            scaling_ap_per_level=3.0,
        ),
        "abilities": [
            MonsterAbilityModel(
                id=uuid4(),
                monster_blueprint_id=lord_id,
                name="Spirit Strike",
                cooldown=0,
                priority=1,
                effects=[{"opcode": "damage", "params": {"formula": "AD * 1.5", "damage_type": "MIXED"}}],
            ),
            MonsterAbilityModel(
                id=uuid4(),
                monster_blueprint_id=lord_id,
                name="Soul Drain",
                cooldown=4,
                priority=3,
                condition_expr="S_HP_PERCENT < 0.6",
                effects=[
                    {"opcode": "damage", "params": {"formula": "AP * 1.5", "damage_type": "MAGIC"}},
                    {"opcode": "lifesteal", "params": {"percent": 0.5}}
                ],
            ),
            MonsterAbilityModel(
                id=uuid4(),
                monster_blueprint_id=lord_id,
                name="Wrath of Spirits",
                cooldown=5,
                priority=4,
                condition_expr="S_HP_PERCENT < 0.3",
                effects=[
                    {"opcode": "damage", "params": {"formula": "max(AD, AP) * 2.5", "damage_type": "TRUE"}}
                ],
            ),
        ],
    })
    
    return monsters


# =============================================================================
# Dungeons
# =============================================================================
def create_dungeons(monsters: list):
    """Create dungeons referencing monsters."""
    dungeons = []
    
    # Map monster names to IDs
    monster_ids = {m["blueprint"].name: m["blueprint"].id for m in monsters}
    boss_id = monster_ids.get("Spirit Lord")
    wisp_id = monster_ids.get("Spirit Wisp")
    guardian_id = monster_ids.get("Blossom Guardian")
    
    # Spirit Grove
    grove_id = uuid4()
    dungeons.append({
        "dungeon": DungeonModel(
            id=grove_id,
            name="Spirit Grove",
            description="An ancient grove inhabited by spirits",
            level_requirement=1,
            recommended_level=5,
            boss_blueprint_id=boss_id,
            background_key="spirit_grove",
        ),
        "sequence": [
            DungeonMonsterSequenceModel(id=uuid4(), dungeon_id=grove_id, monster_blueprint_id=wisp_id, sequence_order=1),
            DungeonMonsterSequenceModel(id=uuid4(), dungeon_id=grove_id, monster_blueprint_id=wisp_id, sequence_order=2),
            DungeonMonsterSequenceModel(id=uuid4(), dungeon_id=grove_id, monster_blueprint_id=guardian_id, sequence_order=3),
            DungeonMonsterSequenceModel(id=uuid4(), dungeon_id=grove_id, monster_blueprint_id=boss_id, sequence_order=4),
        ],
    })
    
    return dungeons


# =============================================================================
# Achievements & Quests
# =============================================================================
def create_achievements():
    """Create achievements."""
    return [
        AchievementModel(
            id=uuid4(),
            name="First Blood",
            description="Defeat your first monster",
            category=AchievementCategory.COMBAT,
            condition_type="monsters_killed",
            condition_value=1,
            reward_xp=50,
            reward_gold=25,
        ),
        AchievementModel(
            id=uuid4(),
            name="Monster Slayer",
            description="Defeat 100 monsters",
            category=AchievementCategory.COMBAT,
            condition_type="monsters_killed",
            condition_value=100,
            reward_xp=500,
            reward_gold=200,
        ),
        AchievementModel(
            id=uuid4(),
            name="Spirit Walker",
            description="Reach level 10",
            category=AchievementCategory.PROGRESSION,
            condition_type="level_reached",
            condition_value=10,
            reward_xp=250,
            reward_gold=100,
        ),
    ]


def create_quests():
    """Create quests."""
    return [
        QuestModel(
            id=uuid4(),
            name="Daily Hunt",
            description="Defeat 5 monsters today",
            quest_type=QuestType.DAILY,
            objective_type="kill_monster",
            objective_target=5,
            reward_xp=100,
            reward_gold=50,
            is_repeatable=True,
            reset_period_hours=24,
        ),
        QuestModel(
            id=uuid4(),
            name="Weekly Challenge",
            description="Win 20 combats this week",
            quest_type=QuestType.WEEKLY,
            objective_type="win_combat",
            objective_target=20,
            reward_xp=500,
            reward_gold=300,
            is_repeatable=True,
            reset_period_hours=168,
        ),
    ]


# =============================================================================
# Main Seed Function
# =============================================================================
async def seed_database():
    """Seed the database with initial game data."""
    async with async_session_factory() as session:
        # Check if already seeded
        result = await session.execute(select(StatusDefinitionModel))
        if result.scalars().first():
            print("Database already seeded. Skipping.")
            return
        
        print("Seeding database with initial game data...")
        
        # Status definitions
        for status in STATUS_DEFINITIONS:
            session.add(StatusDefinitionModel(**status))
        print(f"  Added {len(STATUS_DEFINITIONS)} status definitions")
        
        # Weapons
        weapons = create_weapons()
        for weapon in weapons:
            session.add(weapon["blueprint"])
            session.add(weapon["weapon"])
            for spell in weapon["spells"]:
                session.add(spell)
        print(f"  Added {len(weapons)} weapons with spells")
        
        # Equipment
        equipment = create_equipment()
        for equip in equipment:
            session.add(equip["blueprint"])
            session.add(equip["equipment"])
        print(f"  Added {len(equipment)} equipment pieces")
        
        # Consumables
        consumables = create_consumables()
        for consumable in consumables:
            session.add(consumable["blueprint"])
            session.add(consumable["consumable"])
        print(f"  Added {len(consumables)} consumables")
        
        # Monsters
        monsters = create_monsters()
        for monster in monsters:
            session.add(monster["blueprint"])
            for ability in monster["abilities"]:
                session.add(ability)
        print(f"  Added {len(monsters)} monsters with abilities")
        
        # Dungeons
        dungeons = create_dungeons(monsters)
        for dungeon in dungeons:
            session.add(dungeon["dungeon"])
            for seq in dungeon["sequence"]:
                session.add(seq)
        print(f"  Added {len(dungeons)} dungeons")
        
        # Achievements
        achievements = create_achievements()
        for achievement in achievements:
            session.add(achievement)
        print(f"  Added {len(achievements)} achievements")
        
        # Quests
        quests = create_quests()
        for quest in quests:
            session.add(quest)
        print(f"  Added {len(quests)} quests")
        
        await session.commit()
        print("Database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_database())
