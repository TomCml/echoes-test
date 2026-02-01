from sqlalchemy import Column, Integer, DateTime, String, Boolean, BigInteger, Float, Text, ForeignKey, func   
from app.core.database import Base

class Player(Base):
    __tablename__ = "players"

    player_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    twitch_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    level = Column(Integer, default=1)
    gold = Column(Integer, default=0)
    
    echo_current = Column(Integer, default=0)
    echo_max = Column(Integer, default=100)

    experience = Column(BigInteger, default=0)
    health_points = Column(Integer, default=500)
    attack_damage = Column(Integer, default=50 )
    ability_power = Column(Integer, default=15)
    armor = Column(Integer, default=40)
    magic_resistance = Column(Integer, default=30)
    attack_speed = Column(Integer, default=0)
    ability_haste = Column(Integer, default=0)
    crit_chance = Column(Integer, default=5)
    dodge = Column(Integer, default=1)
    speed = Column(Integer, default=300)
    life_steal = Column(Integer, default=0)
    spell_vamp = Column(Integer, default=0)
    is_watching = Column(Boolean, default=False)
    start_watch = Column(DateTime, nullable=True)
    title_id = Column(Integer, ForeignKey("titles.title_id"))
    player_shop_id = Column(Integer, ForeignKey("player_shop.player_shop_id"))
    shop_level = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), default=func.now())
    last_login = Column(DateTime(timezone=True), default=func.now())