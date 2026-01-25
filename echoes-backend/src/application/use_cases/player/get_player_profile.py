"""
Echoes Backend - Get Player Profile Use Case
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from src.application.interfaces.repositories import IPlayerRepository, IItemRepository
from src.application.dto.player_dto import PlayerProfileDTO, PlayerStatsDTO, EquipmentLoadoutDTO


@dataclass
class GetPlayerProfileOutput:
    """Output for player profile."""
    id: UUID
    username: str
    level: int
    current_xp: int
    xp_to_next_level: int
    xp_progress_percent: float
    gold: int
    stat_points_available: int
    stats: Dict[str, Any]
    equipment: Dict[str, Any]
    spells: List[Dict[str, Any]]


class GetPlayerProfileUseCase:
    """
    Use case for getting a player's full profile.
    Includes stats calculated from equipment and available spells.
    """
    
    def __init__(
        self,
        player_repository: IPlayerRepository,
        item_repository: IItemRepository,
    ):
        self.player_repo = player_repository
        self.item_repo = item_repository
    
    async def execute(
        self,
        player_id: UUID,
        requesting_user_id: Optional[UUID] = None,
    ) -> Tuple[Optional[GetPlayerProfileOutput], Optional[str]]:
        """
        Get a player's profile.
        
        Args:
            player_id: The player to fetch
            requesting_user_id: The user making the request (for privacy checks)
            
        Returns:
            Tuple of (output, error_message)
        """
        player = await self.player_repo.get_by_id(player_id)
        if not player:
            return None, "Player not found"
        
        # Calculate XP progress percentage
        xp_progress = (player.current_xp / player.xp_to_next_level * 100) if player.xp_to_next_level > 0 else 0
        
        # Get equipped items
        inventory = await self.item_repo.get_player_inventory(player_id)
        equipped_items = [item for item in inventory if item.is_equipped]
        
        # Calculate total stats from equipment
        stats = self._calculate_stats(player.level, equipped_items)
        
        # Build equipment dict
        equipment = {}
        for item in equipped_items:
            if item.equipped_slot:
                equipment[item.equipped_slot.value if hasattr(item.equipped_slot, 'value') else item.equipped_slot] = {
                    "id": str(item.id),
                    "name": item.blueprint.name if hasattr(item, 'blueprint') else "Unknown",
                    "item_level": item.item_level,
                }
        
        # Collect spells from weapons
        spells = []
        for item in equipped_items:
            if hasattr(item, 'blueprint') and hasattr(item.blueprint, 'spells'):
                for spell in item.blueprint.spells:
                    spells.append({
                        "id": str(spell.id),
                        "name": spell.name,
                        "spell_type": spell.spell_type.value if hasattr(spell.spell_type, 'value') else spell.spell_type,
                        "cooldown_turns": spell.cooldown_turns,
                        "echo_cost": spell.echo_cost,
                    })
        
        return GetPlayerProfileOutput(
            id=player.id,
            username=player.user.username if hasattr(player, 'user') else "Unknown",
            level=player.level,
            current_xp=player.current_xp,
            xp_to_next_level=player.xp_to_next_level,
            xp_progress_percent=round(xp_progress, 1),
            gold=player.gold,
            stat_points_available=player.stat_points_available,
            stats=stats,
            equipment=equipment,
            spells=spells,
        ), None
    
    def _calculate_stats(self, player_level: int, equipped_items: list) -> Dict[str, Any]:
        """Calculate total stats from player level and equipment."""
        # Base stats (could come from a config or player entity)
        stats = {
            "max_hp": 100 + (player_level * 10),
            "ad": 10 + (player_level * 2),
            "ap": 10 + (player_level * 2),
            "armor": 5 + (player_level * 1),
            "mr": 5 + (player_level * 1),
            "speed": 10,
            "crit_chance": 0.05,
            "crit_damage": 1.5,
        }
        
        # Add stats from equipment
        for item in equipped_items:
            if hasattr(item, 'blueprint'):
                bp = item.blueprint
                item_level = item.item_level
                
                # Add base stats
                stats["max_hp"] += getattr(bp, 'base_max_hp', 0) or 0
                stats["ad"] += getattr(bp, 'base_ad', 0) or 0
                stats["ap"] += getattr(bp, 'base_ap', 0) or 0
                stats["armor"] += getattr(bp, 'base_armor', 0) or 0
                stats["mr"] += getattr(bp, 'base_mr', 0) or 0
                stats["speed"] += getattr(bp, 'base_speed', 0) or 0
                stats["crit_chance"] += getattr(bp, 'base_crit_chance', 0) or 0
                
                # Add scaled stats based on item level
                stats["max_hp"] += int((getattr(bp, 'scaling_hp_per_level', 0) or 0) * item_level)
                stats["ad"] += int((getattr(bp, 'scaling_ad_per_level', 0) or 0) * item_level)
                stats["ap"] += int((getattr(bp, 'scaling_ap_per_level', 0) or 0) * item_level)
                stats["armor"] += int((getattr(bp, 'scaling_armor_per_level', 0) or 0) * item_level)
                stats["mr"] += int((getattr(bp, 'scaling_mr_per_level', 0) or 0) * item_level)
        
        return stats
