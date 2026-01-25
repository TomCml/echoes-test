"""
Echoes Backend - Equip Item Use Case
"""
from dataclasses import dataclass
from typing import Optional, Tuple
from uuid import UUID

from src.application.interfaces.repositories import IPlayerRepository, IItemRepository
from src.domain.enums.types import EquipmentSlot, ItemType


@dataclass
class EquipItemInput:
    """Input for equipping an item."""
    player_id: UUID
    item_instance_id: UUID
    slot: str  # Target slot


@dataclass
class EquipItemOutput:
    """Output from equipping an item."""
    success: bool
    item_name: str
    slot: str
    unequipped_item_name: Optional[str] = None


class EquipItemUseCase:
    """
    Use case for equipping an item to a slot.
    Handles validation and swapping if slot is occupied.
    """
    
    def __init__(
        self,
        player_repository: IPlayerRepository,
        item_repository: IItemRepository,
    ):
        self.player_repo = player_repository
        self.item_repo = item_repository
    
    async def execute(self, input_data: EquipItemInput) -> Tuple[Optional[EquipItemOutput], Optional[str]]:
        """
        Equip an item to a slot.
        
        Returns:
            Tuple of (output, error_message)
        """
        # Validate slot
        try:
            target_slot = EquipmentSlot(input_data.slot.upper())
        except ValueError:
            return None, f"Invalid equipment slot: {input_data.slot}"
        
        # Get the item instance
        item = await self.item_repo.get_instance_by_id(input_data.item_instance_id)
        if not item:
            return None, "Item not found"
        
        # Check ownership
        if item.owner_id != input_data.player_id:
            return None, "You don't own this item"
        
        # Validate item can go in this slot
        if not self._is_valid_slot_for_item(item, target_slot):
            return None, f"This item cannot be equipped in slot {target_slot.value}"
        
        # Check level requirement
        player = await self.player_repo.get_by_id(input_data.player_id)
        if not player:
            return None, "Player not found"
        
        blueprint = item.blueprint if hasattr(item, 'blueprint') else None
        if blueprint and hasattr(blueprint, 'level_requirement'):
            if player.level < blueprint.level_requirement:
                return None, f"You need to be level {blueprint.level_requirement} to equip this item"
        
        # Get item name
        item_name = blueprint.name if blueprint else "Unknown Item"
        
        # Check if slot is occupied and unequip if needed
        unequipped_name = None
        inventory = await self.item_repo.get_player_inventory(input_data.player_id)
        for inv_item in inventory:
            if inv_item.is_equipped and inv_item.equipped_slot == target_slot:
                await self.item_repo.unequip_item(inv_item.id)
                inv_blueprint = inv_item.blueprint if hasattr(inv_item, 'blueprint') else None
                unequipped_name = inv_blueprint.name if inv_blueprint else "Unknown Item"
                break
        
        # Equip the new item
        await self.item_repo.equip_item(input_data.item_instance_id, target_slot)
        
        return EquipItemOutput(
            success=True,
            item_name=item_name,
            slot=target_slot.value,
            unequipped_item_name=unequipped_name,
        ), None
    
    def _is_valid_slot_for_item(self, item, target_slot: EquipmentSlot) -> bool:
        """Check if the item can be equipped in the target slot."""
        blueprint = item.blueprint if hasattr(item, 'blueprint') else None
        if not blueprint:
            return False
        
        item_type = blueprint.item_type if hasattr(blueprint, 'item_type') else None
        if not item_type:
            return False
        
        # Map item types to valid slots
        slot_map = {
            ItemType.WEAPON: [EquipmentSlot.WEAPON_PRIMARY, EquipmentSlot.WEAPON_SECONDARY],
            ItemType.HEAD: [EquipmentSlot.HEAD],
            ItemType.ARMOR: [EquipmentSlot.ARMOR],
            ItemType.ARTIFACT: [EquipmentSlot.ARTIFACT],
            ItemType.BLESSING: [EquipmentSlot.BLESSING],
            ItemType.CONSUMABLE: [EquipmentSlot.CONSUMABLE],
        }
        
        valid_slots = slot_map.get(item_type, [])
        return target_slot in valid_slots
