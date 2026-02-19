"""Adaptive damage opcodes - Dégâts adaptatifs AD/AP.

IMPORTANT: Tous les paramètres doivent être fournis par les items JSON.
"""
import math
from typing import Dict, Any
from app.engine.combat import register, eval_formula, apply_damage
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


def _check_crit(b: Battle, src: Entity, can_crit: bool) -> tuple[float, bool]:
    if can_crit and b.rng.random() < src.stats.CRIT_CHANCE:
        return src.stats.CRIT_DAMAGE, True
    return 1.0, False


@register("adaptive_damage")
def eff_adaptive_damage(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Dégâts adaptatifs (utilise AD ou AP selon le plus élevé).
    
    Params: base (REQUIS), adaptive_ratio (REQUIS), can_crit (REQUIS), label (REQUIS)
    Optionnel: formula (utilise formula au lieu de base si fourni)
    """
    if not _require_param(b, "adaptive_damage", p, "base"): return
    if not _require_param(b, "adaptive_damage", p, "adaptive_ratio"): return
    if not _require_param(b, "adaptive_damage", p, "can_crit"): return
    if not _require_param(b, "adaptive_damage", p, "label"): return
    
    if "formula" in p:
        base = eval_formula(p["formula"], src, tgt)
    else:
        base = float(p["base"])
    
    adaptive_ratio = float(p["adaptive_ratio"])
    can_crit = bool(p["can_crit"])
    label = p["label"]
    
    if src.stats.AD >= src.stats.AP:
        stat_value = src.stats.AD
        damage_type = "physical"
    else:
        stat_value = src.stats.AP
        damage_type = "magical"
    
    amount = base + stat_value * adaptive_ratio
    
    crit_mult, is_crit = _check_crit(b, src, can_crit)
    amount *= crit_mult
    if is_crit:
        label += " (crit)"
    
    if damage_type == "physical":
        amount = _mitigation(amount, tgt.stats.ARMOR)
    else:
        amount = _mitigation(amount, tgt.stats.MR)
    
    apply_damage(b, tgt, amount, label)


@register("adaptive_damage_scaling")
def eff_adaptive_damage_scaling(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Dégâts adaptatifs avec scaling selon buffs/debuffs.
    
    Params: base (REQUIS), adaptive_ratio (REQUIS), scale_per_debuff (REQUIS), 
            scale_per_buff (REQUIS), label (REQUIS)
    """
    if not _require_param(b, "adaptive_damage_scaling", p, "base"): return
    if not _require_param(b, "adaptive_damage_scaling", p, "adaptive_ratio"): return
    if not _require_param(b, "adaptive_damage_scaling", p, "scale_per_debuff"): return
    if not _require_param(b, "adaptive_damage_scaling", p, "scale_per_buff"): return
    if not _require_param(b, "adaptive_damage_scaling", p, "label"): return
    
    base = float(p["base"])
    adaptive_ratio = float(p["adaptive_ratio"])
    scale_per_debuff = float(p["scale_per_debuff"])
    scale_per_buff = float(p["scale_per_buff"])
    label = p["label"]
    
    if src.stats.AD >= src.stats.AP:
        stat_value = src.stats.AD
        damage_type = "physical"
    else:
        stat_value = src.stats.AP
        damage_type = "magical"
    
    amount = base + stat_value * adaptive_ratio
    
    # Bonus par debuff sur la cible
    debuff_count = len([s for s in tgt.statuses.keys() if s in [
        "burn", "laceration", "fatigue", "slow", "vulnerability", "antiheal",
        "armor_reduction", "mr_reduction", "exposed"
    ]])
    
    # Bonus par buff sur soi
    buff_count = len([s for s in src.statuses.keys() if s in [
        "puissance", "haste", "rythme", "mur", "focus", "concentration", "volonte"
    ]])
    
    bonus = 1 + (debuff_count * scale_per_debuff) + (buff_count * scale_per_buff)
    amount *= bonus
    
    if damage_type == "physical":
        amount = _mitigation(amount, tgt.stats.ARMOR)
    else:
        amount = _mitigation(amount, tgt.stats.MR)
    
    apply_damage(b, tgt, amount, label)
