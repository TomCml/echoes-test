from sqlalchemy import Column, Integer, String, ForeignKey, Enum, JSON, Float
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.damage_types import DamageType

class Weapon(Base):
    __tablename__ = "weapons"

    weapon_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    
    bonus_ad = Column(Integer, default=0)
    bonus_ap = Column(Integer, default=0)
    bonus_speed = Column(Integer, default=0)
    
    spells = relationship("Spell", back_populates="weapon")

class Spell(Base):
    __tablename__ = "spells"

    spell_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    
    weapon_id = Column(Integer, ForeignKey("weapons.weapon_id"), nullable=True)
    weapon = relationship("Weapon", back_populates="spells")

    damage_type = Column(Enum(DamageType), nullable=False)
    mana_cost = Column(Integer, default=0)
    echo_cost = Column(Integer, default=0) 
    cooldown = Column(Integer, default=0)
    
    # Effets stockés en JSON
    # Ex: [{"opcode": "damage", "params": {...}}]
    effects = Column(JSON, nullable=False)

