from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.player import PlayerResponse, LoginRequest
from app.repositories.player import get_by_twitch_id, create as create_player

router = APIRouter()

@router.post("/login", response_model=PlayerResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> PlayerResponse:
    player = get_by_twitch_id(db, payload.twitch_id)
    if player:
        return player

    # Assuming create_player repository takes PlayerCreate schema, we need to convert LoginRequest or create it
    # But repository create() takes PlayerCreate. LoginRequest might be different?
    # backend/schemas/player.py likely has PlayerCreate.
    # payload is LoginRequest.
    # We might need to construct PlayerCreate from payload.
    # For now, simplistic adaptation based on previous commented code.
    from app.schemas.player import PlayerCreate
    new_player_in = PlayerCreate(twitch_id=payload.twitch_id, username=payload.username)
    new_player = create_player(db, new_player_in)
    return new_player
