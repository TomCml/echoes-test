from sqlalchemy import Column, Integer, String, JSON
from core.database import Base

class Monster(Base):
    __tablename__ = "monsters"

    monster_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    
    level = Column(Integer, nullable=False)
    hp_max = Column(Integer, nullable=False)
    attack_damage = Column(Integer, nullable=False)
    
    reward_xp = Column(Integer, nullable=False)
    reward_gold = Column(Integer, nullable=False)
    
    metadata_props = Column(JSON, nullable=True)
