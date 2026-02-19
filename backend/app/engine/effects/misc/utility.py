"""Utility opcodes - Opcodes utilitaires.

IMPORTANT: Tous les paramètres doivent être fournis par les items JSON.
"""
from typing import Dict, Any
from app.engine.combat import register
from app.engine.domain import Battle, Entity


def _require_param(b: Battle, opcode: str, p: Dict, key: str) -> bool:
    if key not in p:
        b.log.append(f"[WARN] {opcode}: '{key}' param missing")
        return False
    return True


@register("log_message")
def eff_log_message(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Ajoute un message au log. Params: message (REQUIS)"""
    if not _require_param(b, "log_message", p, "message"): return
    b.log.append(p["message"])


@register("debug_entity")
def eff_debug_entity(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Log les stats d'une entité (debug). Params: self (optionnel, default True)"""
    entity = src if p.get("self", True) else tgt
    b.log.append(f"[DEBUG] {entity.name}: HP={entity.stats.HP}/{entity.stats.MAX_HP}, "
                 f"AD={entity.stats.AD}, AP={entity.stats.AP}, "
                 f"ARMOR={entity.stats.ARMOR}, MR={entity.stats.MR}")


@register("random_choice")
def eff_random_choice(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Choisit un effet aléatoire parmi plusieurs. Params: choices (REQUIS - liste d'effets), weights (optionnel)"""
    if not _require_param(b, "random_choice", p, "choices"): return
    
    choices = p["choices"]
    weights = p.get("weights")
    
    if not choices:
        return
    
    if weights:
        total = sum(weights)
        r = b.rng.random() * total
        cumulative = 0
        for i, w in enumerate(weights):
            cumulative += w
            if r <= cumulative:
                chosen = choices[i]
                break
        else:
            chosen = choices[-1]
    else:
        chosen = b.rng.choice(choices)
    
    opcode = chosen.get("opcode")
    params = chosen.get("params", {})
    
    from app.engine.combat import REGISTRY
    if opcode in REGISTRY:
        REGISTRY[opcode](b, src, tgt, params)


@register("repeat_effect")
def eff_repeat_effect(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Répète un effet plusieurs fois. Params: times (REQUIS), effect (REQUIS)"""
    if not _require_param(b, "repeat_effect", p, "times"): return
    if not _require_param(b, "repeat_effect", p, "effect"): return
    
    times = int(p["times"])
    effect = p["effect"]
    
    opcode = effect.get("opcode")
    params = effect.get("params", {})
    
    from app.engine.combat import REGISTRY
    if opcode not in REGISTRY:
        return
    
    for i in range(times):
        REGISTRY[opcode](b, src, tgt, params)


@register("swap_target")
def eff_swap_target(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Exécute un effet avec src et tgt inversés. Params: effect (REQUIS)"""
    if not _require_param(b, "swap_target", p, "effect"): return
    
    effect = p["effect"]
    opcode = effect.get("opcode")
    params = effect.get("params", {})
    
    from app.engine.combat import REGISTRY
    if opcode in REGISTRY:
        REGISTRY[opcode](b, tgt, src, params)


@register("no_op")
def eff_no_op(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Ne fait rien (placeholder). Params: aucun"""
    pass
