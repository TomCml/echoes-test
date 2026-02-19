"""Echo gauge opcodes - Gestion de la jauge Echo.

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


@register("build_echo")
def eff_build_echo(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Génère de l'Echo pour le prochain Echo Skill. Params: amount (REQUIS), max (REQUIS)"""
    if not _require_param(b, "build_echo", p, "amount"): return
    if not _require_param(b, "build_echo", p, "max"): return
    
    amount = int(p["amount"])
    max_echo = int(p["max"])
    
    current = src.gauges.get("echo", 0)
    new_value = min(max_echo, current + amount)
    src.gauges["echo"] = new_value
    
    b.log.append(f"{src.name} gains {amount} Echo ({new_value}/{max_echo}).")


@register("consume_echo")
def eff_consume_echo(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Consomme l'Echo pour l'Echo Skill. Params: cost (REQUIS)"""
    if not _require_param(b, "consume_echo", p, "cost"): return
    
    cost = int(p["cost"])
    current = src.gauges.get("echo", 0)
    
    if current < cost:
        b.log.append(f"{src.name} doesn't have enough Echo ({current}/{cost}).")
        return False
    
    src.gauges["echo"] = current - cost
    b.log.append(f"{src.name} consumes {cost} Echo ({src.gauges['echo']} remaining).")
    return True


@register("echo_scaling_damage")
def eff_echo_scaling_damage(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Dégâts qui scale avec l'Echo accumulé. 
    Params: base (REQUIS), ratio (REQUIS), ratio_stat (REQUIS), echo_scaling (REQUIS), damage_type (REQUIS)
    """
    if not _require_param(b, "echo_scaling_damage", p, "base"): return
    if not _require_param(b, "echo_scaling_damage", p, "ratio"): return
    if not _require_param(b, "echo_scaling_damage", p, "ratio_stat"): return
    if not _require_param(b, "echo_scaling_damage", p, "echo_scaling"): return
    if not _require_param(b, "echo_scaling_damage", p, "damage_type"): return
    
    import math
    
    base = float(p["base"])
    ratio = float(p["ratio"])
    ratio_stat = p["ratio_stat"]
    echo_scaling = float(p["echo_scaling"])
    
    stat_value = src.stats.AD if ratio_stat == "AD" else src.stats.AP
    amount = base + stat_value * ratio
    
    echo = src.gauges.get("echo", 0)
    amount *= (1 + echo_scaling * echo)
    
    damage_type = p["damage_type"]
    label = p.get("label", f"Echo Skill (x{echo})")
    
    if damage_type == "physical":
        resistance = tgt.stats.ARMOR
    else:
        resistance = tgt.stats.MR
    
    if resistance > 0:
        amount *= math.exp(-resistance / 448.6)
    
    from app.engine.combat import apply_damage
    apply_damage(b, tgt, amount, label)


@register("reset_echo")
def eff_reset_echo(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Reset l'Echo à 0. Params: aucun requis"""
    old = src.gauges.get("echo", 0)
    src.gauges["echo"] = 0
    b.log.append(f"{src.name}'s Echo reset ({old} -> 0).")


@register("echo_bonus_effect")
def eff_echo_bonus_effect(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Active un effet bonus si assez d'Echo. Params: threshold (REQUIS), bonus_opcode (REQUIS), bonus_params (REQUIS)"""
    if not _require_param(b, "echo_bonus_effect", p, "threshold"): return
    if not _require_param(b, "echo_bonus_effect", p, "bonus_opcode"): return
    if not _require_param(b, "echo_bonus_effect", p, "bonus_params"): return
    
    threshold = int(p["threshold"])
    bonus_opcode = p["bonus_opcode"]
    bonus_params = p["bonus_params"]
    
    current = src.gauges.get("echo", 0)
    if current >= threshold:
        b.log.append(f"Echo threshold reached ({current}/{threshold})! Bonus activated.")
        
        from app.engine.combat import REGISTRY
        if bonus_opcode in REGISTRY:
            REGISTRY[bonus_opcode](b, src, tgt, bonus_params)
    else:
        b.log.append(f"Echo below threshold ({current}/{threshold}).")
