"""
Echoes Backend - Progression Repository
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infrastructure.database.models.progression_model import (
    AchievementModel,
    DungeonModel,
    LeaderboardEntryModel,
    PlayerAchievementModel,
    PlayerDungeonProgressModel,
    PlayerQuestModel,
    QuestModel,
)
from src.domain.enums.types import LeaderboardType


class ProgressionRepository:
    """Repository for Progression data access."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # =========================================================================
    # Achievements
    # =========================================================================
    
    async def get_all_achievements(self) -> List[AchievementModel]:
        """Get all achievements."""
        result = await self.session.execute(
            select(AchievementModel)
        )
        return list(result.scalars().all())
    
    async def get_player_achievements(
        self, player_id: UUID
    ) -> List[PlayerAchievementModel]:
        """Get all player achievement progress."""
        result = await self.session.execute(
            select(PlayerAchievementModel)
            .where(PlayerAchievementModel.player_id == player_id)
        )
        return list(result.scalars().all())
    
    async def update_achievement_progress(
        self, player_id: UUID, achievement_id: UUID, progress: int
    ) -> PlayerAchievementModel:
        """Update or create player achievement progress."""
        result = await self.session.execute(
            select(PlayerAchievementModel)
            .where(
                PlayerAchievementModel.player_id == player_id,
                PlayerAchievementModel.achievement_id == achievement_id,
            )
        )
        player_achievement = result.scalar_one_or_none()
        
        if player_achievement:
            player_achievement.progress = progress
        else:
            player_achievement = PlayerAchievementModel(
                player_id=player_id,
                achievement_id=achievement_id,
                progress=progress,
            )
            self.session.add(player_achievement)
        
        await self.session.flush()
        return player_achievement
    
    # =========================================================================
    # Quests
    # =========================================================================
    
    async def get_player_active_quests(
        self, player_id: UUID
    ) -> List[PlayerQuestModel]:
        """Get active quests for a player."""
        result = await self.session.execute(
            select(PlayerQuestModel)
            .where(
                PlayerQuestModel.player_id == player_id,
                PlayerQuestModel.is_completed == False,
            )
        )
        return list(result.scalars().all())
    
    async def get_quest_by_id(self, quest_id: UUID) -> Optional[QuestModel]:
        """Get a quest by ID."""
        result = await self.session.execute(
            select(QuestModel).where(QuestModel.id == quest_id)
        )
        return result.scalar_one_or_none()
    
    async def assign_quest(
        self, player_id: UUID, quest_id: UUID
    ) -> PlayerQuestModel:
        """Assign a quest to a player."""
        player_quest = PlayerQuestModel(
            player_id=player_id,
            quest_id=quest_id,
        )
        self.session.add(player_quest)
        await self.session.flush()
        return player_quest
    
    # =========================================================================
    # Dungeons
    # =========================================================================
    
    async def get_all_dungeons(self) -> List[DungeonModel]:
        """Get all dungeons."""
        result = await self.session.execute(
            select(DungeonModel)
            .options(selectinload(DungeonModel.monster_sequence))
        )
        return list(result.scalars().all())
    
    async def get_dungeon_by_id(self, dungeon_id: UUID) -> Optional[DungeonModel]:
        """Get a dungeon by ID."""
        result = await self.session.execute(
            select(DungeonModel)
            .where(DungeonModel.id == dungeon_id)
            .options(selectinload(DungeonModel.monster_sequence))
        )
        return result.scalar_one_or_none()
    
    async def get_player_dungeon_progress(
        self, player_id: UUID
    ) -> List[PlayerDungeonProgressModel]:
        """Get player's dungeon progress."""
        result = await self.session.execute(
            select(PlayerDungeonProgressModel)
            .where(PlayerDungeonProgressModel.player_id == player_id)
        )
        return list(result.scalars().all())
    
    async def get_player_dungeon_progress_single(
        self, player_id: UUID, dungeon_id: UUID
    ) -> Optional[PlayerDungeonProgressModel]:
        """Get player's progress for a specific dungeon."""
        result = await self.session.execute(
            select(PlayerDungeonProgressModel)
            .where(
                PlayerDungeonProgressModel.player_id == player_id,
                PlayerDungeonProgressModel.dungeon_id == dungeon_id,
            )
        )
        return result.scalar_one_or_none()
    
    # =========================================================================
    # Leaderboards
    # =========================================================================
    
    async def get_leaderboard(
        self, leaderboard_type: LeaderboardType, limit: int = 100
    ) -> List[LeaderboardEntryModel]:
        """Get top entries for a leaderboard."""
        result = await self.session.execute(
            select(LeaderboardEntryModel)
            .where(LeaderboardEntryModel.leaderboard_type == leaderboard_type)
            .order_by(LeaderboardEntryModel.rank)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_player_leaderboard_entry(
        self, player_id: UUID, leaderboard_type: LeaderboardType
    ) -> Optional[LeaderboardEntryModel]:
        """Get a player's leaderboard entry."""
        result = await self.session.execute(
            select(LeaderboardEntryModel)
            .where(
                LeaderboardEntryModel.player_id == player_id,
                LeaderboardEntryModel.leaderboard_type == leaderboard_type,
            )
        )
        return result.scalar_one_or_none()
    
    async def update_leaderboard_entry(
        self, player_id: UUID, leaderboard_type: LeaderboardType, score: int
    ) -> LeaderboardEntryModel:
        """Update or create a leaderboard entry."""
        entry = await self.get_player_leaderboard_entry(player_id, leaderboard_type)
        
        if entry:
            entry.score = score
        else:
            entry = LeaderboardEntryModel(
                player_id=player_id,
                leaderboard_type=leaderboard_type,
                score=score,
            )
            self.session.add(entry)
        
        await self.session.flush()
        return entry
    
    async def get_leaderboard_total_count(self, leaderboard_type: LeaderboardType) -> int:
        """Get total number of entries in a leaderboard."""
        from sqlalchemy import func
        
        result = await self.session.execute(
            select(func.count(LeaderboardEntryModel.id))
            .where(LeaderboardEntryModel.leaderboard_type == leaderboard_type)
        )
        return result.scalar() or 0
