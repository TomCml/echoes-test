"""
Echoes Backend - Inventory Endpoints
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_db
from src.infrastructure.database.repositories import (
    PlayerRepository,
    ItemRepository,
)
from src.application.use_cases.inventory.get_inventory import GetInventoryUseCase
from src.application.use_cases.inventory.upgrade_item import UpgradeItemUseCase, UpgradeItemInput
from src.application.use_cases.player.equip_item import EquipItemUseCase, EquipItemInput
from src.presentation.api.deps import get_current_user
from src.presentation.schemas.schemas import (
    InventoryResponse,
    ItemInstanceResponse,
    EquipItemRequest,
    UpgradeItemRequest,
    MessageResponse,
    ErrorResponse,
)

router = APIRouter()


@router.get(
    "/",
    response_model=InventoryResponse,
    responses={401: {"model": ErrorResponse}},
)
async def get_inventory(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current player's inventory."""
    user_id = UUID(current_user["user_id"])
    
    player_repo = PlayerRepository(db)
    item_repo = ItemRepository(db)
    
    player = await player_repo.get_by_user_id(user_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found",
        )
    
    use_case = GetInventoryUseCase(item_repository=item_repo)
    result, error = await use_case.execute(player.id)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    items = [
        ItemInstanceResponse(
            id=item.id,
            blueprint_id=item.blueprint_id,
            name=item.name,
            description=item.description,
            item_type=item.item_type,
            rarity=item.rarity,
            item_level=item.item_level,
            item_xp=item.item_xp,
            item_xp_to_next_level=item.item_xp_to_next_level,
            is_equipped=item.is_equipped,
            equipped_slot=item.equipped_slot,
            stats={},  # Stats could be calculated here if needed
            spells=[{"id": str(s.id), "name": s.name} for s in item.spells],
        )
        for item in result.items
    ]
    
    return InventoryResponse(
        items=items,
        total_count=result.total_count,
    )


@router.post(
    "/equip",
    response_model=MessageResponse,
    responses={400: {"model": ErrorResponse}},
)
async def equip_item(
    request: EquipItemRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Equip an item from inventory."""
    user_id = UUID(current_user["user_id"])
    
    player_repo = PlayerRepository(db)
    item_repo = ItemRepository(db)
    
    player = await player_repo.get_by_user_id(user_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found",
        )
    
    use_case = EquipItemUseCase(
        player_repository=player_repo,
        item_repository=item_repo,
    )
    
    result, error = await use_case.execute(EquipItemInput(
        player_id=player.id,
        item_instance_id=request.item_instance_id,
        slot=request.slot,
    ))
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    message = f"Equipped {result.item_name} to {result.slot}"
    if result.unequipped_item_name:
        message += f" (unequipped {result.unequipped_item_name})"
    
    return MessageResponse(message=message)


@router.post(
    "/unequip",
    response_model=MessageResponse,
    responses={400: {"model": ErrorResponse}},
)
async def unequip_item(
    request: EquipItemRequest,  # Reusing request, only item_id needed
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Unequip an item."""
    user_id = UUID(current_user["user_id"])
    
    player_repo = PlayerRepository(db)
    item_repo = ItemRepository(db)
    
    player = await player_repo.get_by_user_id(user_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found",
        )
    
    # Verify ownership
    item = await item_repo.get_instance_by_id(request.item_instance_id)
    if not item or item.owner_id != player.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found",
        )
    
    if not item.is_equipped:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item is not equipped",
        )
    
    await item_repo.unequip_item(request.item_instance_id)
    
    item_name = item.blueprint.name if hasattr(item, 'blueprint') and item.blueprint else "Item"
    return MessageResponse(message=f"Unequipped {item_name}")


@router.post(
    "/{item_id}/upgrade",
    response_model=MessageResponse,
    responses={400: {"model": ErrorResponse}},
)
async def upgrade_item(
    item_id: UUID,
    request: UpgradeItemRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upgrade an item with XP."""
    user_id = UUID(current_user["user_id"])
    
    player_repo = PlayerRepository(db)
    item_repo = ItemRepository(db)
    
    player = await player_repo.get_by_user_id(user_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found",
        )
    
    use_case = UpgradeItemUseCase(
        item_repository=item_repo,
        player_repository=player_repo,
    )
    
    result, error = await use_case.execute(UpgradeItemInput(
        player_id=player.id,
        item_instance_id=item_id,
        xp_amount=request.xp_amount,
    ))
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    message = f"{result.item_name} is now level {result.new_level}"
    if result.levels_gained > 0:
        message += f" (+{result.levels_gained} levels!)"
    
    return MessageResponse(message=message)
