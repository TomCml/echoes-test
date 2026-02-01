"""
Player Repository - Fonctions d'accès DB pour les joueurs.
Recyclé depuis controllers/player.py
"""
import logging
from sqlalchemy.orm import Session
from typing import Optional
from app.models.player import Player
from app.schemas.player import PlayerCreate, PlayerUpdate

logger = logging.getLogger(__name__)


def get_by_id(db: Session, player_id: int) -> Optional[Player]:
    """Récupère un joueur par son ID."""
    return db.query(Player).filter(Player.player_id == player_id).first()


def get_by_twitch_id(db: Session, twitch_id: int) -> Optional[Player]:
    """Récupère un joueur par son ID Twitch."""
    return db.query(Player).filter(Player.twitch_id == twitch_id).first()


def create(db: Session, payload: PlayerCreate) -> Player:
    """Crée un nouveau joueur."""
    new_player = Player(
        twitch_id=payload.twitch_id,
        username=payload.username
    )
    db.add(new_player)
    db.commit()
    db.refresh(new_player)
    logger.debug(f"Player created: {new_player.player_id}")
    return new_player


def update(db: Session, player_id: int, payload: PlayerUpdate) -> Optional[Player]:
    """Met à jour un joueur existant."""
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


def delete(db: Session, player_id: int) -> bool:
    """Supprime un joueur."""
    player = db.query(Player).filter(Player.player_id == player_id).first()
    if not player:
        return False

    db.delete(player)
    db.commit()
    return True
