"""
Echoes Backend - Item SQLAlchemy Models
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.connection import Base
from src.domain.enums.types import DamageType, EquipmentSlot, ItemType, Rarity


class ItemBlueprintModel(Base):
    """Base blueprint for all items."""
    
    __tablename__ = "item_blueprints"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), default="")
    item_type: Mapped[ItemType] = mapped_column(
        Enum(ItemType, name="item_type", create_constraint=True),
        nullable=False,
    )
    rarity: Mapped[Rarity] = mapped_column(
        Enum(Rarity, name="rarity", create_constraint=True),
        nullable=False,
    )
    level_requirement: Mapped[int] = mapped_column(Integer, default=1)
    max_level: Mapped[int] = mapped_column(Integer, default=100)
    is_tradeable: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Base stats
    base_max_hp: Mapped[int] = mapped_column(Integer, default=0)
    base_ad: Mapped[int] = mapped_column(Integer, default=0)
    base_ap: Mapped[int] = mapped_column(Integer, default=0)
    base_armor: Mapped[int] = mapped_column(Integer, default=0)
    base_mr: Mapped[int] = mapped_column(Integer, default=0)
    base_speed: Mapped[int] = mapped_column(Integer, default=0)
    base_crit_chance: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Scaling per level
    scaling_hp_per_level: Mapped[float] = mapped_column(Float, default=0.0)
    scaling_ad_per_level: Mapped[float] = mapped_column(Float, default=0.0)
    scaling_ap_per_level: Mapped[float] = mapped_column(Float, default=0.0)
    scaling_armor_per_level: Mapped[float] = mapped_column(Float, default=0.0)
    scaling_mr_per_level: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Relationships
    weapon_data: Mapped["WeaponBlueprintModel"] = relationship(
        "WeaponBlueprintModel",
        back_populates="item_blueprint",
        uselist=False,
    )
    equipment_data: Mapped["EquipmentBlueprintModel"] = relationship(
        "EquipmentBlueprintModel",
        back_populates="item_blueprint",
        uselist=False,
    )
    consumable_data: Mapped["ConsumableBlueprintModel"] = relationship(
        "ConsumableBlueprintModel",
        back_populates="item_blueprint",
        uselist=False,
    )
    instances: Mapped[list["ItemInstanceModel"]] = relationship(
        "ItemInstanceModel",
        back_populates="blueprint",
    )


class WeaponBlueprintModel(Base):
    """Weapon-specific data (extends ItemBlueprint)."""
    
    __tablename__ = "weapon_blueprints"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("item_blueprints.id", ondelete="CASCADE"),
        primary_key=True,
    )
    damage_type: Mapped[DamageType] = mapped_column(
        Enum(DamageType, name="damage_type", create_constraint=True),
        default=DamageType.PHYSICAL,
    )
    
    # Relationships
    item_blueprint: Mapped["ItemBlueprintModel"] = relationship(
        "ItemBlueprintModel",
        back_populates="weapon_data",
    )
    spells: Mapped[list["SpellModel"]] = relationship(
        "SpellModel",
        back_populates="weapon_blueprint",
    )


class EquipmentBlueprintModel(Base):
    """Equipment-specific data (extends ItemBlueprint)."""
    
    __tablename__ = "equipment_blueprints"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("item_blueprints.id", ondelete="CASCADE"),
        primary_key=True,
    )
    slot: Mapped[EquipmentSlot] = mapped_column(
        Enum(EquipmentSlot, name="equipment_slot", create_constraint=True),
        nullable=False,
    )
    passive_effects: Mapped[dict] = mapped_column(JSONB, default=list)
    
    # Relationships
    item_blueprint: Mapped["ItemBlueprintModel"] = relationship(
        "ItemBlueprintModel",
        back_populates="equipment_data",
    )


class ConsumableBlueprintModel(Base):
    """Consumable-specific data (extends ItemBlueprint)."""
    
    __tablename__ = "consumable_blueprints"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("item_blueprints.id", ondelete="CASCADE"),
        primary_key=True,
    )
    effects: Mapped[dict] = mapped_column(JSONB, default=list)
    uses_per_combat: Mapped[int] = mapped_column(Integer, default=1)
    
    # Relationships
    item_blueprint: Mapped["ItemBlueprintModel"] = relationship(
        "ItemBlueprintModel",
        back_populates="consumable_data",
    )


class ItemInstanceModel(Base):
    """Player-owned item instance."""
    
    __tablename__ = "item_instances"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    blueprint_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("item_blueprints.id", ondelete="CASCADE"),
        nullable=False,
    )
    owner_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_level: Mapped[int] = mapped_column(Integer, default=1)
    item_xp: Mapped[int] = mapped_column(Integer, default=0)
    item_xp_to_next_level: Mapped[int] = mapped_column(Integer, default=100)
    is_equipped: Mapped[bool] = mapped_column(Boolean, default=False)
    equipped_slot: Mapped[EquipmentSlot] = mapped_column(
        Enum(EquipmentSlot, name="equipment_slot", create_constraint=True),
        nullable=True,
    )
    acquired_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    
    # Relationships
    blueprint: Mapped["ItemBlueprintModel"] = relationship(
        "ItemBlueprintModel",
        back_populates="instances",
    )
    owner: Mapped["PlayerModel"] = relationship(
        "PlayerModel",
        back_populates="item_instances",
    )
