"""Magical damage opcodes - Dégâts magiques avec mitigation par MR.

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


def _mitigation_mr(raw: float, mr: float) -> float:
    """Réduction exponentielle par la MR."""
    if mr <= 0:
        return raw
    mult = math.exp(-mr / 448.6)
    return raw * mult


def _check_crit(b: Battle, src: Entity, can_crit: bool) -> tuple[float, bool]:
    if can_crit and b.rng.random() < src.stats.CRIT_CHANCE:
        return src.stats.CRIT_DAMAGE, True
    return 1.0, False


@register("magical_damage")
def eff_magical_damage(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Inflige des dégâts magiques (mitigés par la MR).
    
    Params: formula (REQUIS), can_crit (REQUIS), label (REQUIS)
    Optionnel: variance, magic_pen_pct, flat_magic_pen
    """
    if not _require_param(b, "magical_damage", p, "formula"): return
    if not _require_param(b, "magical_damage", p, "can_crit"): return
    if not _require_param(b, "magical_damage", p, "label"): return
    
    base = eval_formula(p["formula"], src, tgt)
    
    variance = float(p.get("variance", 0.0))
    roll = 1.0 + (b.rng.random() * 2 - 1) * variance
    amount = base * roll
    
    can_crit = bool(p["can_crit"])
    label = p["label"]
    crit_mult, is_crit = _check_crit(b, src, can_crit)
    amount *= crit_mult
    if is_crit:
        label += " (crit)"
    
    mr = tgt.stats.MR
    magic_pen_pct = float(p.get("magic_pen_pct", 0))
    flat_magic_pen = float(p.get("flat_magic_pen", 0))
    
    effective_mr = mr * (1 - magic_pen_pct) - flat_magic_pen
    effective_mr = max(0, effective_mr)
    
    amount = _mitigation_mr(amount, effective_mr)
    apply_damage(b, tgt, amount, label)


@register("magical_damage_ap_ratio")
def eff_magical_damage_ap_ratio(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Dégâts magiques avec ratio AP simplifié.
    
    Params: base (REQUIS), ap_ratio (REQUIS), can_crit (REQUIS), label (REQUIS)
    """
    if not _require_param(b, "magical_damage_ap_ratio", p, "base"): return
    if not _require_param(b, "magical_damage_ap_ratio", p, "ap_ratio"): return
    if not _require_param(b, "magical_damage_ap_ratio", p, "can_crit"): return
    if not _require_param(b, "magical_damage_ap_ratio", p, "label"): return
    
    base_dmg = float(p["base"])
    ap_ratio = float(p["ap_ratio"])
    
    amount = base_dmg + src.stats.AP * ap_ratio
    
    can_crit = bool(p["can_crit"])
    label = p["label"]
    crit_mult, is_crit = _check_crit(b, src, can_crit)
    amount *= crit_mult
    if is_crit:
        label += " (crit)"
    
    amount = _mitigation_mr(amount, tgt.stats.MR)
    apply_damage(b, tgt, amount, label)


@register("magical_damage_speed_ratio")
def eff_magical_damage_speed_ratio(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Dégâts magiques avec ratio vitesse + AP.
    
    Params: base (REQUIS), speed_ratio (REQUIS), ap_ratio (REQUIS), can_crit (REQUIS), label (REQUIS)
    """
    if not _require_param(b, "magical_damage_speed_ratio", p, "base"): return
    if not _require_param(b, "magical_damage_speed_ratio", p, "speed_ratio"): return
    if not _require_param(b, "magical_damage_speed_ratio", p, "ap_ratio"): return
    if not _require_param(b, "magical_damage_speed_ratio", p, "can_crit"): return
    if not _require_param(b, "magical_damage_speed_ratio", p, "label"): return
    
    base_dmg = float(p["base"])
    speed_ratio = float(p["speed_ratio"])
    ap_ratio = float(p["ap_ratio"])
    
    amount = base_dmg + src.stats.SPEED * speed_ratio + src.stats.AP * ap_ratio
    
    can_crit = bool(p["can_crit"])
    label = p["label"]
    crit_mult, is_crit = _check_crit(b, src, can_crit)
    amount *= crit_mult
    if is_crit:
        label += " (crit)"
    
    amount = _mitigation_mr(amount, tgt.stats.MR)
    apply_damage(b, tgt, amount, label)
