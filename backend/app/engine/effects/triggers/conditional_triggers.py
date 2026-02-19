"""Conditional triggers - Déclencheurs conditionnels.

IMPORTANT: Tous les paramètres doivent être fournis par les items JSON.
"""
from typing import Dict, Any
from app.engine.combat import register, REGISTRY
from app.engine.domain import Battle, Entity


def _require_param(b: Battle, opcode: str, p: Dict, key: str) -> bool:
    if key not in p:
        b.log.append(f"[WARN] {opcode}: '{key}' param missing")
        return False
    return True


@register("conditional_effect")
def eff_conditional_effect(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Exécute un effet si une condition est remplie. Params: condition (REQUIS), effect (REQUIS), else_effect (optionnel)"""
    if not _require_param(b, "conditional_effect", p, "condition"): return
    if not _require_param(b, "conditional_effect", p, "effect"): return
    
    condition = p["condition"]
    effect = p["effect"]
    else_effect = p.get("else_effect")
    
    condition_met = _check_condition(b, src, tgt, condition)
    
    if condition_met:
        opcode = effect.get("opcode")
        params = effect.get("params", {})
        if opcode in REGISTRY:
            REGISTRY[opcode](b, src, tgt, params)
    elif else_effect:
        opcode = else_effect.get("opcode")
        params = else_effect.get("params", {})
        if opcode in REGISTRY:
            REGISTRY[opcode](b, src, tgt, params)


def _check_condition(b: Battle, src: Entity, tgt: Entity, condition: Dict) -> bool:
    """Vérifie une condition. Requires: type, avec params spécifiques par type."""
    cond_type = condition.get("type")
    
    if cond_type == "has_status":
        entity = src if condition.get("on_self", False) else tgt
        return condition.get("status_code") in entity.statuses
    
    elif cond_type == "hp_below":
        entity = src if condition.get("on_self", False) else tgt
        threshold = float(condition.get("threshold", 0.5))
        return entity.stats.HP / entity.stats.MAX_HP <= threshold
    
    elif cond_type == "hp_above":
        entity = src if condition.get("on_self", False) else tgt
        threshold = float(condition.get("threshold", 0.5))
        return entity.stats.HP / entity.stats.MAX_HP > threshold
    
    elif cond_type == "gauge_at_least":
        gauge = condition.get("gauge")
        value = int(condition.get("value", 0))
        return src.gauges.get(gauge, 0) >= value
    
    elif cond_type == "has_tag":
        entity = src if condition.get("on_self", False) else tgt
        return condition.get("tag") in entity.tags
    
    elif cond_type == "random":
        chance = float(condition.get("chance", 0.5))
        return b.rng.random() <= chance
    
    return False


@register("if_has_status")
def eff_if_has_status(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Exécute un effet si la cible a un statut. Params: status_code (REQUIS), effect (REQUIS), check_self (optionnel)"""
    if not _require_param(b, "if_has_status", p, "status_code"): return
    if not _require_param(b, "if_has_status", p, "effect"): return
    
    status_code = p["status_code"]
    check_self = bool(p.get("check_self", False))
    effect = p["effect"]
    
    entity = src if check_self else tgt
    
    if status_code in entity.statuses:
        opcode = effect.get("opcode")
        params = effect.get("params", {})
        if opcode in REGISTRY:
            REGISTRY[opcode](b, src, tgt, params)


@register("if_hp_threshold")
def eff_if_hp_threshold(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Exécute un effet selon un seuil de PV. Params: threshold (REQUIS), effect (REQUIS), below (optionnel), check_self (optionnel)"""
    if not _require_param(b, "if_hp_threshold", p, "threshold"): return
    if not _require_param(b, "if_hp_threshold", p, "effect"): return
    
    threshold = float(p["threshold"])
    below = bool(p.get("below", True))
    check_self = bool(p.get("check_self", False))
    effect = p["effect"]
    
    entity = src if check_self else tgt
    hp_percent = entity.stats.HP / entity.stats.MAX_HP
    
    condition_met = (hp_percent <= threshold) if below else (hp_percent > threshold)
    
    if condition_met:
        opcode = effect.get("opcode")
        params = effect.get("params", {})
        if opcode in REGISTRY:
            REGISTRY[opcode](b, src, tgt, params)


@register("chain_effects")
def eff_chain_effects(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Exécute une chaîne d'effets. Params: effects (REQUIS - liste d'effets)"""
    if not _require_param(b, "chain_effects", p, "effects"): return
    
    effects = p["effects"]
    for effect in effects:
        opcode = effect.get("opcode")
        params = effect.get("params", {})
        if opcode in REGISTRY:
            REGISTRY[opcode](b, src, tgt, params)
