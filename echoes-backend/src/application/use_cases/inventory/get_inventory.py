"""
Echoes Backend - Get Inventory Use Case
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple
from uuid import UUID

from src.application.interfaces.repositories import IItemRepository
from src.application.dto.player_dto import ItemInstanceDTO, SpellDTO


@dataclass
class GetInventoryOutput:
    """Output for inventory listing."""
    items: List[ItemInstanceDTO]
    total_count: int


class GetInventoryUseCase:
    """
    Use case for getting a player's inventory.
    """
    
    def __init__(self, item_repository: IItemRepository):
        self.item_repo = item_repository
    
    async def execute(self, player_id: UUID) -> Tuple[Optional[GetInventoryOutput], Optional[str]]:
        """
        Get the player's inventory.
        
        Returns:
            Tuple of (output, error_message)
        """
        items = await self.item_repo.get_player_inventory(player_id)
        
        item_dtos = []
        for item in items:
            bp = item.blueprint if hasattr(item, 'blueprint') else None
            
            # Get spells for weapons
            spells = []
            if bp and hasattr(bp, 'spells'):
                for spell in bp.spells:
                    spells.append(SpellDTO(
                        id=spell.id,
                        name=spell.name,
                        description=spell.description,
                        spell_type=spell.spell_type.value if hasattr(spell.spell_type, 'value') else str(spell.spell_type),
                        cooldown_turns=spell.cooldown_turns,
                        echo_cost=spell.echo_cost,
                        is_ultimate=spell.spell_type.value == "ULTIMATE" if hasattr(spell.spell_type, 'value') else False,
                    ))
            
            item_dtos.append(ItemInstanceDTO(
                id=item.id,
                blueprint_id=bp.id if bp else item.blueprint_id,
                name=bp.name if bp else "Unknown",
                description=bp.description if bp else "",
                item_type=bp.item_type.value if bp and hasattr(bp.item_type, 'value') else str(getattr(bp, 'item_type', 'UNKNOWN')),
                rarity=bp.rarity.value if bp and hasattr(bp.rarity, 'value') else str(getattr(bp, 'rarity', 'COMMON')),
                item_level=item.item_level,
                item_xp=item.item_xp,
                item_xp_to_next_level=item.item_xp_to_next_level,
                is_equipped=item.is_equipped,
                equipped_slot=item.equipped_slot.value if item.equipped_slot and hasattr(item.equipped_slot, 'value') else str(item.equipped_slot) if item.equipped_slot else None,
                spells=spells,
            ))
        
        return GetInventoryOutput(
            items=item_dtos,
            total_count=len(item_dtos),
        ), None
