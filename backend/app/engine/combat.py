"""
Combat Engine — Registre d'opcodes et fonctions utilitaires.

Le cœur du système d'effets :
- register(opcode) : décore une fonction pour l'enregistrer
- run_effects()    : exécute une liste d'EffectPayload sur le Battle
- eval_formula()   : évalue une expression mathématique avec les stats
- apply_damage()   : applique des dégâts à une entité + émet DamageEvent
- apply_heal()     : applique un soin à une entité + émet HealEvent
- apply_status()   : applique un statut à une entité + émet StatusAppliedEvent
"""
from typing import Dict, Any, Callable, List
from app.engine.domain import Battle, Entity
from app.schemas.combat_events import (
    DamageEvent,
    HealEvent,
    StatusAppliedEvent,
    EntityDeathEvent,
)

EffectFn = Callable[[Battle, Entity, Entity, Dict[str, Any]], None]
REGISTRY: Dict[str, EffectFn] = {}


def register(opcode: str):
    """Décorateur pour enregistrer un opcode dans le registre."""
    def deco(fn: EffectFn):
        REGISTRY[opcode] = fn
        return fn
    return deco


def run_effects(b: Battle, src: Entity, tgt: Entity, effects: List[Dict[str, Any]]):
    """
    Exécute une liste d'EffectPayload triés par `order`.

    Chaque payload = {"opcode": "...", "order": 0, "params": {...}}
    """
    for e in sorted(effects, key=lambda x: x.get("order", 0)):
        fn = REGISTRY.get(e["opcode"])
        if not fn:
            b.add_log(f"[WARN] unknown opcode: {e['opcode']}")
            continue
        fn(b, src, tgt, e.get("params", {}))


def eval_formula(expr: str, src: Entity, tgt: Entity) -> float:
    """
    Évalue une expression mathématique avec les stats des entités.

    Variables disponibles dans la formule :
      - AD, AP, ARMOR, MR, SPEED, HP, MAX_HP  → stats du caster (sans préfixe)
      - S_AD, S_AP, S_ARMOR ...                → stats du caster (préfixe explicite)
      - T_AD, T_AP, T_ARMOR ...                → stats de la cible
    """
    scope = {
        # Stats du caster sans préfixe (rétro-compatible avec "AD * 1.5")
        **src.stats.__dict__,
        # Stats du caster avec préfixe S_
        **{f"S_{k}": v for k, v in src.stats.__dict__.items()},
        # Stats de la cible avec préfixe T_
        **{f"T_{k}": v for k, v in tgt.stats.__dict__.items()},
    }

    return float(eval(expr, {"__builtins__": {}}, scope))


def apply_damage(
    b: Battle,
    target: Entity,
    amount: float,
    label: str = "damage",
    *,
    source: Entity | None = None,
    damage_type: str = "physical",
    is_crit: bool = False,
) -> int:
    """
    Applique des dégâts à une entité (minimum 1).
    Émet un DamageEvent + potentiellement un EntityDeathEvent.

    Returns:
        Le montant de dégâts effectivement appliqué.
    """
    val = max(1, int(round(amount)))
    target.stats.HP = max(0, target.stats.HP - val)

    # Legacy text log
    b.add_log(f"{target.name} takes {val} ({label}). HP {target.stats.HP}/{target.stats.MAX_HP}")

    # Structured event
    src_id = source.id if source else "unknown"
    b.emit(DamageEvent(
        turn=0, sequence=0,  # Overridden by emit()
        source=src_id,
        target=target.id,
        amount=val,
        damage_type=damage_type,
        is_crit=is_crit,
        label=label,
        target_hp_after=target.stats.HP,
        target_max_hp=target.stats.MAX_HP,
    ))

    # Death check
    if not target.is_alive:
        b.emit(EntityDeathEvent(
            turn=0, sequence=0,
            target=target.id,
            killer=src_id,
        ))

    return val


def apply_heal(
    b: Battle,
    target: Entity,
    amount: float,
    *,
    source: Entity | None = None,
) -> int:
    """
    Applique un soin à une entité (cap à MAX_HP).
    Émet un HealEvent.

    Returns:
        Le montant de soin effectivement appliqué.
    """
    val = max(0, int(round(amount)))
    old_hp = target.stats.HP
    target.stats.HP = min(target.stats.MAX_HP, target.stats.HP + val)
    actual = target.stats.HP - old_hp

    b.add_log(f"{target.name} heals {actual}. HP {target.stats.HP}/{target.stats.MAX_HP}")

    src_id = source.id if source else target.id
    b.emit(HealEvent(
        turn=0, sequence=0,
        source=src_id,
        target=target.id,
        amount=actual,
        target_hp_after=target.stats.HP,
        target_max_hp=target.stats.MAX_HP,
    ))

    return actual


def apply_status(
    b: Battle,
    target: Entity,
    code: str,
    duration: int,
    stacks_inc: int = 1,
    *,
    source: Entity | None = None,
) -> None:
    """
    Applique ou empile un statut sur une entité.
    Émet un StatusAppliedEvent.
    """
    inst = target.statuses.get(code)
    if inst:
        inst["stacks"] = inst.get("stacks", 1) + stacks_inc
        inst["remaining"] = max(inst["remaining"], duration)
        new_stacks = inst["stacks"]
    else:
        target.statuses[code] = {"remaining": duration, "stacks": stacks_inc}
        new_stacks = stacks_inc

    b.add_log(f"{target.name} gains {code} ({duration}t).")

    src_id = source.id if source else "unknown"
    b.emit(StatusAppliedEvent(
        turn=0, sequence=0,
        source=src_id,
        target=target.id,
        status_code=code,
        duration=duration,
        stacks=new_stacks,
    ))
