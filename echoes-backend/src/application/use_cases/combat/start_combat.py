"""
Echoes Backend - Start Combat Use Case
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from src.application.interfaces.repositories import (
    IPlayerRepository,
    IMonsterRepository,
    ICombatRepository,
    IItemRepository,
)
from src.application.dto.combat_dto import CombatStateDTO, EntityStateDTO, PlayerStateDTO
from src.domain.entities.combat import (
    CombatSession,
    PlayerCombatEntity,
    MonsterCombatEntity,
)
from src.domain.value_objects.stats import StatsBlock
from src.domain.enums.types import CombatStatus


@dataclass
class StartCombatInput:
    """Input for starting combat."""
    player_id: UUID
    monster_blueprint_id: UUID
    monster_level: Optional[int] = None


@dataclass
class StartCombatOutput:
    """Output from starting combat."""
    session_id: UUID
    combat_state: CombatStateDTO


class StartCombatUseCase:
    """
    Use case for starting a new combat session.
    Creates the session, initializes player and monster entities.
    """
    
    def __init__(
        self,
        player_repository: IPlayerRepository,
        monster_repository: IMonsterRepository,
        combat_repository: ICombatRepository,
        item_repository: IItemRepository,
    ):
        self.player_repo = player_repository
        self.monster_repo = monster_repository
        self.combat_repo = combat_repository
        self.item_repo = item_repository
    
    async def execute(self, input_data: StartCombatInput) -> Tuple[Optional[StartCombatOutput], Optional[str]]:
        """
        Start a new combat session.
        
        Returns:
            Tuple of (output, error_message)
        """
        # Check for existing active combat
        existing = await self.combat_repo.get_active_session_for_player(input_data.player_id)
        if existing:
            return None, "You already have an active combat session"
        
        # Get player
        player = await self.player_repo.get_by_id(input_data.player_id)
        if not player:
            return None, "Player not found"
        
        # Get monster blueprint
        monster_bp = await self.monster_repo.get_blueprint_by_id(input_data.monster_blueprint_id)
        if not monster_bp:
            return None, "Monster not found"
        
        # Determine monster level
        monster_level = input_data.monster_level or monster_bp.base_level
        
        # Calculate player stats from equipment
        player_stats = await self._calculate_player_stats(input_data.player_id, player.level)
        player_max_hp = player_stats.max_hp
        
        # Calculate monster stats with scaling
        monster_stats = self._calculate_monster_stats(monster_bp, monster_level)
        monster_max_hp = monster_stats.max_hp
        
        # Create combat session
        session = await self.combat_repo.create_session(
            player_id=input_data.player_id,
            monster_blueprint_id=input_data.monster_blueprint_id,
            monster_level=monster_level,
            player_max_hp=player_max_hp,
            monster_max_hp=monster_max_hp,
        )
        
        if not session:
            return None, "Failed to create combat session"
        
        # Build combat state DTO
        combat_state = CombatStateDTO(
            session_id=session.id,
            status=CombatStatus.PLAYER_TURN,
            turn_count=1,
            current_turn="player",
            player=PlayerStateDTO(
                name=player.user.username if hasattr(player, 'user') else "Player",
                current_hp=player_max_hp,
                max_hp=player_max_hp,
                echo_current=0,
                echo_max=100,
                spell_cooldowns={},
                consumable_uses=1,
            ),
            monster=EntityStateDTO(
                name=monster_bp.name,
                current_hp=monster_max_hp,
                max_hp=monster_max_hp,
            ),
            logs=[f"Combat started! vs {monster_bp.name} (Lv.{monster_level})"],
        )
        
        return StartCombatOutput(
            session_id=session.id,
            combat_state=combat_state,
        ), None
    
    async def _calculate_player_stats(self, player_id: UUID, player_level: int) -> StatsBlock:
        """Calculate player stats from level and equipment."""
        # Base stats
        base = StatsBlock(
            max_hp=100 + (player_level * 10),
            ad=10 + (player_level * 2),
            ap=10 + (player_level * 2),
            armor=5 + player_level,
            mr=5 + player_level,
            speed=10,
            crit_chance=0.05,
            crit_damage=1.5,
        )
        
        # Add equipment stats
        inventory = await self.item_repo.get_player_inventory(player_id)
        for item in inventory:
            if item.is_equipped and hasattr(item, 'blueprint'):
                bp = item.blueprint
                item_level = item.item_level
                
                equip_stats = StatsBlock(
                    max_hp=int((getattr(bp, 'base_max_hp', 0) or 0) + 
                              (getattr(bp, 'scaling_hp_per_level', 0) or 0) * item_level),
                    ad=int((getattr(bp, 'base_ad', 0) or 0) + 
                          (getattr(bp, 'scaling_ad_per_level', 0) or 0) * item_level),
                    ap=int((getattr(bp, 'base_ap', 0) or 0) + 
                          (getattr(bp, 'scaling_ap_per_level', 0) or 0) * item_level),
                    armor=int((getattr(bp, 'base_armor', 0) or 0) + 
                             (getattr(bp, 'scaling_armor_per_level', 0) or 0) * item_level),
                    mr=int((getattr(bp, 'base_mr', 0) or 0) + 
                          (getattr(bp, 'scaling_mr_per_level', 0) or 0) * item_level),
                    speed=getattr(bp, 'base_speed', 0) or 0,
                    crit_chance=getattr(bp, 'base_crit_chance', 0) or 0,
                )
                base = base + equip_stats
        
        return base
    
    def _calculate_monster_stats(self, monster_bp, level: int) -> StatsBlock:
        """Calculate monster stats with level scaling."""
        return StatsBlock(
            max_hp=int((monster_bp.base_max_hp or 0) + 
                      (monster_bp.scaling_hp_per_level or 0) * level),
            ad=int((monster_bp.base_ad or 0) + 
                  (monster_bp.scaling_ad_per_level or 0) * level),
            ap=int((monster_bp.base_ap or 0) + 
                  (monster_bp.scaling_ap_per_level or 0) * level),
            armor=int((monster_bp.base_armor or 0) + 
                     (monster_bp.scaling_armor_per_level or 0) * level),
            mr=int((monster_bp.base_mr or 0) + 
                  (monster_bp.scaling_mr_per_level or 0) * level),
            speed=monster_bp.base_speed or 0,
        )
