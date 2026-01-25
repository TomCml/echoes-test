"""
Echoes Backend - Monsters Endpoints
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_db
from src.infrastructure.database.repositories import MonsterRepository
from src.presentation.schemas.schemas import (
    MonsterBlueprintResponse,
    MonsterListResponse,
    ErrorResponse,
)

router = APIRouter()


@router.get(
    "/",
    response_model=MonsterListResponse,
)
async def list_monsters(
    db: AsyncSession = Depends(get_db),
):
    """List all monster blueprints."""
    monster_repo = MonsterRepository(db)
    
    monsters = await monster_repo.get_all_blueprints()
    
    monster_responses = [
        MonsterBlueprintResponse(
            id=m.id,
            name=m.name,
            description=m.description or "",
            base_level=m.base_level,
            is_boss=m.is_boss,
            sprite_key=m.sprite_key or "",
            base_stats={
                "max_hp": m.base_max_hp,
                "ad": m.base_ad,
                "ap": m.base_ap,
                "armor": m.base_armor,
                "mr": m.base_mr,
                "speed": m.base_speed,
            },
        )
        for m in monsters
    ]
    
    return MonsterListResponse(
        monsters=monster_responses,
        total_count=len(monster_responses),
    )


@router.get(
    "/{monster_id}",
    response_model=MonsterBlueprintResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_monster(
    monster_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific monster blueprint."""
    monster_repo = MonsterRepository(db)
    
    monster = await monster_repo.get_blueprint_by_id(monster_id)
    if not monster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monster not found",
        )
    
    return MonsterBlueprintResponse(
        id=monster.id,
        name=monster.name,
        description=monster.description or "",
        base_level=monster.base_level,
        is_boss=monster.is_boss,
        sprite_key=monster.sprite_key or "",
        base_stats={
            "max_hp": monster.base_max_hp,
            "ad": monster.base_ad,
            "ap": monster.base_ap,
            "armor": monster.base_armor,
            "mr": monster.base_mr,
            "speed": monster.base_speed,
        },
    )
