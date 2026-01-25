"""
Echoes Backend - Players Endpoints
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_db
from src.infrastructure.database.repositories import (
    PlayerRepository,
    ItemRepository,
    UserRepository,
)
from src.application.use_cases.player.get_player_profile import GetPlayerProfileUseCase
from src.presentation.api.deps import get_current_user
from src.presentation.schemas.schemas import (
    PlayerProfileResponse,
    ErrorResponse,
)

router = APIRouter()


@router.get(
    "/me",
    response_model=PlayerProfileResponse,
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def get_my_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current player's profile."""
    user_id = UUID(current_user["user_id"])
    
    player_repo = PlayerRepository(db)
    item_repo = ItemRepository(db)
    
    # First get player ID from user
    player = await player_repo.get_by_user_id(user_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found. Please create a character first.",
        )
    
    use_case = GetPlayerProfileUseCase(
        player_repository=player_repo,
        item_repository=item_repo,
    )
    
    result, error = await use_case.execute(
        player_id=player.id,
        requesting_user_id=user_id,
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error,
        )
    
    return PlayerProfileResponse(
        id=result.id,
        username=result.username,
        level=result.level,
        current_xp=result.current_xp,
        xp_to_next_level=result.xp_to_next_level,
        xp_progress_percent=result.xp_progress_percent,
        gold=result.gold,
        stat_points_available=result.stat_points_available,
    )


@router.get(
    "/{player_id}",
    response_model=PlayerProfileResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_player_profile(
    player_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a player's public profile."""
    player_repo = PlayerRepository(db)
    item_repo = ItemRepository(db)
    
    use_case = GetPlayerProfileUseCase(
        player_repository=player_repo,
        item_repository=item_repo,
    )
    
    result, error = await use_case.execute(player_id=player_id)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error,
        )
    
    return PlayerProfileResponse(
        id=result.id,
        username=result.username,
        level=result.level,
        current_xp=result.current_xp,
        xp_to_next_level=result.xp_to_next_level,
        xp_progress_percent=result.xp_progress_percent,
        gold=result.gold,
        stat_points_available=result.stat_points_available,
    )


from pydantic import BaseModel
from typing import Optional

class UpdateProfileRequest(BaseModel):
    is_profile_public: Optional[bool] = None


@router.patch("/me")
async def update_my_profile(
    request: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current player's profile settings."""
    user_id = UUID(current_user["user_id"])
    
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Update fields if provided
    if request.is_profile_public is not None:
        user.is_profile_public = request.is_profile_public
    
    await user_repo.update(user)
    
    return {
        "message": "Profile updated successfully",
        "is_profile_public": user.is_profile_public,
    }
