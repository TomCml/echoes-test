"""Burn damage opcodes - Dégâts de brûlure (DoT).

IMPORTANT: Tous les paramètres doivent être fournis par les items JSON.
"""
from typing import Dict, Any
from app.engine.combat import register, apply_damage
from app.engine.domain import Battle, Entity


def _require_param(b: Battle, opcode: str, p: Dict, key: str) -> bool:
    if key not in p:
        b.log.append(f"[WARN] {opcode}: '{key}' param missing")
        return False
    return True


@register("apply_burn")
def eff_apply_burn(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Applique des stacks de brûlure.
    
    Params: stacks (REQUIS), duration (REQUIS)
    """
    if not _require_param(b, "apply_burn", p, "stacks"): return
    if not _require_param(b, "apply_burn", p, "duration"): return
    
    stacks = int(p["stacks"])
    duration = int(p["duration"])
    
    current = tgt.statuses.get("burn", {"stacks": 0, "remaining": 0})
    new_stacks = current["stacks"] + stacks
    tgt.statuses["burn"] = {
        "stacks": new_stacks, 
        "remaining": max(current["remaining"], duration),
        "source_ad": src.stats.AD,
        "source_ap": src.stats.AP,
        "source_max_hp": src.stats.MAX_HP
    }
    b.log.append(f"{tgt.name} gains {stacks} burn stacks (total {new_stacks}).")


@register("tick_burn_damage")
def eff_tick_burn_damage(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Applique les dégâts de brûlure (appelé chaque tour).
    
    Params: hp_percent_per_stack (REQUIS), ad_ratio_per_stack (REQUIS), 
            ap_ratio_per_stack (REQUIS), max_hp_ratio_per_stack (REQUIS)
    """
    if not _require_param(b, "tick_burn_damage", p, "hp_percent_per_stack"): return
    if not _require_param(b, "tick_burn_damage", p, "ad_ratio_per_stack"): return
    if not _require_param(b, "tick_burn_damage", p, "ap_ratio_per_stack"): return
    if not _require_param(b, "tick_burn_damage", p, "max_hp_ratio_per_stack"): return
    
    burn = tgt.statuses.get("burn")
    if not burn:
        return
    
    stacks = burn.get("stacks", 0)
    source_ad = burn.get("source_ad", 0)
    source_ap = burn.get("source_ap", 0)
    source_max_hp = burn.get("source_max_hp", 0)
    
    hp_pct = float(p["hp_percent_per_stack"])
    ad_ratio = float(p["ad_ratio_per_stack"])
    ap_ratio = float(p["ap_ratio_per_stack"])
    max_hp_ratio = float(p["max_hp_ratio_per_stack"])
    
    # Formule: (0.3% PV_max_cible + AD*0.07 + AP*0.05 + HP_max*0.02) par stack
    damage_per_stack = (
        tgt.stats.MAX_HP * hp_pct + 
        source_ad * ad_ratio + 
        source_ap * ap_ratio + 
        source_max_hp * max_hp_ratio
    )
    total_damage = damage_per_stack * stacks
    
    apply_damage(b, tgt, total_damage, f"burn ({stacks} stacks)")
    
    burn["remaining"] -= 1
    if burn["remaining"] <= 0:
        del tgt.statuses["burn"]
        b.log.append(f"{tgt.name}'s burn fades.")


@register("double_burn_stacks")
def eff_double_burn_stacks(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Double les stacks de brûlure actuels.
    
    Params: duration (REQUIS)
    """
    if not _require_param(b, "double_burn_stacks", p, "duration"): return
    
    duration = int(p["duration"])
    burn = tgt.statuses.get("burn")
    
    if burn:
        old = burn["stacks"]
        burn["stacks"] *= 2
        burn["remaining"] = max(burn["remaining"], duration)
        b.log.append(f"{tgt.name}'s burn stacks doubled ({old} -> {burn['stacks']})!")
    else:
        b.log.append(f"{tgt.name} has no burn to double.")


@register("damage_with_burn")
def eff_damage_with_burn(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Dégâts + application de brûlure.
    
    Params: base (REQUIS), ap_ratio (REQUIS), ad_ratio (REQUIS), 
            burn_stacks (REQUIS), burn_duration (REQUIS), label (REQUIS)
    """
    if not _require_param(b, "damage_with_burn", p, "base"): return
    if not _require_param(b, "damage_with_burn", p, "ap_ratio"): return
    if not _require_param(b, "damage_with_burn", p, "ad_ratio"): return
    if not _require_param(b, "damage_with_burn", p, "burn_stacks"): return
    if not _require_param(b, "damage_with_burn", p, "burn_duration"): return
    if not _require_param(b, "damage_with_burn", p, "label"): return
    
    base = float(p["base"])
    ap_ratio = float(p["ap_ratio"])
    ad_ratio = float(p["ad_ratio"])
    burn_stacks = int(p["burn_stacks"])
    burn_duration = int(p["burn_duration"])
    label = p["label"]
    
    amount = base + src.stats.AP * ap_ratio + src.stats.AD * ad_ratio
    apply_damage(b, tgt, amount, label)
    
    # Apply burn
    eff_apply_burn(b, src, tgt, {"stacks": burn_stacks, "duration": burn_duration})
