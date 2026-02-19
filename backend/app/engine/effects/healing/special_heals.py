"""Special heals opcodes - Soins spéciaux.

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


@register("revive")
def eff_revive(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Ressuscite une cible morte. Params: hp_percent (REQUIS)"""
    if not _require_param(b, "revive", p, "hp_percent"): return
    
    hp_percent = float(p["hp_percent"])
    
    if tgt.stats.HP > 0:
        b.log.append(f"{tgt.name} is not dead.")
        return
    
    tgt.stats.HP = int(tgt.stats.MAX_HP * hp_percent)
    b.log.append(f"{tgt.name} revived at {int(hp_percent*100)}% HP ({tgt.stats.HP})!")


@register("heal_on_kill")
def eff_heal_on_kill(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Soin lors d'un kill. Params: percent (REQUIS)"""
    if not _require_param(b, "heal_on_kill", p, "percent"): return
    
    if tgt.stats.HP > 0:
        return
    
    percent = float(p["percent"])
    heal = src.stats.MAX_HP * percent
    
    old_hp = src.stats.HP
    src.stats.HP = min(src.stats.MAX_HP, src.stats.HP + int(heal))
    actual_heal = src.stats.HP - old_hp
    
    b.log.append(f"{src.name} heals {actual_heal} on kill ({int(percent*100)}% max HP).")


@register("meditation_heal")
def eff_meditation_heal(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Soin de Méditation (chaque tour si buff actif).
    
    Params: hp_percent_per_stack (REQUIS), ap_ratio_per_stack (REQUIS)
    """
    if not _require_param(b, "meditation_heal", p, "hp_percent_per_stack"): return
    if not _require_param(b, "meditation_heal", p, "ap_ratio_per_stack"): return
    
    meditation = tgt.statuses.get("meditation")
    if not meditation:
        return
    
    hp_pct = float(p["hp_percent_per_stack"])
    ap_ratio = float(p["ap_ratio_per_stack"])
    stacks = meditation.get("stacks", 0)
    
    # Formule: (0.6% PV max + 0.8×AP) par stack
    heal_per_stack = tgt.stats.MAX_HP * hp_pct + tgt.stats.AP * ap_ratio
    total_heal = heal_per_stack * stacks
    
    old_hp = tgt.stats.HP
    tgt.stats.HP = min(tgt.stats.MAX_HP, tgt.stats.HP + int(total_heal))
    actual_heal = tgt.stats.HP - old_hp
    
    b.log.append(f"{tgt.name} meditates for {actual_heal} HP ({stacks} stacks).")
    
    meditation["remaining"] -= 1
    if meditation["remaining"] <= 0:
        del tgt.statuses["meditation"]
        b.log.append(f"{tgt.name}'s meditation ends.")
