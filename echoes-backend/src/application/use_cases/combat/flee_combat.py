"""
Echoes Backend - Flee Combat Use Case
"""
from dataclasses import dataclass
from typing import Optional, Tuple
from uuid import UUID

from src.application.interfaces.repositories import (
    IPlayerRepository,
    IMonsterRepository,
    ICombatRepository,
)
from src.application.dto.combat_dto import CombatActionResultDTO
from src.domain.enums.types import CombatStatus


@dataclass
class FleeCombatInput:
    """Input for fleeing combat."""
    player_id: UUID
    session_id: UUID


class FleeCombatUseCase:
    """
    Use case for fleeing from combat.
    Flee chance is based on speed difference.
    """
    
    def __init__(
        self,
        player_repository: IPlayerRepository,
        monster_repository: IMonsterRepository,
        combat_repository: ICombatRepository,
    ):
        self.player_repo = player_repository
        self.monster_repo = monster_repository
        self.combat_repo = combat_repository
    
    async def execute(self, input_data: FleeCombatInput) -> Tuple[Optional[CombatActionResultDTO], Optional[str]]:
        """
        Attempt to flee from combat.
        
        Returns:
            Tuple of (result, error_message)
        """
        # Get combat session
        session = await self.combat_repo.get_session_by_id(input_data.session_id)
        if not session:
            return None, "Combat session not found"
        
        # Verify ownership
        if session.player_id != input_data.player_id:
            return None, "This is not your combat session"
        
        # Check session is active
        if session.status not in [CombatStatus.PLAYER_TURN, CombatStatus.IN_PROGRESS]:
            return None, "Cannot flee from this combat state"
        
        # For now, we'll use a simple random flee with the combat engine
        # Import here to avoid circular imports
        from src.application.use_cases.combat.execute_action import ExecuteActionUseCase
        
        # Build battle to use flee logic
        player = await self.player_repo.get_by_id(input_data.player_id)
        monster_bp = await self.monster_repo.get_blueprint_by_id(session.monster_blueprint_id)
        
        # Simple flee calculation based on speed
        import random
        player_speed = 10 + player.level  # Base + level
        monster_speed = monster_bp.base_speed + session.monster_level
        
        speed_diff = player_speed - monster_speed
        flee_chance = 0.5 + (speed_diff * 0.02)  # +2% per speed point
        flee_chance = max(0.1, min(0.9, flee_chance))  # 10% to 90%
        
        if random.random() < flee_chance:
            # Flee successful
            session.status = CombatStatus.ABANDONED
            await self.combat_repo.update_session(session)
            
            return CombatActionResultDTO(
                success=True,
                message="You escaped from combat!",
                combat_ended=True,
                result="fled",
            ), None
        else:
            # Flee failed - monster gets a free attack
            # For simplicity, we'll just damage the player
            damage = int(monster_bp.base_ad * 0.5)  # Half damage attack
            session.player_current_hp = max(0, session.player_current_hp - damage)
            
            # Check if player died
            if session.player_current_hp <= 0:
                session.status = CombatStatus.DEFEAT
                await self.combat_repo.update_session(session)
                
                return CombatActionResultDTO(
                    success=False,
                    message=f"Failed to flee! {monster_bp.name} attacks for {damage} damage. You have been defeated!",
                    combat_ended=True,
                    result="defeat",
                ), None
            
            await self.combat_repo.update_session(session)
            
            return CombatActionResultDTO(
                success=False,
                message=f"Failed to flee! {monster_bp.name} attacks for {damage} damage.",
                combat_ended=False,
            ), None
