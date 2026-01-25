"""
Echoes Backend - Player SQLAlchemy Model
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.connection import Base


class PlayerModel(Base):
    """Player game character."""
    
    __tablename__ = "players"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    level: Mapped[int] = mapped_column(Integer, default=1)
    current_xp: Mapped[int] = mapped_column(Integer, default=0)
    xp_to_next_level: Mapped[int] = mapped_column(Integer, default=100)
    gold: Mapped[int] = mapped_column(Integer, default=0)
    stat_points_available: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    
    # Relationships
    user: Mapped["UserModel"] = relationship(
        "UserModel",
        back_populates="player",
    )
    equipment_loadout: Mapped["PlayerEquipmentLoadoutModel"] = relationship(
        "PlayerEquipmentLoadoutModel",
        back_populates="player",
        uselist=False,
    )
    item_instances: Mapped[list["ItemInstanceModel"]] = relationship(
        "ItemInstanceModel",
        back_populates="owner",
    )
    combat_sessions: Mapped[list["CombatSessionModel"]] = relationship(
        "CombatSessionModel",
        back_populates="player",
    )


class PlayerEquipmentLoadoutModel(Base):
    """Player's equipped items."""
    
    __tablename__ = "player_equipment_loadout"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    player_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    weapon_primary_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("item_instances.id", ondelete="SET NULL"),
        nullable=True,
    )
    weapon_secondary_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("item_instances.id", ondelete="SET NULL"),
        nullable=True,
    )
    head_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("item_instances.id", ondelete="SET NULL"),
        nullable=True,
    )
    armor_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("item_instances.id", ondelete="SET NULL"),
        nullable=True,
    )
    artifact_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("item_instances.id", ondelete="SET NULL"),
        nullable=True,
    )
    blessing_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("item_instances.id", ondelete="SET NULL"),
        nullable=True,
    )
    consumable_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("item_instances.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Relationships
    player: Mapped["PlayerModel"] = relationship(
        "PlayerModel",
        back_populates="equipment_loadout",
    )
