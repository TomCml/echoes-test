"""Multi-hit damage opcodes - Attaques multi-coups.

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


def _check_crit(b: Battle, src: Entity, can_crit: bool) -> tuple[float, bool]:
    if can_crit and b.rng.random() < src.stats.CRIT_CHANCE:
        return src.stats.CRIT_DAMAGE, True
    return 1.0, False


@register("multi_basic_attack")
def eff_multi_basic_attack(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Plusieurs attaques de base successives.
    
    Params: hits (REQUIS), ad_ratio (REQUIS), can_crit (REQUIS)
    """
    if not _require_param(b, "multi_basic_attack", p, "hits"): return
    if not _require_param(b, "multi_basic_attack", p, "ad_ratio"): return
    if not _require_param(b, "multi_basic_attack", p, "can_crit"): return
    
    hits = int(p["hits"])
    ad_ratio = float(p["ad_ratio"])
    can_crit = bool(p["can_crit"])
    
    for i in range(hits):
        amount = src.stats.AD * ad_ratio
        label = f"multi-attack {i+1}/{hits}"
        
        crit_mult, is_crit = _check_crit(b, src, can_crit)
        amount *= crit_mult
        if is_crit:
            label += " (crit)"
        
        amount = _mitigation(amount, tgt.stats.ARMOR)
        apply_damage(b, tgt, amount, label)


@register("multi_hit_spell")
def eff_multi_hit_spell(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Sort avec plusieurs projectiles/coups.
    
    Params: hits (REQUIS), base_per_hit (REQUIS), ratio_per_hit (REQUIS), 
            ratio_stat (REQUIS), damage_type (REQUIS), label (REQUIS)
    """
    if not _require_param(b, "multi_hit_spell", p, "hits"): return
    if not _require_param(b, "multi_hit_spell", p, "base_per_hit"): return
    if not _require_param(b, "multi_hit_spell", p, "ratio_per_hit"): return
    if not _require_param(b, "multi_hit_spell", p, "ratio_stat"): return
    if not _require_param(b, "multi_hit_spell", p, "damage_type"): return
    if not _require_param(b, "multi_hit_spell", p, "label"): return
    
    hits = int(p["hits"])
    base_per_hit = float(p["base_per_hit"])
    ratio_per_hit = float(p["ratio_per_hit"])
    ratio_stat = p["ratio_stat"]
    damage_type = p["damage_type"]
    base_label = p["label"]
    
    stat_value = src.stats.AD if ratio_stat == "AD" else src.stats.AP
    
    for i in range(hits):
        amount = base_per_hit + stat_value * ratio_per_hit
        label = f"{base_label} {i+1}/{hits}"
        
        if damage_type == "physical":
            amount = _mitigation(amount, tgt.stats.ARMOR)
        elif damage_type == "magical":
            amount = _mitigation(amount, tgt.stats.MR)
        
        apply_damage(b, tgt, amount, label)
