"""
Echoes Backend - Item Repository
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infrastructure.database.models.item_model import (
    ItemBlueprintModel,
    ItemInstanceModel,
    WeaponBlueprintModel,
)
from src.infrastructure.database.models.spell_model import SpellModel
from src.domain.enums.types import EquipmentSlot


class ItemRepository:
    """Repository for Item data access."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # =========================================================================
    # Blueprints
    # =========================================================================
    
    async def get_blueprint_by_id(self, blueprint_id: UUID) -> Optional[ItemBlueprintModel]:
        """Get an item blueprint by ID."""
        result = await self.session.execute(
            select(ItemBlueprintModel)
            .where(ItemBlueprintModel.id == blueprint_id)
            .options(
                selectinload(ItemBlueprintModel.weapon_data),
                selectinload(ItemBlueprintModel.equipment_data),
                selectinload(ItemBlueprintModel.consumable_data),
            )
        )
        return result.scalar_one_or_none()
    
    async def get_weapon_blueprint_with_spells(
        self, blueprint_id: UUID
    ) -> Optional[WeaponBlueprintModel]:
        """Get a weapon blueprint with its spells."""
        result = await self.session.execute(
            select(WeaponBlueprintModel)
            .where(WeaponBlueprintModel.id == blueprint_id)
            .options(selectinload(WeaponBlueprintModel.spells))
        )
        return result.scalar_one_or_none()
    
    async def get_all_blueprints(self) -> List[ItemBlueprintModel]:
        """Get all item blueprints."""
        result = await self.session.execute(
            select(ItemBlueprintModel)
        )
        return list(result.scalars().all())
    
    # =========================================================================
    # Instances
    # =========================================================================
    
    async def get_instance_by_id(self, instance_id: UUID) -> Optional[ItemInstanceModel]:
        """Get an item instance by ID."""
        result = await self.session.execute(
            select(ItemInstanceModel)
            .where(ItemInstanceModel.id == instance_id)
            .options(selectinload(ItemInstanceModel.blueprint))
        )
        return result.scalar_one_or_none()
    
    async def get_player_inventory(self, player_id: UUID) -> List[ItemInstanceModel]:
        """Get all items owned by a player."""
        result = await self.session.execute(
            select(ItemInstanceModel)
            .where(ItemInstanceModel.owner_id == player_id)
            .options(selectinload(ItemInstanceModel.blueprint))
        )
        return list(result.scalars().all())
    
    async def get_player_equipped_items(self, player_id: UUID) -> List[ItemInstanceModel]:
        """Get all equipped items for a player."""
        result = await self.session.execute(
            select(ItemInstanceModel)
            .where(
                ItemInstanceModel.owner_id == player_id,
                ItemInstanceModel.is_equipped == True,
            )
            .options(selectinload(ItemInstanceModel.blueprint))
        )
        return list(result.scalars().all())
    
    async def create_instance(
        self, blueprint_id: UUID, owner_id: UUID
    ) -> ItemInstanceModel:
        """Create a new item instance for a player."""
        instance = ItemInstanceModel(
            blueprint_id=blueprint_id,
            owner_id=owner_id,
        )
        self.session.add(instance)
        await self.session.flush()
        return instance
    
    async def equip_item(
        self, instance_id: UUID, slot: EquipmentSlot
    ) -> ItemInstanceModel:
        """Equip an item in a slot."""
        instance = await self.get_instance_by_id(instance_id)
        if not instance:
            raise ValueError(f"Item {instance_id} not found")
        
        instance.is_equipped = True
        instance.equipped_slot = slot
        await self.session.flush()
        return instance
    
    async def unequip_item(self, instance_id: UUID) -> ItemInstanceModel:
        """Unequip an item."""
        instance = await self.get_instance_by_id(instance_id)
        if not instance:
            raise ValueError(f"Item {instance_id} not found")
        
        instance.is_equipped = False
        instance.equipped_slot = None
        await self.session.flush()
        return instance
    
    async def add_item_xp(
        self, instance_id: UUID, amount: int
    ) -> tuple[int, int]:
        """
        Add XP to an item.
        Returns (new_level, levels_gained).
        """
        instance = await self.get_instance_by_id(instance_id)
        if not instance:
            raise ValueError(f"Item {instance_id} not found")
        
        instance.item_xp += amount
        levels_gained = 0
        max_level = 100  # Should come from blueprint
        
        while (
            instance.item_xp >= instance.item_xp_to_next_level
            and instance.item_level < max_level
        ):
            instance.item_xp -= instance.item_xp_to_next_level
            instance.item_level += 1
            levels_gained += 1
            instance.item_xp_to_next_level = int(50 * (instance.item_level ** 1.3))
        
        await self.session.flush()
        return instance.item_level, levels_gained
    
    async def update_instance(self, item_instance: ItemInstanceModel) -> None:
        """Update an item instance."""
        self.session.add(item_instance)
        await self.session.flush()
    
    # =========================================================================
    # Spells
    # =========================================================================
    
    async def get_spells_for_weapon(self, weapon_blueprint_id: UUID) -> List[SpellModel]:
        """Get all spells for a weapon."""
        result = await self.session.execute(
            select(SpellModel)
            .where(SpellModel.weapon_blueprint_id == weapon_blueprint_id)
            .order_by(SpellModel.spell_order)
        )
        return list(result.scalars().all())
    
    async def get_spell_by_id(self, spell_id: UUID) -> Optional[SpellModel]:
        """Get a spell by ID."""
        result = await self.session.execute(
            select(SpellModel).where(SpellModel.id == spell_id)
        )
        return result.scalar_one_or_none()
