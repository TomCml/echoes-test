from sqlalchemy import Column, Integer, String, DateTime, Enum, JSON, ForeignKey, func
from app.core.database import Base
from app.models.enums import CombatStatus


class CombatSession(Base):
    __tablename__ = "combat_sessions"

    session_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("players.player_id"), nullable=False)
    monster_id = Column(Integer, ForeignKey("monsters.monster_id"), nullable=True)
    target_player_id = Column(Integer, ForeignKey("players.player_id"), nullable=True)

    status = Column(Enum(CombatStatus, name="combat_status_enum"), default=CombatStatus.PENDING)
    turn_count = Column(Integer, default=0)

    # État joueur
    player_current_hp = Column(Integer, nullable=False)
    player_max_hp = Column(Integer, nullable=False)
    player_echo_current = Column(Integer, default=0)
    player_statuses = Column(JSON, default={})
    player_gauges = Column(JSON, default={})

    # État adversaire
    opponent_current_hp = Column(Integer, nullable=False)
    opponent_max_hp = Column(Integer, nullable=False)
    opponent_statuses = Column(JSON, default={})

    started_at = Column(DateTime(timezone=True), default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
