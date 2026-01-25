"""
Echoes Backend - Monster SQLAlchemy Models
"""
from uuid import uuid4

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.connection import Base


class LootTableModel(Base):
    """Loot table definition."""
    
    __tablename__ = "loot_tables"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Relationships
    entries: Mapped[list["LootTableEntryModel"]] = relationship(
        "LootTableEntryModel",
        back_populates="loot_table",
    )
    monsters: Mapped[list["MonsterBlueprintModel"]] = relationship(
        "MonsterBlueprintModel",
        back_populates="loot_table",
    )


class LootTableEntryModel(Base):
    """Entry in a loot table."""
    
    __tablename__ = "loot_table_entries"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    loot_table_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("loot_tables.id", ondelete="CASCADE"),
        nullable=False,
    )
    item_blueprint_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("item_blueprints.id", ondelete="CASCADE"),
        nullable=False,
    )
    weight: Mapped[int] = mapped_column(Integer, default=100)
    min_quantity: Mapped[int] = mapped_column(Integer, default=1)
    max_quantity: Mapped[int] = mapped_column(Integer, default=1)
    min_player_level: Mapped[int] = mapped_column(Integer, default=1)
    
    # Relationships
    loot_table: Mapped["LootTableModel"] = relationship(
        "LootTableModel",
        back_populates="entries",
    )


class MonsterBlueprintModel(Base):
    """Monster type definition."""
    
    __tablename__ = "monster_blueprints"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), default="")
    base_level: Mapped[int] = mapped_column(Integer, default=1)
    ai_behavior: Mapped[str] = mapped_column(String(50), default="basic")
    loot_table_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("loot_tables.id", ondelete="SET NULL"),
        nullable=True,
    )
    xp_reward: Mapped[int] = mapped_column(Integer, default=0)
    gold_reward_min: Mapped[int] = mapped_column(Integer, default=0)
    gold_reward_max: Mapped[int] = mapped_column(Integer, default=0)
    is_boss: Mapped[bool] = mapped_column(Boolean, default=False)
    sprite_key: Mapped[str] = mapped_column(String(100), default="")
    
    # Base stats
    base_max_hp: Mapped[int] = mapped_column(Integer, default=100)
    base_ad: Mapped[int] = mapped_column(Integer, default=10)
    base_ap: Mapped[int] = mapped_column(Integer, default=10)
    base_armor: Mapped[int] = mapped_column(Integer, default=5)
    base_mr: Mapped[int] = mapped_column(Integer, default=5)
    base_speed: Mapped[int] = mapped_column(Integer, default=10)
    
    # Scaling per level
    scaling_hp_per_level: Mapped[float] = mapped_column(Float, default=10.0)
    scaling_ad_per_level: Mapped[float] = mapped_column(Float, default=1.0)
    scaling_ap_per_level: Mapped[float] = mapped_column(Float, default=1.0)
    scaling_armor_per_level: Mapped[float] = mapped_column(Float, default=0.5)
    scaling_mr_per_level: Mapped[float] = mapped_column(Float, default=0.5)
    
    # Relationships
    loot_table: Mapped["LootTableModel"] = relationship(
        "LootTableModel",
        back_populates="monsters",
    )
    abilities: Mapped[list["MonsterAbilityModel"]] = relationship(
        "MonsterAbilityModel",
        back_populates="monster_blueprint",
    )


class MonsterAbilityModel(Base):
    """Monster ability definition."""
    
    __tablename__ = "monster_abilities"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    monster_blueprint_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("monster_blueprints.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    cooldown: Mapped[int] = mapped_column(Integer, default=0)
    priority: Mapped[int] = mapped_column(Integer, default=1)
    condition_expr: Mapped[str] = mapped_column(String(200), nullable=True)
    effects: Mapped[dict] = mapped_column(JSONB, default=list)
    
    # Relationships
    monster_blueprint: Mapped["MonsterBlueprintModel"] = relationship(
        "MonsterBlueprintModel",
        back_populates="abilities",
    )
