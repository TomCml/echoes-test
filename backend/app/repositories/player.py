from sqlalchemy.orm import Session
from app.models.player import Player
from app.schemas.player import PlayerCreate, PlayerUpdate
from typing import Optional

def get_by_twitch_id(db: Session, twitch_id: int) -> Optional[Player]:
    return db.query(Player).filter(Player.twitch_id == twitch_id).first()

def get_by_id(db: Session, player_id: int) -> Optional[Player]:
    return db.query(Player).filter(Player.player_id == player_id).first()

def create(db: Session, player: PlayerCreate) -> Player:
    new_player = Player(
        twitch_id=player.twitch_id,
        username=player.username
    )
    db.add(new_player)
    db.commit()
    db.refresh(new_player)
    return new_player

def update(db: Session, player_id: int, payload: PlayerUpdate) -> Optional[Player]:
    player = get_by_id(db, player_id)
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

def delete(db: Session, player_id: int) -> bool:
    player = get_by_id(db, player_id)
    if not player:
        return False

    db.delete(player)
    db.commit()
    return True
