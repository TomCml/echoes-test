"""
Echoes Backend - Combat Repository
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infrastructure.database.models.combat_model import (
    CombatLogModel,
    CombatSessionModel,
    CombatSpellCooldownModel,
    StatusDefinitionModel,
)
from src.domain.enums.types import CombatStatus


class CombatRepository:
    """Repository for Combat data access."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # =========================================================================
    # Combat Sessions
    # =========================================================================
    
    async def get_session_by_id(
        self, session_id: UUID
    ) -> Optional[CombatSessionModel]:
        """Get a combat session by ID."""
        result = await self.session.execute(
            select(CombatSessionModel)
            .where(CombatSessionModel.id == session_id)
            .options(
                selectinload(CombatSessionModel.spell_cooldowns),
                selectinload(CombatSessionModel.logs),
            )
        )
        return result.scalar_one_or_none()
    
    async def get_active_session_for_player(
        self, player_id: UUID
    ) -> Optional[CombatSessionModel]:
        """Get the active combat session for a player."""
        active_statuses = [
            CombatStatus.PENDING,
            CombatStatus.IN_PROGRESS,
            CombatStatus.PLAYER_TURN,
            CombatStatus.MONSTER_TURN,
        ]
        
        result = await self.session.execute(
            select(CombatSessionModel)
            .where(
                CombatSessionModel.player_id == player_id,
                CombatSessionModel.status.in_(active_statuses),
            )
            .options(selectinload(CombatSessionModel.spell_cooldowns))
        )
        return result.scalar_one_or_none()
    
    async def create_session(
        self,
        player_id: UUID,
        monster_blueprint_id: UUID,
        monster_level: int,
        player_max_hp: int,
        monster_max_hp: int,
    ) -> CombatSessionModel:
        """Create a new combat session."""
        session = CombatSessionModel(
            player_id=player_id,
            monster_blueprint_id=monster_blueprint_id,
            monster_level=monster_level,
            player_current_hp=player_max_hp,
            player_max_hp=player_max_hp,
            monster_current_hp=monster_max_hp,
            monster_max_hp=monster_max_hp,
        )
        self.session.add(session)
        await self.session.flush()
        return session
    
    async def update_session(
        self, combat_session: CombatSessionModel
    ) -> CombatSessionModel:
        """Update a combat session."""
        await self.session.flush()
        return combat_session
    
    async def get_player_combat_history(
        self, player_id: UUID, limit: int = 20
    ) -> List[CombatSessionModel]:
        """Get combat history for a player."""
        result = await self.session.execute(
            select(CombatSessionModel)
            .where(CombatSessionModel.player_id == player_id)
            .order_by(CombatSessionModel.started_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    # =========================================================================
    # Cooldowns
    # =========================================================================
    
    async def set_spell_cooldown(
        self, session_id: UUID, spell_id: UUID, remaining_turns: int
    ) -> CombatSpellCooldownModel:
        """Set or update a spell cooldown."""
        # Check if exists
        result = await self.session.execute(
            select(CombatSpellCooldownModel)
            .where(
                CombatSpellCooldownModel.combat_session_id == session_id,
                CombatSpellCooldownModel.spell_id == spell_id,
            )
        )
        cooldown = result.scalar_one_or_none()
        
        if cooldown:
            cooldown.remaining_turns = remaining_turns
        else:
            cooldown = CombatSpellCooldownModel(
                combat_session_id=session_id,
                spell_id=spell_id,
                remaining_turns=remaining_turns,
            )
            self.session.add(cooldown)
        
        await self.session.flush()
        return cooldown
    
    async def tick_all_cooldowns(self, session_id: UUID) -> None:
        """Decrement all cooldowns for a session and remove expired ones."""
        result = await self.session.execute(
            select(CombatSpellCooldownModel)
            .where(CombatSpellCooldownModel.combat_session_id == session_id)
        )
        cooldowns = result.scalars().all()
        
        for cooldown in cooldowns:
            cooldown.remaining_turns -= 1
            if cooldown.remaining_turns <= 0:
                await self.session.delete(cooldown)
        
        await self.session.flush()
    
    # =========================================================================
    # Combat Logs
    # =========================================================================
    
    async def add_log(
        self,
        session_id: UUID,
        turn: int,
        actor: str,
        action_type: str,
        message: str,
        **kwargs,
    ) -> CombatLogModel:
        """Add a combat log entry."""
        log = CombatLogModel(
            combat_session_id=session_id,
            turn=turn,
            actor=actor,
            action_type=action_type,
            message=message,
            **kwargs,
        )
        self.session.add(log)
        await self.session.flush()
        return log
    
    async def get_session_logs(
        self, session_id: UUID, limit: int = 50
    ) -> List[CombatLogModel]:
        """Get logs for a combat session."""
        result = await self.session.execute(
            select(CombatLogModel)
            .where(CombatLogModel.combat_session_id == session_id)
            .order_by(CombatLogModel.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    # =========================================================================
    # Status Definitions
    # =========================================================================
    
    async def get_all_status_definitions(self) -> List[StatusDefinitionModel]:
        """Get all status definitions."""
        result = await self.session.execute(
            select(StatusDefinitionModel)
        )
        return list(result.scalars().all())
    
    async def get_status_definition(
        self, code: str
    ) -> Optional[StatusDefinitionModel]:
        """Get a status definition by code."""
        result = await self.session.execute(
            select(StatusDefinitionModel)
            .where(StatusDefinitionModel.code == code)
        )
        return result.scalar_one_or_none()
