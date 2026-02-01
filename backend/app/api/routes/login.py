"""
Login Routes - Endpoints d'authentification.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories import player as player_repo
from app.schemas.player import PlayerCreate, PlayerRead

router = APIRouter()


@router.post("/login", response_model=PlayerRead)
def login(payload: PlayerCreate, db: Session = Depends(get_db)) -> PlayerRead:
    """Login or create a new player."""
    # Check if player exists
    player = player_repo.get_by_twitch_id(db, payload.twitch_id)
    if player:
        return player
    
    # Create new player
    new_player = player_repo.create(db, payload)
    return new_player
