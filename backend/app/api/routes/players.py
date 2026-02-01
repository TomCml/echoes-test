from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.repositories.player import get_by_id, update, delete
from app.schemas.player import PlayerResponse, PlayerUpdate

router = APIRouter()

@router.get("/{player_id}", response_model=PlayerResponse)
def get_player(player_id: int, db: Session = Depends(get_db)):
    player = get_by_id(db, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player

@router.patch("/{player_id}", response_model=PlayerResponse)
def update_player_route(player_id: int, payload: PlayerUpdate, db: Session = Depends(get_db)):
    player = update(db, player_id, payload)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player

@router.delete("/{player_id}")
def delete_player_route(player_id: int, db: Session = Depends(get_db)):
    success = delete(db, player_id)
    if not success:
        raise HTTPException(status_code=404, detail="Player not found")
    return {"message": "Player deleted"}
