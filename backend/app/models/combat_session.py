"""
CombatSession — Modèle SQLAlchemy pour la persistance des combats.

Tables :
  - combat_sessions   : état complet du combat entre les requêtes
  - combat_logs        : journal structuré (1 row par event)
  - combat_spell_cds   : cooldowns des sorts (1 row par sort en CD)
"""
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text,
    ForeignKey, Enum, JSON, func, CheckConstraint
)
from app.core.database import Base
from app.engine.domain import CombatStatus


class CombatSession(Base):
    __tablename__ = "combat_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("players.player_id"), nullable=False, index=True)
    monster_id = Column(Integer, ForeignKey("monsters.monster_id"), nullable=False)
    monster_level = Column(Integer, nullable=False)

    status = Column(
        Enum(CombatStatus, name="combat_status_enum", create_constraint=True),
        nullable=False,
        default=CombatStatus.PENDING
    )
    turn_count = Column(Integer, default=0)
    current_turn_entity = Column(String(20))  # "player" or "monster"

    # ─── Player combat state ─────────────────────────
    player_current_hp = Column(Integer, nullable=False)
    player_max_hp = Column(Integer, nullable=False)
    player_echo_current = Column(Integer, default=0)
    player_echo_max = Column(Integer, default=100)
    player_statuses = Column(JSON, default=dict)   # {code: {remaining, stacks}}
    player_gauges = Column(JSON, default=dict)      # {gauge_name: value}
    player_cds = Column(JSON, default=dict)         # {spell_code: remaining}

    # ─── Monster combat state ────────────────────────
    monster_current_hp = Column(Integer, nullable=False)
    monster_max_hp = Column(Integer, nullable=False)
    monster_statuses = Column(JSON, default=dict)
    monster_cds = Column(JSON, default=dict)

    # ─── Timestamps ──────────────────────────────────
    started_at = Column(DateTime(timezone=True), default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)


class CombatLog(Base):
    __tablename__ = "combat_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    combat_session_id = Column(Integer, ForeignKey("combat_sessions.id"), nullable=False, index=True)
    turn = Column(Integer, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now())


class CombatSpellCooldown(Base):
    __tablename__ = "combat_spell_cooldowns"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    combat_session_id = Column(Integer, ForeignKey("combat_sessions.id"), nullable=False)
    spell_code = Column(String(100), nullable=False)
    entity_id = Column(String(50), nullable=False)   # "player" or "monster_X"
    remaining_turns = Column(Integer, nullable=False)
