"""
Battle Service — Orchestration complète du combat avec persistance DB.

Public API :
  start_battle()     → crée la session en DB, retourne battle_id
  execute_turn()     → charge depuis DB, exécute un tour, re-sauvegarde
  get_battle_state() → retourne l'état courant depuis DB
  abandon_battle()   → abandonne un combat en cours
  simulate_spell()   → one-shot PvP (sans persistance, rétro-compat)

Utilise :
  - Engine domain  (Battle, Entity, Stats)
  - Engine combat  (run_effects, REGISTRY)
  - Engine status_engine (end_turn)
  - Repositories   (player, item, combat_session)
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from sqlalchemy.orm import Session

from app.engine.domain import Battle, Entity, Stats, CombatStatus, CombatLogEntry
from app.engine.combat import run_effects
from app.engine.status_engine import start_turn, end_turn
# Importer les effects pour enregistrer les opcodes
from app.engine import effects as _effects  # noqa: F401

from app.repositories import player as player_repo
from app.repositories import item as item_repo
from app.repositories import combat_session as combat_session_repo

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────
# Cache status definitions (chargé une seule fois)
# ─────────────────────────────────────────────────────────

_STATUS_DEFS_CACHE: Optional[Dict[str, Any]] = None


def _load_status_defs() -> Dict[str, Any]:
    """Charge les définitions de statuts depuis data/statuses.json."""
    global _STATUS_DEFS_CACHE
    if _STATUS_DEFS_CACHE is not None:
        return _STATUS_DEFS_CACHE

    path = Path("./data/statuses.json")
    if path.exists():
        _STATUS_DEFS_CACHE = json.loads(path.read_text(encoding="utf-8"))
    else:
        logger.warning("statuses.json not found, no tick effects will apply")
        _STATUS_DEFS_CACHE = {}
    return _STATUS_DEFS_CACHE


# ─────────────────────────────────────────────────────────
# Entity Factories
# ─────────────────────────────────────────────────────────

def _get_item_stats_at_level(item_data: Dict[str, Any], item_level: int) -> Dict[str, float]:
    """
    Calcule les stats d'un item à un niveau donné.
    stat_finale = base_stat + scaling_per_level * (item_level - 1)
    """
    base = item_data.get("base_stats", item_data.get("stats", {}))
    scaling = item_data.get("stats_scaling", {})
    level_bonus = max(0, item_level - 1)

    result: Dict[str, float] = {}
    for key, val in base.items():
        result[key] = float(val)

    # Appliquer le scaling
    for scale_key, scale_val in scaling.items():
        # Convertir "ad_per_level" → "AD"
        stat_name = scale_key.replace("_per_level", "").upper()
        result[stat_name] = result.get(stat_name, 0.0) + float(scale_val) * level_bonus

    return result


def player_to_entity(player, loadout: Optional[List[Any]] = None) -> Entity:
    """Convertit un Player SQLAlchemy en Entity du moteur, en incluant les stats d'équipement."""
    entity = Entity(
        id=str(player.player_id),
        name=player.username,
        stats=Stats(
            MAX_HP=player.health_points,
            HP=player.health_points,
            AD=player.attack_damage,
            AP=getattr(player, 'ability_power', 0) or 0,
            ARMOR=player.armor or 0,
            MR=getattr(player, 'magic_resistance', 0) or 0,
            SPEED=getattr(player, 'speed', 10) or 10,
            CRIT_CHANCE=(getattr(player, 'crit_chance', 0) or 0) / 100.0,
            CRIT_DAMAGE=1.5,
        ),
        gauges={"echo": getattr(player, 'echo_current', 0) or 0},
    )

    if loadout:
        for inv in loadout:
            item_data = item_repo.load_item(inv.item_id)
            if not item_data:
                continue

            item_level = getattr(inv, 'item_level', 1) or 1
            stats_bonus = _get_item_stats_at_level(item_data, item_level)

            hp_bonus = stats_bonus.get("MAX_HP", 0)
            entity.stats.MAX_HP += int(hp_bonus)
            entity.stats.HP += int(hp_bonus)
            entity.stats.AD += int(stats_bonus.get("AD", 0))
            entity.stats.AP += int(stats_bonus.get("AP", 0))
            entity.stats.ARMOR += int(stats_bonus.get("ARMOR", 0))
            entity.stats.MR += int(stats_bonus.get("MR", 0))
            entity.stats.SPEED += int(stats_bonus.get("SPEED", 0))

            crit = stats_bonus.get("CRIT_CHANCE", 0)
            if crit > 0:
                entity.stats.CRIT_CHANCE += float(crit)

    return entity


def _player_base_stats(player, loadout: Optional[List[Any]] = None) -> Stats:
    """Extrait les Stats de base d'un Player (loadout inclus) pour reload depuis DB."""
    return player_to_entity(player, loadout).stats


def monster_to_entity(monster, level: Optional[int] = None) -> Entity:
    """Convertit un Monster SQLAlchemy en Entity du moteur avec level scaling."""
    lvl = level or getattr(monster, 'level', 1) or 1

    s_hp = getattr(monster, 'scaling_hp_per_level', 0) or 0
    s_ad = getattr(monster, 'scaling_ad_per_level', 0) or 0
    s_armor = getattr(monster, 'scaling_armor_per_level', 0) or 0

    bonus = max(0, lvl - 1)
    hp = (getattr(monster, 'hp_max', 500) or 500) + int(s_hp * bonus)
    ad = (getattr(monster, 'attack_damage', 50) or 50) + int(s_ad * bonus)
    armor = (getattr(monster, 'armor', 0) or 0) + int(s_armor * bonus)

    return Entity(
        id=f"monster_{monster.monster_id}",
        name=monster.name,
        stats=Stats(
            MAX_HP=hp, HP=hp,
            AD=ad,
            AP=getattr(monster, 'ability_power', 0) or 0,
            ARMOR=armor,
            MR=getattr(monster, 'magic_resistance', 0) or 0,
            SPEED=getattr(monster, 'speed', 10) or 10,
        ),
        tags={"boss"} if getattr(monster, 'is_boss', False) else set(),
    )


def _monster_base_stats(monster, level: int = 1) -> Stats:
    """Extrait les Stats de base d'un Monster (pour reload depuis DB)."""
    entity = monster_to_entity(monster, level)
    return entity.stats


# ─────────────────────────────────────────────────────────
# Spell helpers
# ─────────────────────────────────────────────────────────

def _find_spell(item_data: Dict[str, Any], spell_code: str) -> Optional[Dict[str, Any]]:
    """Cherche un sort par code dans les données d'un item."""
    for s in item_data.get("spells", []):
        if s.get("code") == spell_code:
            return s
    return None


def _check_cooldown(entity: Entity, spell: Dict[str, Any]) -> Optional[str]:
    """Vérifie si le sort est prêt. Retourne None si OK, erreur sinon."""
    code = spell.get("code", "")
    remaining = entity.cds.get(code, 0)
    if remaining > 0:
        return f"Spell '{code}' is on cooldown ({remaining} turns remaining)"
    return None


def _apply_cooldown(entity: Entity, spell: Dict[str, Any]) -> None:
    """Met le sort en cooldown."""
    cd = spell.get("cooldown_turns", 0)
    if cd > 0:
        entity.cds[spell["code"]] = cd


def _check_echo_cost(entity: Entity, spell: Dict[str, Any]) -> Optional[str]:
    """Vérifie si le sort nécessite d'avoir l'écho max (c'est le cas du sort ultime 'Echo')."""
    is_ultimate = spell.get("is_echo", False)
    if is_ultimate:
        current = entity.gauges.get("echo", 0)
        max_echo = entity.gauges.get("echo_max", 100)  # Default max 100
        if current < max_echo:
            return f"Not enough echo to cast ultimate ({current}/{max_echo})"
    return None


def _generate_echo(entity: Entity, spell: Dict[str, Any], battle: Battle) -> None:
    """Génère de l'écho en lançant un sort classique, ou le consomme si c'est l'ultime."""
    is_ultimate = spell.get("is_echo", False)
    
    if is_ultimate:
        # Ultimate consomme tout l'écho
        entity.gauges["echo"] = 0
        battle.add_log(f"💥 {entity.name} unleashes an ECHO spell! Gauge reset to 0.")
    else:
        # Les sorts classiques génèrent de l'écho (0-5)
        # On utilise 'echo_cost' du json temporairement, ou une nouvelle clé 'echo_gain'
        gain = spell.get("echo_gain", spell.get("echo_cost", 0))
        if gain > 0:
            max_echo = entity.gauges.get("echo_max", 100)
            current = entity.gauges.get("echo", 0)
            new_val = min(max_echo, current + gain)
            entity.gauges["echo"] = new_val
            if new_val > current:
                battle.add_log(f"✨ {entity.name} gains {new_val - current} echo ({new_val}/{max_echo}).")


# ─────────────────────────────────────────────────────────
# Passives
# ─────────────────────────────────────────────────────────

def _infer_damage_type(flags: List[str]) -> str:
    """Infère le damage_type depuis les flags du spell."""
    flags_lower = [f.lower() for f in flags]
    if "physical" in flags_lower:
        return "physical"
    if "magic" in flags_lower or "magical" in flags_lower:
        return "magic"
    if "true" in flags_lower:
        return "true"
    if "mixed" in flags_lower:
        return "mixed"
    return "physical"  # default


def _inject_spell_context(spell: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Injecte le contexte du spell (damage_type, flags) dans les params de chaque effet.

    Évite de dupliquer l'info dans le JSON :
      - spell.flags = ["physical", "can_crit"] → chaque damage effect reçoit damage_type=physical
    """
    effects = spell.get("effects", [])
    flags = spell.get("flags", [])
    damage_type = _infer_damage_type(flags)

    enriched = []
    for e in effects:
        e_copy = dict(e)
        if e_copy.get("opcode") == "damage":
            params = dict(e_copy.get("params", {}))
            if "damage_type" not in params:
                params["damage_type"] = damage_type
            e_copy["params"] = params
        enriched.append(e_copy)
    return enriched


def _trigger_passives(
    battle: Battle, caster: Entity, target: Entity,
    item_data: Dict[str, Any], trigger: str
) -> None:
    """Déclenche les passives d'un item qui matchent le trigger."""
    for passive in item_data.get("passives", []):
        if passive.get("trigger") == trigger:
            battle.add_log(f"Passive: {passive.get('name', '?')}")
            run_effects(battle, caster, target, passive.get("effects", []))


# ─────────────────────────────────────────────────────────
# Monster AI
# ─────────────────────────────────────────────────────────

def _monster_ai_pick(
    battle: Battle, monster: Entity, abilities: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """IA simple : filtre CD, évalue conditions, trie par priorité."""
    available = []
    for ability in abilities:
        code = ability.get("name", "")
        if monster.cds.get(code, 0) > 0:
            continue

        condition = ability.get("condition_expr") or ability.get("condition")
        if condition:
            try:
                target = battle.other(monster)
                hp_ratio = target.stats.HP / max(1, target.stats.MAX_HP)
                scope = {
                    "target_hp_ratio": hp_ratio,
                    "monster_hp_ratio": monster.stats.HP / max(1, monster.stats.MAX_HP),
                    "turn": battle.turn,
                }
                if not eval(condition, {"__builtins__": {}}, scope):
                    continue
            except Exception:
                pass

        available.append(ability)

    if not available:
        return None

    available.sort(key=lambda a: a.get("priority", 1), reverse=True)
    return available[0]


def _execute_monster_ability(
    battle: Battle, monster: Entity, target: Entity, ability: Dict[str, Any]
) -> None:
    """Exécute une ability du monstre."""
    name = ability.get("name", "Attack")
    battle.add_log(f"{monster.name} uses {name}!")
    run_effects(battle, monster, target, ability.get("effects", []))
    cd = ability.get("cooldown", 0)
    if cd > 0:
        monster.cds[name] = cd


def _monster_basic_attack(battle: Battle, monster: Entity, target: Entity) -> None:
    """Attaque de base du monstre (dégâts = AD)."""
    from app.engine.combat import apply_damage
    battle.add_log(f"{monster.name} attacks!")
    apply_damage(battle, target, float(monster.stats.AD), label="basic attack")


# ─────────────────────────────────────────────────────────
# Serialization
# ─────────────────────────────────────────────────────────

def _serialize_entity(entity: Entity) -> Dict[str, Any]:
    return {
        "id": entity.id,
        "name": entity.name,
        "stats": {
            "HP": entity.stats.HP, "MAX_HP": entity.stats.MAX_HP,
            "AD": entity.stats.AD, "AP": entity.stats.AP,
            "ARMOR": entity.stats.ARMOR, "MR": entity.stats.MR,
            "SPEED": entity.stats.SPEED,
        },
        "statuses": {
            code: {"remaining": inst["remaining"], "stacks": inst.get("stacks", 1)}
            for code, inst in entity.statuses.items()
        },
        "gauges": dict(entity.gauges),
        "cooldowns": dict(entity.cds),
        "is_alive": entity.is_alive,
    }


def _serialize_battle(battle: Battle, session_id: Optional[int] = None) -> Dict[str, Any]:
    result = {
        "turn": battle.turn,
        "status": battle.status.value,
        "player": _serialize_entity(battle.player),
        "monster": _serialize_entity(battle.monster),
        "log": [
            {"turn": entry.turn, "message": entry.message}
            for entry in battle.log
        ],
    }
    if session_id is not None:
        result["battle_id"] = session_id
    return result


# ═════════════════════════════════════════════════════════
#  PUBLIC API
# ═════════════════════════════════════════════════════════

def start_battle(
    db: Session,
    player_id: int,
    monster_id: int,
    monster_level: int = 1,
) -> Dict[str, Any]:
    """
    Démarre un nouveau combat et le persiste en DB.

    Returns:
        {"success": True, "battle_id": int, "battle": {...}}
    """
    from app.models.monster import Monster

    # Check no active battle
    active = combat_session_repo.get_active_by_player(db, player_id)
    if active:
        return {"error": f"Player already has an active battle (id={active.id})"}

    # Load player
    player = player_repo.get_by_id(db, player_id)
    if not player:
        return {"error": f"Player {player_id} not found"}

    # Load monster
    monster = db.query(Monster).filter(Monster.monster_id == monster_id).first()
    if not monster:
        return {"error": f"Monster {monster_id} not found"}

    # Create entities
    from app.repositories.inventory import get_all_equipped
    loadout = get_all_equipped(db, player_id)
    player_entity = player_to_entity(player, loadout)
    monster_entity = monster_to_entity(monster, monster_level)

    # Persist session
    cs = combat_session_repo.create(
        db, player_id, monster_id, monster_level,
        player_entity, monster_entity,
    )

    # Build Battle for initial state / logging
    battle = Battle(
        player=player_entity,
        monster=monster_entity,
        status_defs=_load_status_defs(),
    )
    battle.start()

    # Persist the start log
    combat_session_repo.save_battle(db, cs.id, battle, new_logs_start_index=0)

    logger.info(f"Battle #{cs.id} started: {player_entity.name} vs {monster_entity.name}")

    return {
        "success": True,
        "battle_id": cs.id,
        "battle": _serialize_battle(battle, session_id=cs.id),
    }


def execute_turn(
    db: Session,
    battle_id: int,
    spell_code: str,
    item_id: str,
    monster_abilities: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Exécute un tour complet : player spell → passives → tick → monster AI → tick.

    Charge depuis DB, exécute, sauvegarde.

    Returns:
        {"success": True, "battle": {...}}
    """
    from app.models.monster import Monster

    # 1. Load combat session
    cs = combat_session_repo.get_by_id(db, battle_id)
    if not cs:
        return {"error": f"Battle {battle_id} not found"}

    if cs.status in (CombatStatus.VICTORY, CombatStatus.DEFEAT, CombatStatus.ABANDONED):
        return {"error": "Battle is already finished"}

    # 2. Load base entities for stat reconstruction
    player = player_repo.get_by_id(db, cs.player_id)
    monster = db.query(Monster).filter(Monster.monster_id == cs.monster_id).first()

    if not player or not monster:
        return {"error": "Could not load player or monster data"}

    # 3. Reconstruct Battle from DB
    from app.repositories.inventory import get_all_equipped
    loadout = get_all_equipped(db, cs.player_id)

    battle = combat_session_repo.load_battle(
        db, battle_id,
        player_base_stats=_player_base_stats(player, loadout),
        monster_base_stats=_monster_base_stats(monster, cs.monster_level),
        player_name=player.username,
        monster_name=monster.name,
    )
    if not battle:
        return {"error": f"Could not load battle {battle_id}"}

    log_count_before = len(battle.log)

    # 4. Load item data
    item_data = item_repo.load_item(item_id)
    if not item_data:
        return {"error": f"Item {item_id} not found"}

    # ─── Phase 1: Player Turn ────────────────────────

    battle.status = CombatStatus.PLAYER_TURN
    start_turn(battle, battle.player)

    spell = _find_spell(item_data, spell_code)
    if not spell:
        return {"error": f"Spell '{spell_code}' not found in item"}

    cd_error = _check_cooldown(battle.player, spell)
    if cd_error:
        return {"error": cd_error, "battle": _serialize_battle(battle, battle_id)}

    echo_error = _check_echo_cost(battle.player, spell)
    if echo_error:
        return {"error": echo_error, "battle": _serialize_battle(battle, battle_id)}

    # Execute spell
    battle.add_log(f"{battle.player.name} casts {spell.get('name', spell_code)}!")
    _generate_echo(battle.player, spell, battle)
    enriched_effects = _inject_spell_context(spell)
    run_effects(battle, battle.player, battle.monster, enriched_effects)
    _trigger_passives(battle, battle.player, battle.monster, item_data, trigger="on_hit")
    _apply_cooldown(battle.player, spell)
    end_turn(battle, battle.player)

    # Check if monster died
    if battle.is_finished():
        winner = battle.get_winner()
        battle.add_log(f"{winner.name} wins!")
        combat_session_repo.save_battle(db, battle_id, battle, log_count_before)
        return {"success": True, "battle": _serialize_battle(battle, battle_id)}

    # ─── Phase 2: Monster Turn ───────────────────────

    battle.status = CombatStatus.MONSTER_TURN
    start_turn(battle, battle.monster)

    abilities = monster_abilities or []
    chosen = _monster_ai_pick(battle, battle.monster, abilities)

    if chosen:
        _execute_monster_ability(battle, battle.monster, battle.player, chosen)
    else:
        _monster_basic_attack(battle, battle.monster, battle.player)

    end_turn(battle, battle.monster)

    if battle.is_finished():
        winner = battle.get_winner()
        battle.add_log(f"{winner.name} wins!")
        combat_session_repo.save_battle(db, battle_id, battle, log_count_before)
        return {"success": True, "battle": _serialize_battle(battle, battle_id)}

    # ─── Advance turn ────────────────────────────────

    battle.next_turn()

    # 5. Save state back to DB
    combat_session_repo.save_battle(db, battle_id, battle, log_count_before)

    return {"success": True, "battle": _serialize_battle(battle, battle_id)}


def get_battle_state(db: Session, battle_id: int) -> Dict[str, Any]:
    """Retourne l'état courant d'un combat depuis la DB."""
    from app.models.monster import Monster

    cs = combat_session_repo.get_by_id(db, battle_id)
    if not cs:
        return {"error": f"Battle {battle_id} not found"}

    player = player_repo.get_by_id(db, cs.player_id)
    monster = db.query(Monster).filter(Monster.monster_id == cs.monster_id).first()

    if not player or not monster:
        return {"error": "Could not load player or monster data"}

    from app.repositories.inventory import get_all_equipped
    loadout = get_all_equipped(db, cs.player_id)

    battle = combat_session_repo.load_battle(
        db, battle_id,
        player_base_stats=_player_base_stats(player, loadout),
        monster_base_stats=_monster_base_stats(monster, cs.monster_level),
        player_name=player.username,
        monster_name=monster.name,
    )
    if not battle:
        return {"error": f"Could not load battle {battle_id}"}

    return {"success": True, "battle": _serialize_battle(battle, battle_id)}


def abandon_battle(db: Session, battle_id: int) -> Dict[str, Any]:
    """Abandonne un combat en cours."""
    success = combat_session_repo.abandon(db, battle_id)
    if not success:
        return {"error": "Battle not found or already ended"}
    return {"success": True, "message": f"Battle {battle_id} abandoned"}


# ─────────────────────────────────────────────────────────
# Consumable effects
# ─────────────────────────────────────────────────────────

def apply_consumable_effects(
    db: Session,
    battle_id: int,
    player_id: int,
    effects: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Applique les effets d'un consommable sur le combat en cours.
    Charge la session, applique les effets sur le joueur, sauvegarde.
    """
    from app.models.monster import Monster

    cs = combat_session_repo.get_by_id(db, battle_id)
    if not cs or cs.player_id != player_id:
        return None

    if cs.status in (CombatStatus.VICTORY, CombatStatus.DEFEAT, CombatStatus.ABANDONED):
        return None

    player = player_repo.get_by_id(db, player_id)
    monster = db.query(Monster).filter(Monster.monster_id == cs.monster_id).first()
    if not player or not monster:
        return None

    from app.repositories.inventory import get_all_equipped
    loadout = get_all_equipped(db, player_id)

    battle = combat_session_repo.load_battle(
        db, battle_id,
        player_base_stats=_player_base_stats(player, loadout),
        monster_base_stats=_monster_base_stats(monster, cs.monster_level),
        player_name=player.username,
        monster_name=monster.name,
    )
    if not battle:
        return None

    log_count_before = len(battle.log)
    battle.add_log(f"{player.username} uses a consumable!")
    # Les effets s'appliquent sur le joueur (self-target)
    run_effects(battle, battle.player, battle.player, effects)

    combat_session_repo.save_battle(db, battle_id, battle, log_count_before)
    return _serialize_battle(battle, battle_id)


# ─────────────────────────────────────────────────────────
# Legacy: One-shot simulation (sans persistance)
# ─────────────────────────────────────────────────────────

def simulate_spell(
    db: Session,
    player_id: int,
    target_id: int,
    item_id: str,
    spell_code: str,
) -> Dict[str, Any]:
    """Simule un seul lancer de sort PvP (sans persistance DB)."""
    player = player_repo.get_by_id(db, player_id)
    if not player:
        return {"error": f"Player {player_id} not found"}

    target = player_repo.get_by_id(db, target_id)
    if not target:
        return {"error": f"Target {target_id} not found"}

    item = item_repo.load_item(item_id)
    if not item:
        return {"error": f"Item {item_id} not found"}

    spell = _find_spell(item, spell_code)
    if not spell:
        return {"error": f"Spell '{spell_code}' not found in item"}

    from app.repositories.inventory import get_all_equipped
    src_loadout = get_all_equipped(db, player_id)
    tgt_loadout = get_all_equipped(db, target_id)

    src = player_to_entity(player, src_loadout)
    tgt = player_to_entity(target, tgt_loadout)

    battle = Battle(player=src, monster=tgt, status_defs=_load_status_defs())
    battle.start()

    run_effects(battle, src, tgt, spell.get("effects", []))
    _trigger_passives(battle, src, tgt, item, trigger="on_hit")
    end_turn(battle, src)

    return {"success": True, "battle": _serialize_battle(battle)}
