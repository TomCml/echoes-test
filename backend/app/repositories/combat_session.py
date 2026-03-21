import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.combat_session import CombatSession, CombatLog, CombatSpellCooldown
from app.models.monster import Monster
from app.engine.domain import (
    Battle, Entity, Stats, CombatStatus, CombatLogEntry,
)

logger = logging.getLogger(__name__)

_STATUS_DEFS_CACHE: Optional[Dict[str, Any]] = None

def _load_status_defs() -> Dict[str, Any]:
    """Charge les définitions de statuts (copie locale pour éviter l'import circulaire)."""
    global _STATUS_DEFS_CACHE
    if _STATUS_DEFS_CACHE is not None:
        return _STATUS_DEFS_CACHE
    path = Path("./data/statuses.json")
    if path.exists():
        _STATUS_DEFS_CACHE = json.loads(path.read_text(encoding="utf-8"))
    else:
        _STATUS_DEFS_CACHE = {}
    return _STATUS_DEFS_CACHE


# ─────────────────────────────────────────────────────────
# CRUD
# ─────────────────────────────────────────────────────────

def get_by_id(db: Session, session_id: int) -> Optional[CombatSession]:
    """Charge une combat_session depuis la DB."""
    return db.query(CombatSession).filter(CombatSession.id == session_id).first()


def get_active_by_player(db: Session, player_id: int) -> Optional[CombatSession]:
    """Retourne le combat actif d'un joueur (s'il y en a un)."""
    return (
        db.query(CombatSession)
        .filter(
            CombatSession.player_id == player_id,
            CombatSession.status.notin_([
                CombatStatus.VICTORY,
                CombatStatus.DEFEAT,
                CombatStatus.ABANDONED,
            ])
        )
        .first()
    )


def create(
    db: Session,
    player_id: int,
    monster_id: int,
    monster_level: int,
    player_entity: Entity,
    monster_entity: Entity,
) -> CombatSession:
    """
    Crée une nouvelle combat_session en DB.

    Appelé par battle_service.start_battle() après avoir construit les entities.
    """
    session = CombatSession(
        player_id=player_id,
        monster_id=monster_id,
        monster_level=monster_level,
        status=CombatStatus.PLAYER_TURN,
        turn_count=1,
        current_turn_entity="player",
        # Player state
        player_current_hp=player_entity.stats.HP,
        player_max_hp=player_entity.stats.MAX_HP,
        player_echo_current=player_entity.gauges.get("echo", 0),
        player_echo_max=100,
        player_statuses=dict(player_entity.statuses),
        player_gauges=dict(player_entity.gauges),
        player_cds=dict(player_entity.cds),
        # Monster state
        monster_current_hp=monster_entity.stats.HP,
        monster_max_hp=monster_entity.stats.MAX_HP,
        monster_statuses=dict(monster_entity.statuses),
        monster_cds=dict(monster_entity.cds),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    logger.info(f"CombatSession #{session.id} created: player={player_id} vs monster={monster_id}")
    return session


# ─────────────────────────────────────────────────────────
# Load: DB → Battle
# ─────────────────────────────────────────────────────────

def load_battle(
    db: Session,
    session_id: int,
    player_base_stats: Stats,
    monster_base_stats: Stats,
    player_name: str = "Player",
    monster_name: str = "Monster",
) -> Optional[Battle]:
    """
    Reconstruit un Battle depuis une combat_session en DB.

    Les stats de base (AD, AP, ARMOR…) viennent du Player/Monster d'origine,
    mais HP, statuses, gauges, cds viennent de la session persistée.
    """
    cs = get_by_id(db, session_id)
    if not cs:
        return None

    # Rebuild player entity: stats de base + HP courant de la session
    p_stats = Stats(
        MAX_HP=cs.player_max_hp,
        HP=cs.player_current_hp,
        AD=player_base_stats.AD,
        AP=player_base_stats.AP,
        ARMOR=player_base_stats.ARMOR,
        MR=player_base_stats.MR,
        SPEED=player_base_stats.SPEED,
        CRIT_CHANCE=player_base_stats.CRIT_CHANCE,
        CRIT_DAMAGE=player_base_stats.CRIT_DAMAGE,
    )
    player_entity = Entity(
        id=str(cs.player_id),
        name=player_name,
        stats=p_stats,
        statuses=dict(cs.player_statuses or {}),
        gauges=dict(cs.player_gauges or {}),
        cds=dict(cs.player_cds or {}),
    )

    # Rebuild monster entity
    m_stats = Stats(
        MAX_HP=cs.monster_max_hp,
        HP=cs.monster_current_hp,
        AD=monster_base_stats.AD,
        AP=monster_base_stats.AP,
        ARMOR=monster_base_stats.ARMOR,
        MR=monster_base_stats.MR,
        SPEED=monster_base_stats.SPEED,
    )
    monster_entity = Entity(
        id=f"monster_{cs.monster_id}",
        name=monster_name,
        stats=m_stats,
        statuses=dict(cs.monster_statuses or {}),
        cds=dict(cs.monster_cds or {}),
    )

    # Load existing logs
    log_rows = (
        db.query(CombatLog)
        .filter(CombatLog.combat_session_id == session_id)
        .order_by(CombatLog.id)
        .all()
    )
    log_entries = [CombatLogEntry(turn=row.turn, message=row.message) for row in log_rows]

    # Build Battle
    battle = Battle(
        player=player_entity,
        monster=monster_entity,
        turn=cs.turn_count,
        status=CombatStatus(cs.status),
        status_defs=_load_status_defs(),
        log=log_entries,
    )

    return battle


# ─────────────────────────────────────────────────────────
# Save: Battle → DB
# ─────────────────────────────────────────────────────────

def save_battle(
    db: Session,
    session_id: int,
    battle: Battle,
    new_logs_start_index: int = 0,
) -> None:
    """
    Sauvegarde l'état du Battle dans la combat_session.

    Args:
        db: Session SQLAlchemy
        session_id: ID de la combat_session
        battle: Instance Battle avec l'état mise à jour
        new_logs_start_index: Index du premier log à persister
            (pour ne pas dupliquer les logs déjà en DB)
    """
    cs = get_by_id(db, session_id)
    if not cs:
        logger.error(f"CombatSession #{session_id} not found for save")
        return

    # Update session state
    cs.status = battle.status
    cs.turn_count = battle.turn
    cs.current_turn_entity = (
        "player" if battle.status == CombatStatus.PLAYER_TURN else "monster"
    )

    # Player state
    cs.player_current_hp = battle.player.stats.HP
    cs.player_statuses = dict(battle.player.statuses)
    cs.player_gauges = dict(battle.player.gauges)
    cs.player_cds = dict(battle.player.cds)

    # Monster state
    cs.monster_current_hp = battle.monster.stats.HP
    cs.monster_statuses = dict(battle.monster.statuses)
    cs.monster_cds = dict(battle.monster.cds)

    # End timestamp
    if battle.status in (CombatStatus.VICTORY, CombatStatus.DEFEAT, CombatStatus.ABANDONED):
        cs.ended_at = func.now()

    # Persist new log entries
    for entry in battle.log[new_logs_start_index:]:
        log_row = CombatLog(
            combat_session_id=session_id,
            turn=entry.turn,
            message=entry.message,
        )
        db.add(log_row)

    db.commit()
    logger.debug(f"CombatSession #{session_id} saved: turn={battle.turn}, status={battle.status}")


# ─────────────────────────────────────────────────────────
# Abandon
# ─────────────────────────────────────────────────────────

def abandon(db: Session, session_id: int) -> bool:
    """Abandonne un combat en cours."""
    cs = get_by_id(db, session_id)
    if not cs:
        return False
    if cs.status in (CombatStatus.VICTORY, CombatStatus.DEFEAT, CombatStatus.ABANDONED):
        return False

    cs.status = CombatStatus.ABANDONED
    cs.ended_at = func.now()
    db.commit()
    logger.info(f"CombatSession #{session_id} abandoned")
    return True
