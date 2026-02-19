"""Execute damage opcodes - Dégâts d'exécution.

IMPORTANT: Tous les paramètres doivent être fournis par les items JSON.
"""
import math
from typing import Dict, Any
from app.engine.combat import register, apply_damage
from app.engine.domain import Battle, Entity


def _require_param(b: Battle, opcode: str, p: Dict, key: str) -> bool:
    if key not in p:
        b.log.append(f"[WARN] {opcode}: '{key}' param missing")
        return False
    return True


def _mitigation(raw: float, resistance: float) -> float:
    if resistance <= 0:
        return raw
    return raw * math.exp(-resistance / 448.6)


@register("execute_damage")
def eff_execute_damage(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Dégâts augmentés en fonction des PV manquants.
    
    Params: base (REQUIS), ratio (REQUIS), ratio_stat (REQUIS), 
            max_bonus (REQUIS), damage_type (REQUIS), label (REQUIS)
    """
    if not _require_param(b, "execute_damage", p, "base"): return
    if not _require_param(b, "execute_damage", p, "ratio"): return
    if not _require_param(b, "execute_damage", p, "ratio_stat"): return
    if not _require_param(b, "execute_damage", p, "max_bonus"): return
    if not _require_param(b, "execute_damage", p, "damage_type"): return
    if not _require_param(b, "execute_damage", p, "label"): return
    
    base = float(p["base"])
    ratio = float(p["ratio"])
    ratio_stat = p["ratio_stat"]
    max_bonus = float(p["max_bonus"])
    damage_type = p["damage_type"]
    label = p["label"]
    
    stat_value = src.stats.AD if ratio_stat == "AD" else src.stats.AP
    amount = base + stat_value * ratio
    
    # Execute bonus: more damage vs low HP targets
    hp_percent = tgt.stats.HP / tgt.stats.MAX_HP
    missing_hp_percent = 1 - hp_percent
    bonus_mult = 1 + (max_bonus * missing_hp_percent)
    amount *= bonus_mult
    
    if damage_type == "physical":
        amount = _mitigation(amount, tgt.stats.ARMOR)
    elif damage_type == "magical":
        amount = _mitigation(amount, tgt.stats.MR)
    
    apply_damage(b, tgt, amount, label)


@register("kill_threshold")
def eff_kill_threshold(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Tue instantanément si la cible est sous un seuil de PV.
    
    Params: threshold (REQUIS)
    """
    if not _require_param(b, "kill_threshold", p, "threshold"): return
    
    threshold_percent = float(p["threshold"])
    
    hp_percent = tgt.stats.HP / tgt.stats.MAX_HP
    if hp_percent <= threshold_percent:
        tgt.stats.HP = 0
        b.log.append(f"{tgt.name} executed at {int(hp_percent*100)}% HP!")
    else:
        b.log.append(f"{tgt.name} above execution threshold ({int(hp_percent*100)}% > {int(threshold_percent*100)}%).")
