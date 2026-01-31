from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
# from schemas.player import PlayerResponse, LoginRequest
from controllers.player import get_player_by_twitch_id, create_player

router = APIRouter()

# @router.post("/login", response_model=PlayerResponse)
# def login(payload: LoginRequest, db: Session = Depends(get_db)) -> PlayerResponse:
#     player = get_player_by_twitch_id(db, payload.twitch_id)
#     if player:
#         return player

#     new_player = create_player(db, payload.twitch_id)
#     return new_player
