"""
Seed Script — Crée des données de test depuis le Bestiaire Echoes.

Données extraites de : Echoes/monsters/Echoes _ part 2 - Bestiaire Résumé.csv
Stats sont à level 1 (valeur min des ranges "X a Y").
Les scaling per level sont calculés depuis les ranges du CSV.

Usage:
    cd backend
    python -m scripts.seed_combat
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.player import Player
from app.models.monster import Monster
# Import all models so SQLAlchemy resolves FKs
from app.models import player_shop, title, inventory, quest  # noqa: F401


# ─── Monster Data (Bestiaire Résumé) ────────────────────
# Format: base stats at level 1, scaling derived from "min a max" over 99 levels
# category = pallier (1=basic, 2=elite, 3=boss, 4=raid)

MONSTERS = [
    # ── Catégorie 1 (Lv 1-100) ───────────────────────
    {
        "name": "Carapateur",
        "level": 1,
        "hp_max": 1,
        "attack_damage": 0,
        "reward_xp": 10,
        "reward_gold": 5,
        "metadata_props": {
            "category": 1,
            "base_ap": 0, "base_armor": 0, "base_mr": 0,
            "base_speed": 0, "crit": 5,
            "scaling_hp_per_level": 0, "scaling_ad_per_level": 0,
        },
    },
    {
        "name": "Lycans",
        "level": 1,
        "hp_max": 500,
        "attack_damage": 60,
        "reward_xp": 30,
        "reward_gold": 12,
        "metadata_props": {
            "category": 1,
            "base_ap": 0, "base_armor": 20, "base_mr": 20,
            "base_speed": 400, "crit": 50,
            # (2500-500)/99 ≈ 20.2 HP/lvl, (300-60)/99 ≈ 2.4 AD/lvl
            "scaling_hp_per_level": 20.2, "scaling_ad_per_level": 2.4,
        },
    },
    {
        "name": "Corbins",
        "level": 1,
        "hp_max": 600,
        "attack_damage": 30,
        "reward_xp": 35,
        "reward_gold": 14,
        "metadata_props": {
            "category": 1,
            "base_ap": 0, "base_armor": 5, "base_mr": 0,
            "base_speed": 350, "crit": 5,
            # (3000-600)/99 ≈ 24.2, (150-30)/99 ≈ 1.2
            "scaling_hp_per_level": 24.2, "scaling_ad_per_level": 1.2,
        },
    },
    {
        "name": "Krugs",
        "level": 1,
        "hp_max": 900,
        "attack_damage": 80,
        "reward_xp": 45,
        "reward_gold": 18,
        "metadata_props": {
            "category": 1,
            "base_ap": 0, "base_armor": 50, "base_mr": 50,
            "base_speed": 295, "crit": 5,
            # (4500-900)/99 ≈ 36.4, (400-80)/99 ≈ 3.2
            "scaling_hp_per_level": 36.4, "scaling_ad_per_level": 3.2,
        },
    },

    # ── Catégorie 2 (Lv 1-100) ───────────────────────
    {
        "name": "Roncier Rouge",
        "level": 5,
        "hp_max": 1300,
        "attack_damage": 160,
        "reward_xp": 80,
        "reward_gold": 30,
        "metadata_props": {
            "category": 2,
            "base_ap": 0, "base_armor": 50, "base_mr": 50,
            "base_speed": 375, "crit": 5,
            # (6500-1300)/99 ≈ 52.5, (800-160)/99 ≈ 6.5
            "scaling_hp_per_level": 52.5, "scaling_ad_per_level": 6.5,
        },
    },
    {
        "name": "Sentinelle Bleu",
        "level": 5,
        "hp_max": 1400,
        "attack_damage": 60,
        "reward_xp": 85,
        "reward_gold": 32,
        "metadata_props": {
            "category": 2,
            "base_ap": 160, "base_armor": 75, "base_mr": 75,
            "base_speed": 330, "crit": 5,
            # (7000-1400)/99 ≈ 56.6, (300-60)/99 ≈ 2.4, AP: (800-160)/99 ≈ 6.5
            "scaling_hp_per_level": 56.6, "scaling_ad_per_level": 2.4,
        },
    },
    {
        "name": "Dragon des Océans",
        "level": 10,
        "hp_max": 1600,
        "attack_damage": 120,
        "reward_xp": 120,
        "reward_gold": 50,
        "metadata_props": {
            "category": 2,
            "base_ap": 100, "base_armor": 50, "base_mr": 50,
            "base_speed": 375, "crit": 5,
            # (8000-1600)/99 ≈ 64.6, (600-120)/99 ≈ 4.8
            "scaling_hp_per_level": 64.6, "scaling_ad_per_level": 4.8,
        },
    },
    {
        "name": "Dragon Infernal",
        "level": 10,
        "hp_max": 2000,
        "attack_damage": 60,
        "reward_xp": 140,
        "reward_gold": 55,
        "metadata_props": {
            "category": 2,
            "base_ap": 120, "base_armor": 0, "base_mr": 0,
            "base_speed": 360, "crit": 5,
            # (10000-2000)/99 ≈ 80.8, (300-60)/99 ≈ 2.4
            "scaling_hp_per_level": 80.8, "scaling_ad_per_level": 2.4,
        },
    },
    {
        "name": "Héraut de la Faille",
        "level": 15,
        "hp_max": 4000,
        "attack_damage": 100,
        "reward_xp": 200,
        "reward_gold": 80,
        "metadata_props": {
            "category": 2,
            "base_ap": 0, "base_armor": 50, "base_mr": 50,
            "base_speed": 331, "crit": 5,
            # (20000-4000)/99 ≈ 161.6, (500-100)/99 ≈ 4.0
            "scaling_hp_per_level": 161.6, "scaling_ad_per_level": 4.0,
        },
    },

    # ── Catégorie 3 — Boss (Lv 20-100) ───────────────
    {
        "name": "Baron Nashor",
        "level": 20,
        "hp_max": 2000,
        "attack_damage": 80,
        "reward_xp": 350,
        "reward_gold": 150,
        "metadata_props": {
            "category": 3, "is_boss": True,
            "base_ap": 80, "base_armor": 25, "base_mr": 25,
            "base_speed": 350, "crit": 5,
            # (10000-2000)/80 ≈ 100, (400-80)/80 ≈ 4.0
            "scaling_hp_per_level": 100.0, "scaling_ad_per_level": 4.0,
        },
    },
    {
        "name": "Mordekaiser",
        "level": 20,
        "hp_max": 2000,
        "attack_damage": 80,
        "reward_xp": 400,
        "reward_gold": 180,
        "metadata_props": {
            "category": 3, "is_boss": True,
            "base_ap": 160, "base_armor": 25, "base_mr": 25,
            "base_speed": 350, "crit": 5,
            # (10000-2000)/80 ≈ 100, (400-80)/80 ≈ 4.0
            "scaling_hp_per_level": 100.0, "scaling_ad_per_level": 4.0,
        },
    },

    # ── Catégorie 4 — Raid (Lv 20-100) ───────────────
    {
        "name": "Kindred",
        "level": 20,
        "hp_max": 1800,
        "attack_damage": 100,
        "reward_xp": 500,
        "reward_gold": 250,
        "metadata_props": {
            "category": 4, "is_boss": True,
            "base_ap": 0, "base_armor": 80, "base_mr": 80,
            "base_speed": 450, "crit": 25,
            # (9000-1800)/80 ≈ 90, (250-100)/80 ≈ 1.9
            "scaling_hp_per_level": 90.0, "scaling_ad_per_level": 1.9,
        },
    },
    {
        "name": "Ornn",
        "level": 20,
        "hp_max": 2000,
        "attack_damage": 60,
        "reward_xp": 600,
        "reward_gold": 300,
        "metadata_props": {
            "category": 4, "is_boss": True,
            "base_ap": 120, "base_armor": 150, "base_mr": 150,
            "base_speed": 340, "crit": 5,
            # (10000-2000)/80 ≈ 100, (300-60)/80 ≈ 3.0
            "scaling_hp_per_level": 100.0, "scaling_ad_per_level": 3.0,
        },
    },
]


TEST_PLAYER = {
    "twitch_id": 123456789,
    "username": "TestHero",
    "level": 10,
    "gold": 500,
    "health_points": 800,
    "attack_damage": 120,
    "ability_power": 30,
    "armor": 60,
    "magic_resistance": 40,
    "speed": 300,
    "crit_chance": 15,
    "echo_current": 0,
    "echo_max": 100,
}


def seed():
    db = SessionLocal()
    try:
        # ─── Player ──────────────────────────────────
        player = db.query(Player).filter(Player.player_id == 1).first()
        if not player:
            player = Player(**TEST_PLAYER)
            db.add(player)
            db.commit()
            db.refresh(player)
            print(f"✅ Player created: #{player.player_id} '{player.username}'")
        else:
            print(f"ℹ️  Player exists: #{player.player_id} '{player.username}'")

        # ─── Monsters ────────────────────────────────
        created = 0
        for m_data in MONSTERS:
            existing = db.query(Monster).filter(Monster.name == m_data["name"]).first()
            if not existing:
                monster = Monster(**m_data)
                db.add(monster)
                db.commit()
                db.refresh(monster)
                cat = m_data["metadata_props"].get("category", "?")
                print(f"  ✅ [{cat}] #{monster.monster_id} {monster.name:<25} "
                      f"Lv{monster.level:>3}  HP:{monster.hp_max:>5}  AD:{monster.attack_damage:>4}")
                created += 1
            else:
                print(f"  ℹ️  exists: #{existing.monster_id} {existing.name}")

        # ─── Summary ─────────────────────────────────
        total = db.query(Monster).count()
        print(f"\n🎮 Seed terminé ! {created} créés, {total} monstres total en DB.\n")

        # Commandes de test
        easy = db.query(Monster).filter(Monster.name == "Lycans").first()
        if easy:
            print(f"Test facile  → POST /battle/start?player_id={player.player_id}"
                  f"&monster_id={easy.monster_id}&monster_level=1")
        hard = db.query(Monster).filter(Monster.name == "Baron Nashor").first()
        if hard:
            print(f"Test boss    → POST /battle/start?player_id={player.player_id}"
                  f"&monster_id={hard.monster_id}&monster_level=20")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
