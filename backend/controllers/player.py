import logging
from sqlalchemy.orm import Session
from models.player import Player
from typing import Dict, Any, Optional
from schemas.player import PlayerCreate, PlayerUpdate

logger = logging.getLogger(__name__)

def get_player_by_twitch_id(db: Session, twitch_id: int) -> Optional[Player]:
    return db.query(Player).filter(Player.twitch_id == twitch_id).first()

def get_player_by_id(db: Session, player_id: int) -> Optional[Player]:
    return db.query(Player).filter(Player.player_id == player_id).first()

def create_player(db: Session, player: PlayerCreate) -> Player:
    new_player = Player(
        twitch_id=player.twitch_id,
        username=player.username
    )
    db.add(new_player)
    db.commit()
    db.refresh(new_player)
    logger.debug(f"Player created: {new_player.player_id}")
    return new_player

def update_player(db: Session, player_id: int, payload: PlayerUpdate) -> Optional[Player]:
    player = db.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        return None

    updates = payload.model_dump(exclude_unset=True)

    for key, value in updates.items():
        if hasattr(player, key):
            setattr(player, key, value)

    db.add(player)
    db.commit()
    db.refresh(player)
    return player

def delete_player(db: Session, player_id: int) -> bool:
    player = db.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        return False

    db.delete(player)
    db.commit()
    return True