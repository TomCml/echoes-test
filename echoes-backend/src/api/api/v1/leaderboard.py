"""
Echoes Backend - Leaderboard Endpoints
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_db
from src.infrastructure.database.repositories import (
    PlayerRepository,
    ProgressionRepository,
)
from src.presentation.api.deps import get_current_user
from src.presentation.schemas.schemas import (
    LeaderboardResponse,
    LeaderboardEntryResponse,
    PlayerRankResponse,
    ErrorResponse,
)
from src.domain.enums.types import LeaderboardType

router = APIRouter()


@router.get(
    "/{leaderboard_type}",
    response_model=LeaderboardResponse,
    responses={400: {"model": ErrorResponse}},
)
async def get_leaderboard(
    leaderboard_type: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Get top 100 of a leaderboard."""
    valid_types = ["GLOBAL_LEVEL", "ACHIEVEMENTS_COUNT", "BOSS_SPEEDRUN", "TOTAL_MONSTERS_KILLED"]
    
    if leaderboard_type.upper() not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid leaderboard type. Valid types: {valid_types}",
        )
    
    progression_repo = ProgressionRepository(db)
    
    entries = await progression_repo.get_leaderboard(LeaderboardType(leaderboard_type.upper()), limit=min(limit, 100))
    
    entry_responses = [
        LeaderboardEntryResponse(
            rank=i + 1,
            player_id=entry.player_id,
            username=entry.player.user.username if hasattr(entry, 'player') and hasattr(entry.player, 'user') else "Unknown",
            score=entry.score,
        )
        for i, entry in enumerate(entries)
    ]
    
    return LeaderboardResponse(
        leaderboard_type=leaderboard_type.upper(),
        entries=entry_responses,
        total_entries=len(entry_responses),
    )


@router.get(
    "/{leaderboard_type}/me",
    response_model=PlayerRankResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_my_rank(
    leaderboard_type: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current player's rank on a leaderboard."""
    valid_types = ["GLOBAL_LEVEL", "ACHIEVEMENTS_COUNT", "BOSS_SPEEDRUN", "TOTAL_MONSTERS_KILLED"]
    
    if leaderboard_type.upper() not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid leaderboard type. Valid types: {valid_types}",
        )
    
    user_id = UUID(current_user["user_id"])
    
    player_repo = PlayerRepository(db)
    progression_repo = ProgressionRepository(db)
    
    player = await player_repo.get_by_user_id(user_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found",
        )
    
    entry = await progression_repo.get_player_leaderboard_entry(player.id, LeaderboardType(leaderboard_type.upper()))
    
    if not entry:
        # Player not on leaderboard yet
        return PlayerRankResponse(
            leaderboard_type=leaderboard_type.upper(),
            rank=0,
            score=0,
            percentile=0.0,
        )
    
    # Calculate percentile
    total_entries = await progression_repo.get_leaderboard_total_count(LeaderboardType(leaderboard_type.upper()))
    percentile = ((total_entries - entry.rank) / total_entries * 100) if total_entries > 0 else 0
    
    return PlayerRankResponse(
        leaderboard_type=leaderboard_type.upper(),
        rank=entry.rank,
        score=entry.score,
        percentile=round(percentile, 1),
    )
