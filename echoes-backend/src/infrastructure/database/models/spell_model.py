"""
Echoes Backend - Spell SQLAlchemy Model
"""
from uuid import uuid4

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.connection import Base
from src.domain.enums.types import SpellType


class SpellModel(Base):
    """Spell/ability attached to a weapon."""
    
    __tablename__ = "spells"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    weapon_blueprint_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("weapon_blueprints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), default="")
    spell_type: Mapped[SpellType] = mapped_column(
        Enum(SpellType, name="spell_type", create_constraint=True),
        nullable=False,
    )
    spell_order: Mapped[int] = mapped_column(Integer, default=1)  # 1-3 per weapon
    cooldown_turns: Mapped[int] = mapped_column(Integer, default=0)
    echo_cost: Mapped[int] = mapped_column(Integer, default=0)
    effects: Mapped[dict] = mapped_column(JSONB, default=list)
    
    # Relationships
    weapon_blueprint: Mapped["WeaponBlueprintModel"] = relationship(
        "WeaponBlueprintModel",
        back_populates="spells",
    )
