"""
Echoes Backend - Upgrade Item Use Case
"""
from dataclasses import dataclass
from typing import Optional, Tuple
from uuid import UUID

from src.application.interfaces.repositories import IItemRepository, IPlayerRepository


@dataclass
class UpgradeItemInput:
    """Input for upgrading an item."""
    player_id: UUID
    item_instance_id: UUID
    xp_amount: int


@dataclass
class UpgradeItemOutput:
    """Output from upgrading an item."""
    success: bool
    item_name: str
    new_level: int
    new_xp: int
    xp_to_next: int
    levels_gained: int


class UpgradeItemUseCase:
    """
    Use case for upgrading an item with XP.
    Items level up when they gain enough XP.
    """
    
    XP_PER_LEVEL_BASE = 100  # Base XP needed per level
    XP_PER_LEVEL_GROWTH = 1.2  # Multiplier per level
    MAX_ITEM_LEVEL = 100
    
    def __init__(
        self,
        item_repository: IItemRepository,
        player_repository: IPlayerRepository,
    ):
        self.item_repo = item_repository
        self.player_repo = player_repository
    
    async def execute(self, input_data: UpgradeItemInput) -> Tuple[Optional[UpgradeItemOutput], Optional[str]]:
        """
        Upgrade an item with XP.
        
        Returns:
            Tuple of (output, error_message)
        """
        if input_data.xp_amount <= 0:
            return None, "XP amount must be positive"
        
        # Get the item
        item = await self.item_repo.get_instance_by_id(input_data.item_instance_id)
        if not item:
            return None, "Item not found"
        
        # Check ownership
        if item.owner_id != input_data.player_id:
            return None, "You don't own this item"
        
        # Check max level
        if item.item_level >= self.MAX_ITEM_LEVEL:
            return None, "Item is already at max level"
        
        # Get item name
        bp = item.blueprint if hasattr(item, 'blueprint') else None
        item_name = bp.name if bp else "Unknown Item"
        
        # Add XP and process level ups
        old_level = item.item_level
        item.item_xp += input_data.xp_amount
        
        levels_gained = 0
        while item.item_xp >= item.item_xp_to_next_level and item.item_level < self.MAX_ITEM_LEVEL:
            item.item_xp -= item.item_xp_to_next_level
            item.item_level += 1
            levels_gained += 1
            
            # Calculate new XP requirement
            item.item_xp_to_next_level = int(
                self.XP_PER_LEVEL_BASE * (self.XP_PER_LEVEL_GROWTH ** item.item_level)
            )
        
        # Save changes (assuming repository has an update method or we use the existing session)
        # For now we'll just update the fields - the repo should handle persistence
        await self.item_repo.update_instance(item)
        
        return UpgradeItemOutput(
            success=True,
            item_name=item_name,
            new_level=item.item_level,
            new_xp=item.item_xp,
            xp_to_next=item.item_xp_to_next_level,
            levels_gained=levels_gained,
        ), None
