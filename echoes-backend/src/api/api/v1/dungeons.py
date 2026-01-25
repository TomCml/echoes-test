"""
Echoes Backend - Dungeons Endpoints
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_db
from src.infrastructure.database.repositories import (
    PlayerRepository,
    ProgressionRepository,
)
from src.presentation.api.deps import get_current_user, get_current_user_optional
from src.presentation.schemas.schemas import (
    DungeonResponse,
    DungeonListResponse,
    ErrorResponse,
)

router = APIRouter()


@router.get(
    "/",
    response_model=DungeonListResponse,
)
async def list_dungeons(
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """List all available dungeons."""
    progression_repo = ProgressionRepository(db)
    
    dungeons = await progression_repo.get_all_dungeons()
    
    # Get player progress if authenticated
    player_progress = {}
    if current_user:
        user_id = UUID(current_user["user_id"])
        player_repo = PlayerRepository(db)
        player = await player_repo.get_by_user_id(user_id)
        
        if player:
            progress_list = await progression_repo.get_player_dungeon_progress(player.id)
            player_progress = {p.dungeon_id: p for p in progress_list}
    
    dungeon_responses = []
    for dungeon in dungeons:
        progress = player_progress.get(dungeon.id)
        
        dungeon_responses.append(DungeonResponse(
            id=dungeon.id,
            name=dungeon.name,
            description=dungeon.description,
            level_requirement=dungeon.level_requirement,
            recommended_level=dungeon.recommended_level,
            is_unlocked=progress.is_unlocked if progress else False,
            best_clear_time_ms=progress.best_clear_time_ms if progress else None,
            clear_count=progress.clear_count if progress else 0,
        ))
    
    return DungeonListResponse(dungeons=dungeon_responses)


@router.get(
    "/{dungeon_id}",
    response_model=DungeonResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_dungeon(
    dungeon_id: UUID,
    current_user: dict = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific dungeon."""
    progression_repo = ProgressionRepository(db)
    
    dungeon = await progression_repo.get_dungeon_by_id(dungeon_id)
    if not dungeon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dungeon not found",
        )
    
    # Get player progress if authenticated
    is_unlocked = False
    best_time = None
    clear_count = 0
    
    if current_user:
        user_id = UUID(current_user["user_id"])
        player_repo = PlayerRepository(db)
        player = await player_repo.get_by_user_id(user_id)
        
        if player:
            progress = await progression_repo.get_player_dungeon_progress_single(player.id, dungeon_id)
            if progress:
                is_unlocked = progress.is_unlocked
                best_time = progress.best_clear_time_ms
                clear_count = progress.clear_count
    
    return DungeonResponse(
        id=dungeon.id,
        name=dungeon.name,
        description=dungeon.description,
        level_requirement=dungeon.level_requirement,
        recommended_level=dungeon.recommended_level,
        is_unlocked=is_unlocked,
        best_clear_time_ms=best_time,
        clear_count=clear_count,
    )


@router.post(
    "/{dungeon_id}/start",
    responses={400: {"model": ErrorResponse}},
)
async def start_dungeon(
    dungeon_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Start a dungeon run.
    Checks requirements and starts combat with first monster.
    """
    user_id = UUID(current_user["user_id"])
    
    # Initialize repositories
    player_repo = PlayerRepository(db)
    progression_repo = ProgressionRepository(db)
    
    # Get player
    player = await player_repo.get_by_user_id(user_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found",
        )
    
    # Get dungeon
    dungeon = await progression_repo.get_dungeon_by_id(dungeon_id)
    if not dungeon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dungeon not found",
        )
    
    # Check level requirement
    if player.level < dungeon.level_requirement:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"You need to be level {dungeon.level_requirement} to enter this dungeon (current: {player.level})",
        )
    
    # Check if dungeon is unlocked (or auto-unlock first dungeon)
    progress = await progression_repo.get_player_dungeon_progress_single(player.id, dungeon_id)
    if not progress:
        # First time - check if this is the first dungeon or if previous dungeon is cleared
        # For POC, auto-unlock all dungeons meeting level req
        pass
    
    # Get first monster in sequence
    if not dungeon.monster_sequence or len(dungeon.monster_sequence) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dungeon has no monsters configured",
        )
    
    first_monster = dungeon.monster_sequence[0]
    
    # Start combat using the combat use case
    from src.infrastructure.database.repositories import MonsterRepository, CombatRepository, ItemRepository
    from src.application.use_cases.combat.start_combat import StartCombatUseCase, StartCombatInput
    
    monster_repo = MonsterRepository(db)
    combat_repo = CombatRepository(db)
    item_repo = ItemRepository(db)
    
    combat_use_case = StartCombatUseCase(
        player_repository=player_repo,
        monster_repository=monster_repo,
        combat_repository=combat_repo,
        item_repository=item_repo,
    )
    
    result, error = await combat_use_case.execute(StartCombatInput(
        player_id=player.id,
        monster_blueprint_id=first_monster.monster_blueprint_id,
        monster_level=first_monster.monster_level or dungeon.recommended_level,
    ))
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    return {
        "message": f"Dungeon '{dungeon.name}' started!",
        "dungeon_id": str(dungeon_id),
        "dungeon_name": dungeon.name,
        "combat_session_id": str(result.session_id),
        "monster_count": len(dungeon.monster_sequence),
        "current_monster": 1,
    }
