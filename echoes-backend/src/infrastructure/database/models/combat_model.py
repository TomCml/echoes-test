"""
Echoes Backend - Combat SQLAlchemy Models
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.connection import Base
from src.domain.enums.types import CombatStatus, DamageType


class CombatSessionModel(Base):
    """Active or historical combat session."""
    
    __tablename__ = "combat_sessions"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    player_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    monster_blueprint_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("monster_blueprints.id", ondelete="CASCADE"),
        nullable=False,
    )
    monster_level: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[CombatStatus] = mapped_column(
        Enum(CombatStatus, name="combat_status", create_constraint=True),
        default=CombatStatus.PENDING,
    )
    turn_count: Mapped[int] = mapped_column(Integer, default=0)
    current_turn_entity: Mapped[str] = mapped_column(String(20), default="player")
    
    # Player state snapshot
    player_current_hp: Mapped[int] = mapped_column(Integer, default=0)
    player_max_hp: Mapped[int] = mapped_column(Integer, default=0)
    player_echo_current: Mapped[int] = mapped_column(Integer, default=0)
    player_echo_max: Mapped[int] = mapped_column(Integer, default=100)
    player_statuses: Mapped[dict] = mapped_column(JSONB, default=dict)
    player_gauges: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # Monster state snapshot
    monster_current_hp: Mapped[int] = mapped_column(Integer, default=0)
    monster_max_hp: Mapped[int] = mapped_column(Integer, default=0)
    monster_statuses: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    ended_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    player: Mapped["PlayerModel"] = relationship(
        "PlayerModel",
        back_populates="combat_sessions",
    )
    spell_cooldowns: Mapped[list["CombatSpellCooldownModel"]] = relationship(
        "CombatSpellCooldownModel",
        back_populates="combat_session",
    )
    logs: Mapped[list["CombatLogModel"]] = relationship(
        "CombatLogModel",
        back_populates="combat_session",
    )


class CombatSpellCooldownModel(Base):
    """Spell cooldown tracking during combat."""
    
    __tablename__ = "combat_spell_cooldowns"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    combat_session_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("combat_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    spell_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("spells.id", ondelete="CASCADE"),
        nullable=False,
    )
    remaining_turns: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    combat_session: Mapped["CombatSessionModel"] = relationship(
        "CombatSessionModel",
        back_populates="spell_cooldowns",
    )


class CombatLogModel(Base):
    """Combat action log entry."""
    
    __tablename__ = "combat_logs"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    combat_session_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("combat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    turn: Mapped[int] = mapped_column(Integer, nullable=False)
    actor: Mapped[str] = mapped_column(String(20), nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    spell_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    damage_dealt: Mapped[int] = mapped_column(Integer, default=0)
    damage_type: Mapped[DamageType] = mapped_column(
        Enum(DamageType, name="damage_type", create_constraint=True),
        nullable=True,
    )
    was_critical: Mapped[bool] = mapped_column(Boolean, default=False)
    echo_gained: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    
    # Relationships
    combat_session: Mapped["CombatSessionModel"] = relationship(
        "CombatSessionModel",
        back_populates="logs",
    )


class StatusDefinitionModel(Base):
    """Status effect definition."""
    
    __tablename__ = "status_definitions"
    
    code: Mapped[str] = mapped_column(String(50), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="")
    icon_key: Mapped[str] = mapped_column(String(100), default="")
    is_debuff: Mapped[bool] = mapped_column(Boolean, default=False)
    is_stackable: Mapped[bool] = mapped_column(Boolean, default=False)
    max_stacks: Mapped[int] = mapped_column(Integer, default=1)
    tick_trigger: Mapped[str] = mapped_column(String(30), default="ON_TURN_END")
    tick_effect: Mapped[dict] = mapped_column(JSONB, nullable=True)
