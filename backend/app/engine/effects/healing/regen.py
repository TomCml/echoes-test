"""Regen opcodes - Régénération.

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


@register("apply_regen")
def eff_apply_regen(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique buff Régénération. Params: duration (REQUIS), stacks (REQUIS)"""
    if not _require_param(b, "apply_regen", p, "duration"): return
    if not _require_param(b, "apply_regen", p, "stacks"): return
    
    duration = int(p["duration"])
    stacks = int(p["stacks"])
    
    current = tgt.statuses.get("regeneration", {"stacks": 0, "remaining": 0})
    new_stacks = current["stacks"] + stacks
    tgt.statuses["regeneration"] = {
        "stacks": new_stacks,
        "remaining": max(current["remaining"], duration)
    }
    b.log.append(f"{tgt.name} gains regeneration ({new_stacks} stacks, {duration}t).")


@register("tick_regen")
def eff_tick_regen(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Applique le soin de régénération (appelé chaque tour).
    
    Params: hp_percent_per_stack (REQUIS), ap_ratio_per_stack (REQUIS)
    """
    if not _require_param(b, "tick_regen", p, "hp_percent_per_stack"): return
    if not _require_param(b, "tick_regen", p, "ap_ratio_per_stack"): return
    
    regen = tgt.statuses.get("regeneration")
    if not regen:
        return
    
    hp_pct = float(p["hp_percent_per_stack"])
    ap_ratio = float(p["ap_ratio_per_stack"])
    stacks = regen.get("stacks", 0)
    
    # Formule: (0.45% PV max + 0.5×AP) par stack
    heal_per_stack = tgt.stats.MAX_HP * hp_pct + tgt.stats.AP * ap_ratio
    total_heal = heal_per_stack * stacks
    
    old_hp = tgt.stats.HP
    tgt.stats.HP = min(tgt.stats.MAX_HP, tgt.stats.HP + int(total_heal))
    actual_heal = tgt.stats.HP - old_hp
    
    b.log.append(f"{tgt.name} regenerates {actual_heal} ({stacks} stacks).")
    
    regen["remaining"] -= 1
    if regen["remaining"] <= 0:
        del tgt.statuses["regeneration"]
        b.log.append(f"{tgt.name}'s regeneration fades.")


@register("hp_per_turn")
def eff_hp_per_turn(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Soin fixe par tour. Params: amount (REQUIS)"""
    if not _require_param(b, "hp_per_turn", p, "amount"): return
    
    amount = float(p["amount"])
    
    old_hp = tgt.stats.HP
    tgt.stats.HP = min(tgt.stats.MAX_HP, tgt.stats.HP + int(amount))
    actual_heal = tgt.stats.HP - old_hp
    
    b.log.append(f"{tgt.name} gains {actual_heal} HP (per turn effect).")
