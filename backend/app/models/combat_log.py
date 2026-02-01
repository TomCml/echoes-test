from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey, Text, func
from app.core.database import Base
from app.models.damage_types import DamageType


class CombatLog(Base):
    __tablename__ = "combat_logs"

    log_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("combat_sessions.session_id"), nullable=False)

    turn = Column(Integer, nullable=False)
    actor = Column(String(20), nullable=False)  # "player" ou "monster"
    action_type = Column(String(50), nullable=True)  # "spell", "basic_attack", "status_tick"
    spell_code = Column(String(100), nullable=True)
    damage_dealt = Column(Integer, nullable=True)
    damage_type = Column(Enum(DamageType, name="damage_type_enum"), nullable=True)
    was_critical = Column(Boolean, default=False)
    echo_gained = Column(Integer, default=0)
    message = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=func.now())
