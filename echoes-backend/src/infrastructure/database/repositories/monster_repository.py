"""
Echoes Backend - Monster Repository
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infrastructure.database.models.monster_model import (
    LootTableModel,
    MonsterBlueprintModel,
)


class MonsterRepository:
    """Repository for Monster data access."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_blueprint_by_id(
        self, blueprint_id: UUID
    ) -> Optional[MonsterBlueprintModel]:
        """Get a monster blueprint by ID with abilities."""
        result = await self.session.execute(
            select(MonsterBlueprintModel)
            .where(MonsterBlueprintModel.id == blueprint_id)
            .options(selectinload(MonsterBlueprintModel.abilities))
        )
        return result.scalar_one_or_none()
    
    async def get_all_blueprints(self) -> List[MonsterBlueprintModel]:
        """Get all monster blueprints."""
        result = await self.session.execute(
            select(MonsterBlueprintModel)
            .options(selectinload(MonsterBlueprintModel.abilities))
        )
        return list(result.scalars().all())
    
    async def get_blueprints_by_level_range(
        self, min_level: int, max_level: int
    ) -> List[MonsterBlueprintModel]:
        """Get monster blueprints within a level range."""
        result = await self.session.execute(
            select(MonsterBlueprintModel)
            .where(
                MonsterBlueprintModel.base_level >= min_level,
                MonsterBlueprintModel.base_level <= max_level,
            )
            .options(selectinload(MonsterBlueprintModel.abilities))
        )
        return list(result.scalars().all())
    
    async def get_bosses(self) -> List[MonsterBlueprintModel]:
        """Get all boss monster blueprints."""
        result = await self.session.execute(
            select(MonsterBlueprintModel)
            .where(MonsterBlueprintModel.is_boss == True)
            .options(selectinload(MonsterBlueprintModel.abilities))
        )
        return list(result.scalars().all())
    
    async def get_loot_table(self, loot_table_id: UUID) -> Optional[LootTableModel]:
        """Get a loot table with entries."""
        result = await self.session.execute(
            select(LootTableModel)
            .where(LootTableModel.id == loot_table_id)
            .options(selectinload(LootTableModel.entries))
        )
        return result.scalar_one_or_none()
