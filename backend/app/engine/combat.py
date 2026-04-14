"""
Combat Engine — Registre d'opcodes et fonctions utilitaires.

Le cœur du système d'effets :
- register(opcode) : décore une fonction pour l'enregistrer
- run_effects()    : exécute une liste d'EffectPayload sur le Battle
- eval_formula()   : évalue une expression mathématique avec les stats
- apply_damage()   : applique des dégâts à une entité
- apply_status()   : applique un statut à une entité
"""
from typing import Dict, Any, Callable, List
from app.engine.domain import Battle, Entity

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


def apply_damage(b: Battle, target: Entity, amount: float, label: str = "damage"):
    """Applique des dégâts à une entité (minimum 1)."""
    val = max(1, int(round(amount)))
    target.stats.HP = max(0, target.stats.HP - val)
    b.add_log(f"{target.name} takes {val} ({label}). HP {target.stats.HP}/{target.stats.MAX_HP}")


def apply_status(b: Battle, target: Entity, code: str, duration: int, stacks_inc: int = 1):
    """Applique ou empile un statut sur une entité."""
    inst = target.statuses.get(code)
    if inst:
        inst["stacks"] = inst.get("stacks", 1) + stacks_inc
        inst["remaining"] = max(inst["remaining"], duration)
    else:
        target.statuses[code] = {"remaining": duration, "stacks": stacks_inc}
    b.add_log(f"{target.name} gains {code} ({duration}t).")
