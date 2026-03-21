"""
Battle Routes - Endpoints du système de combat.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db
from app.services import damage_service, battle_service
from app.repositories import player as player_repo
from app.repositories import item as item_repo

logger = logging.getLogger(__name__)

router = APIRouter()


# ─── Outils de calcul (sans persistance) ────────────────
# IMPORTANT: ces routes statiques DOIVENT être avant /{battle_id}
# sinon FastAPI matche "damages-calculation" comme un battle_id

@router.get("/damages-calculation")
def get_damages_calculation(
    crit: bool,
    item_id: str = Query(..., description="ID de l'item/weapon (JSON)"),
    spell_code: str = Query(..., description="Code du sort"),
    player_id: int = Query(1, description="ID de l'attaquant"),
    target_id: int = Query(2, description="ID de la cible"),
    db: Session = Depends(get_db),
):
    """Calcule les dégâts d'un sort (damage_service, sans persistance)."""
    player = player_repo.get_by_id(db, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Attacker (Player) not found")

    target = player_repo.get_by_id(db, target_id)
    if not target:
        from app.models.player import Player
        target = Player()

    item = item_repo.load_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    spell = None
    for s in item.get("spells", []):
        if s.get("code") == spell_code:
            spell = s
            break

    if not spell:
        raise HTTPException(status_code=404, detail=f"Spell '{spell_code}' not found in item")

    return damage_service.calculate_damage(
        player=player, target=target, item=item, spell=spell, crit=crit,
    )


@router.post("/simulate")
def simulate_spell(
    player_id: int = Query(..., description="ID de l'attaquant"),
    target_id: int = Query(..., description="ID de la cible"),
    item_id: str = Query(..., description="ID de l'item/weapon (JSON)"),
    spell_code: str = Query(..., description="Code du sort"),
    db: Session = Depends(get_db),
):
    """Simule un lancer de sort PvP (engine, sans persistance)."""
    result = battle_service.simulate_spell(db, player_id, target_id, item_id, spell_code)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ─── Combat persisté ────────────────────────────────────

@router.post("/start")
def start_battle(
    player_id: int = Query(..., description="ID du joueur"),
    monster_id: int = Query(..., description="ID du monstre"),
    monster_level: int = Query(1, description="Niveau du monstre"),
    db: Session = Depends(get_db),
):
    """Commence un nouveau combat Player vs Monster."""
    result = battle_service.start_battle(db, player_id, monster_id, monster_level)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{battle_id}/turn")
def execute_turn(
    battle_id: int,
    spell_code: str = Query(..., description="Code du sort à lancer"),
    item_id: str = Query(..., description="ID de l'item équipé"),
    db: Session = Depends(get_db),
):
    """Exécute un tour complet (player + monster)."""
    result = battle_service.execute_turn(db, battle_id, spell_code, item_id)
    if "error" in result:
        status = 404 if "not found" in result["error"].lower() else 400
        raise HTTPException(status_code=status, detail=result["error"])
    return result


@router.get("/{battle_id}")
def get_battle(
    battle_id: int,
    db: Session = Depends(get_db),
):
    """Retourne l'état courant d'un combat."""
    result = battle_service.get_battle_state(db, battle_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/{battle_id}/abandon")
def abandon_battle(
    battle_id: int,
    db: Session = Depends(get_db),
):
    """Abandonne un combat en cours."""
    result = battle_service.abandon_battle(db, battle_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
