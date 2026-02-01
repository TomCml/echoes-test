from sqlalchemy import Column, Integer, String, Boolean, Float, JSON
from app.core.database import Base


class Monster(Base):
    __tablename__ = "monsters"

    monster_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)

    level = Column(Integer, nullable=False, default=1)
    is_boss = Column(Boolean, default=False)
    ai_behavior = Column(String(50), default="basic")

    # Stats de base
    hp_max = Column(Integer, nullable=False)
    attack_damage = Column(Integer, nullable=False)
    ability_power = Column(Integer, default=0)
    armor = Column(Integer, default=0)
    magic_resistance = Column(Integer, default=0)
    speed = Column(Integer, default=10)

    # Scaling par niveau
    scaling_hp = Column(Float, default=0.0)
    scaling_ad = Column(Float, default=0.0)
    scaling_armor = Column(Float, default=0.0)

    # Abilities : liste JSON
    # Ex: [{"name": "Morsure", "cooldown": 2, "effects": [{"opcode": "damage", ...}]}]
    abilities = Column(JSON, default=[])

    # Récompenses
    reward_xp = Column(Integer, nullable=False)
    reward_gold_min = Column(Integer, nullable=False, default=0)
    reward_gold_max = Column(Integer, nullable=False, default=0)

    sprite_key = Column(String(100), nullable=True)
