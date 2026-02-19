"""On-hit triggers - Déclencheurs lors d'attaques.

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


@register("on_basic_attack")
def eff_on_basic_attack(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Déclenche des effets lors d'une attaque de base. Params: effects (REQUIS - liste d'effets)"""
    if not _require_param(b, "on_basic_attack", p, "effects"): return
    
    effects = p["effects"]
    for effect in effects:
        opcode = effect.get("opcode")
        params = effect.get("params", {})
        if opcode in REGISTRY:
            REGISTRY[opcode](b, src, tgt, params)


@register("on_crit")
def eff_on_crit(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Déclenche des effets lors d'un critique. Params: effects (REQUIS - liste d'effets)"""
    if not _require_param(b, "on_crit", p, "effects"): return
    
    effects = p["effects"]
    for effect in effects:
        opcode = effect.get("opcode")
        params = effect.get("params", {})
        if opcode in REGISTRY:
            REGISTRY[opcode](b, src, tgt, params)


@register("on_hit_proc")
def eff_on_hit_proc(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Proc d'on-hit avec chance. Params: chance (REQUIS), effect_opcode (REQUIS), effect_params (REQUIS)"""
    if not _require_param(b, "on_hit_proc", p, "chance"): return
    if not _require_param(b, "on_hit_proc", p, "effect_opcode"): return
    if not _require_param(b, "on_hit_proc", p, "effect_params"): return
    
    chance = float(p["chance"])
    effect_opcode = p["effect_opcode"]
    effect_params = p["effect_params"]
    
    if b.rng.random() <= chance:
        if effect_opcode in REGISTRY:
            REGISTRY[effect_opcode](b, src, tgt, effect_params)
            b.log.append(f"On-hit proc triggered!")
    else:
        b.log.append(f"On-hit proc failed ({int(chance*100)}% chance).")


@register("multi_on_hit")
def eff_multi_on_hit(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique plusieurs effets on-hit. Params: on_hit_effects (REQUIS - liste d'effets)"""
    if not _require_param(b, "multi_on_hit", p, "on_hit_effects"): return
    
    on_hit_effects = p["on_hit_effects"]
    for effect in on_hit_effects:
        opcode = effect.get("opcode")
        params = effect.get("params", {})
        if opcode in REGISTRY:
            REGISTRY[opcode](b, src, tgt, params)


@register("bonus_damage_if_target_has_status")
def eff_bonus_damage_if_status(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Dégâts bonus si la cible a un statut. Params: status_code (REQUIS), bonus_pct (REQUIS)"""
    if not _require_param(b, "bonus_damage_if_target_has_status", p, "status_code"): return
    if not _require_param(b, "bonus_damage_if_target_has_status", p, "bonus_pct"): return
    
    status_code = p["status_code"]
    bonus_pct = float(p["bonus_pct"])
    
    if status_code in tgt.statuses:
        extra = src.stats.AD * bonus_pct
        from app.engine.combat import apply_damage
        apply_damage(b, tgt, extra, f"bonus {int(bonus_pct*100)}% ({status_code})")
