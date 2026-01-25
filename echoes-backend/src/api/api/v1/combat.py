"""
Echoes Backend - Combat Endpoints
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_db
from src.infrastructure.database.repositories import (
    PlayerRepository,
    MonsterRepository,
    CombatRepository,
    ItemRepository,
)
from src.application.use_cases.combat.start_combat import StartCombatUseCase, StartCombatInput
from src.application.use_cases.combat.execute_action import ExecuteActionUseCase, ExecuteActionInput
from src.application.use_cases.combat.flee_combat import FleeCombatUseCase, FleeCombatInput
from src.presentation.api.deps import get_current_user
from src.presentation.schemas.schemas import (
    StartCombatRequest,
    CombatActionRequest,
    CombatStateResponse,
    CombatResultResponse,
    CombatRewardResponse,
    PlayerCombatStateResponse,
    EntityStateResponse,
    ErrorResponse,
)

router = APIRouter()


@router.post(
    "/start",
    response_model=CombatResultResponse,
    responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}},
)
async def start_combat(
    request: StartCombatRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a new combat session against a monster."""
    user_id = UUID(current_user["user_id"])
    
    player_repo = PlayerRepository(db)
    monster_repo = MonsterRepository(db)
    combat_repo = CombatRepository(db)
    item_repo = ItemRepository(db)
    
    # Get player ID
    player = await player_repo.get_by_user_id(user_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found",
        )
    
    use_case = StartCombatUseCase(
        player_repository=player_repo,
        monster_repository=monster_repo,
        combat_repository=combat_repo,
        item_repository=item_repo,
    )
    
    result, error = await use_case.execute(StartCombatInput(
        player_id=player.id,
        monster_blueprint_id=request.monster_blueprint_id,
        monster_level=request.monster_level,
    ))
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    return CombatResultResponse(
        success=True,
        message="Combat started!",
        combat_state=_convert_state(result.combat_state),
        combat_ended=False,
    )


@router.get(
    "/current",
    response_model=CombatStateResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_current_combat(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current combat session state."""
    user_id = UUID(current_user["user_id"])
    
    player_repo = PlayerRepository(db)
    combat_repo = CombatRepository(db)
    
    player = await player_repo.get_by_user_id(user_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found",
        )
    
    session = await combat_repo.get_active_session_for_player(player.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active combat session",
        )
    
    # Get monster info
    monster_bp = await MonsterRepository(db).get_blueprint_by_id(session.monster_blueprint_id)
    
    return CombatStateResponse(
        session_id=session.id,
        status=session.status.value,
        turn_count=session.turn_count,
        current_turn=session.current_turn_entity,
        player=PlayerCombatStateResponse(
            name=player.user.username if hasattr(player, 'user') else "Player",
            current_hp=session.player_current_hp,
            max_hp=session.player_max_hp,
            hp_percent=session.player_current_hp / session.player_max_hp * 100 if session.player_max_hp > 0 else 0,
            echo_current=session.player_echo_current,
            echo_max=session.player_echo_max,
        ),
        monster=EntityStateResponse(
            name=monster_bp.name if monster_bp else "Monster",
            current_hp=session.monster_current_hp,
            max_hp=session.monster_max_hp,
            hp_percent=session.monster_current_hp / session.monster_max_hp * 100 if session.monster_max_hp > 0 else 0,
        ),
        available_actions=["basic_attack", "spell", "consumable", "flee"],
    )


@router.post(
    "/action",
    response_model=CombatResultResponse,
    responses={400: {"model": ErrorResponse}},
)
async def execute_action(
    request: CombatActionRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Execute a combat action (spell, basic attack, consumable)."""
    user_id = UUID(current_user["user_id"])
    
    player_repo = PlayerRepository(db)
    monster_repo = MonsterRepository(db)
    combat_repo = CombatRepository(db)
    item_repo = ItemRepository(db)
    
    player = await player_repo.get_by_user_id(user_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found",
        )
    
    session = await combat_repo.get_active_session_for_player(player.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active combat session",
        )
    
    use_case = ExecuteActionUseCase(
        player_repository=player_repo,
        monster_repository=monster_repo,
        combat_repository=combat_repo,
        item_repository=item_repo,
    )
    
    result, error = await use_case.execute(ExecuteActionInput(
        player_id=player.id,
        session_id=session.id,
        action_type=request.action_type,
        spell_id=request.spell_id,
    ))
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    response = CombatResultResponse(
        success=result.success,
        message=result.message,
        combat_state=_convert_state(result.combat_state) if result.combat_state else None,
        combat_ended=result.combat_ended,
        result=result.result,
    )
    
    return response


@router.post(
    "/flee",
    response_model=CombatResultResponse,
    responses={400: {"model": ErrorResponse}},
)
async def flee_combat(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Attempt to flee from combat."""
    user_id = UUID(current_user["user_id"])
    
    player_repo = PlayerRepository(db)
    monster_repo = MonsterRepository(db)
    combat_repo = CombatRepository(db)
    
    player = await player_repo.get_by_user_id(user_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found",
        )
    
    session = await combat_repo.get_active_session_for_player(player.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active combat session",
        )
    
    use_case = FleeCombatUseCase(
        player_repository=player_repo,
        monster_repository=monster_repo,
        combat_repository=combat_repo,
    )
    
    result, error = await use_case.execute(FleeCombatInput(
        player_id=player.id,
        session_id=session.id,
    ))
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    return CombatResultResponse(
        success=result.success,
        message=result.message,
        combat_ended=result.combat_ended,
        result=result.result,
    )


def _convert_state(dto) -> CombatStateResponse:
    """Convert DTO to response schema."""
    if not dto:
        return None
    
    return CombatStateResponse(
        session_id=dto.session_id,
        status=dto.status.value if hasattr(dto.status, 'value') else str(dto.status),
        turn_count=dto.turn_count,
        current_turn=dto.current_turn,
        player=PlayerCombatStateResponse(
            name=dto.player.name,
            current_hp=dto.player.current_hp,
            max_hp=dto.player.max_hp,
            hp_percent=dto.player.current_hp / dto.player.max_hp * 100 if dto.player.max_hp > 0 else 0,
            echo_current=dto.player.echo_current,
            echo_max=dto.player.echo_max,
            spell_cooldowns={str(k): v for k, v in dto.player.spell_cooldowns.items()},
            consumable_uses=dto.player.consumable_uses,
            statuses=dto.player.statuses,
            shield=dto.player.shield,
        ),
        monster=EntityStateResponse(
            name=dto.monster.name,
            current_hp=dto.monster.current_hp,
            max_hp=dto.monster.max_hp,
            hp_percent=dto.monster.current_hp / dto.monster.max_hp * 100 if dto.monster.max_hp > 0 else 0,
            statuses=dto.monster.statuses,
        ),
        available_actions=["basic_attack", "spell", "consumable", "flee"],
        logs=dto.logs,
    )
