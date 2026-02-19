"""Physical damage opcodes - Dégâts physiques avec mitigation par armure.

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


def _mitigation_armor(raw: float, armor: float) -> float:
    """Réduction exponentielle par l'armure."""
    if armor <= 0:
        return raw
    mult = math.exp(-armor / 448.6)
    return raw * mult


def _check_crit(b: Battle, src: Entity, can_crit: bool) -> tuple[float, bool]:
    """Check if attack crits and return multiplier."""
    if can_crit and b.rng.random() < src.stats.CRIT_CHANCE:
        return src.stats.CRIT_DAMAGE, True
    return 1.0, False


@register("physical_damage")
def eff_physical_damage(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Inflige des dégâts physiques (mitigés par l'armure).
    
    Params: formula (REQUIS), can_crit (REQUIS), label (REQUIS)
    Optionnel: variance, armor_pen_pct, lethality
    """
    if not _require_param(b, "physical_damage", p, "formula"): return
    if not _require_param(b, "physical_damage", p, "can_crit"): return
    if not _require_param(b, "physical_damage", p, "label"): return
    
    base = eval_formula(p["formula"], src, tgt)
    
    # Variance (optionnel, 0 si non spécifié)
    variance = float(p.get("variance", 0.0))
    roll = 1.0 + (b.rng.random() * 2 - 1) * variance
    amount = base * roll
    
    # Crit
    can_crit = bool(p["can_crit"])
    label = p["label"]
    crit_mult, is_crit = _check_crit(b, src, can_crit)
    amount *= crit_mult
    if is_crit:
        label += " (crit)"
    
    # Armor penetration (optionnel)
    armor = tgt.stats.ARMOR
    armor_pen_pct = float(p.get("armor_pen_pct", 0))
    lethality = float(p.get("lethality", 0))
    
    effective_armor = armor * (1 - armor_pen_pct) - lethality
    effective_armor = max(0, effective_armor)
    
    amount = _mitigation_armor(amount, effective_armor)
    apply_damage(b, tgt, amount, label)


@register("physical_damage_ad_ratio")
def eff_physical_damage_ad_ratio(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Dégâts physiques avec ratio AD simplifié.
    
    Params: base (REQUIS), ad_ratio (REQUIS), can_crit (REQUIS), label (REQUIS)
    """
    if not _require_param(b, "physical_damage_ad_ratio", p, "base"): return
    if not _require_param(b, "physical_damage_ad_ratio", p, "ad_ratio"): return
    if not _require_param(b, "physical_damage_ad_ratio", p, "can_crit"): return
    if not _require_param(b, "physical_damage_ad_ratio", p, "label"): return
    
    base_dmg = float(p["base"])
    ad_ratio = float(p["ad_ratio"])
    
    amount = base_dmg + src.stats.AD * ad_ratio
    
    can_crit = bool(p["can_crit"])
    label = p["label"]
    crit_mult, is_crit = _check_crit(b, src, can_crit)
    amount *= crit_mult
    if is_crit:
        label += " (crit)"
    
    amount = _mitigation_armor(amount, tgt.stats.ARMOR)
    apply_damage(b, tgt, amount, label)


@register("basic_attack")
def eff_basic_attack(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Attaque de base standard.
    
    Params: ad_ratio (REQUIS), can_crit (REQUIS)
    """
    if not _require_param(b, "basic_attack", p, "ad_ratio"): return
    if not _require_param(b, "basic_attack", p, "can_crit"): return
    
    ad_ratio = float(p["ad_ratio"])
    amount = src.stats.AD * ad_ratio
    
    can_crit = bool(p["can_crit"])
    label = "basic attack"
    crit_mult, is_crit = _check_crit(b, src, can_crit)
    amount *= crit_mult
    if is_crit:
        label += " (crit)"
    
    amount = _mitigation_armor(amount, tgt.stats.ARMOR)
    apply_damage(b, tgt, amount, label)
    
    b.log.append(f"{src.name} uses basic attack.")
