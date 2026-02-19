"""True damage opcodes - Dégâts bruts ignoring résistances.

IMPORTANT: Tous les paramètres doivent être fournis par les items JSON.
"""
from typing import Dict, Any
from app.engine.combat import register, eval_formula, apply_damage
from app.engine.domain import Battle, Entity


def _require_param(b: Battle, opcode: str, p: Dict, key: str) -> bool:
    if key not in p:
        b.log.append(f"[WARN] {opcode}: '{key}' param missing")
        return False
    return True


def _check_crit(b: Battle, src: Entity, can_crit: bool) -> tuple[float, bool]:
    if can_crit and b.rng.random() < src.stats.CRIT_CHANCE:
        return src.stats.CRIT_DAMAGE, True
    return 1.0, False


@register("true_damage")
def eff_true_damage(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Inflige des dégâts bruts (ignorent les résistances).
    
    Params: formula (REQUIS), can_crit (REQUIS), label (REQUIS)
    """
    if not _require_param(b, "true_damage", p, "formula"): return
    if not _require_param(b, "true_damage", p, "can_crit"): return
    if not _require_param(b, "true_damage", p, "label"): return
    
    amount = eval_formula(p["formula"], src, tgt)
    
    can_crit = bool(p["can_crit"])
    label = p["label"]
    crit_mult, is_crit = _check_crit(b, src, can_crit)
    amount *= crit_mult
    if is_crit:
        label += " (crit)"
    
    apply_damage(b, tgt, amount, label)


@register("true_damage_flat")
def eff_true_damage_flat(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Dégâts bruts fixes.
    
    Params: amount (REQUIS), label (REQUIS)
    """
    if not _require_param(b, "true_damage_flat", p, "amount"): return
    if not _require_param(b, "true_damage_flat", p, "label"): return
    
    amount = int(p["amount"])
    label = p["label"]
    apply_damage(b, tgt, amount, label)


@register("self_true_damage")
def eff_self_true_damage(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Auto-dégâts bruts (coûts de vie).
    
    Params: formula (REQUIS), label (REQUIS)
    """
    if not _require_param(b, "self_true_damage", p, "formula"): return
    if not _require_param(b, "self_true_damage", p, "label"): return
    
    amount = eval_formula(p["formula"], src, src)
    label = p["label"]
    apply_damage(b, src, amount, label)


@register("destroy_shield_then_damage")
def eff_destroy_shield_then_damage(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Détruit le bouclier puis inflige des dégâts % PV.
    
    Params: hp_percent (REQUIS), label (REQUIS)
    """
    if not _require_param(b, "destroy_shield_then_damage", p, "hp_percent"): return
    if not _require_param(b, "destroy_shield_then_damage", p, "label"): return
    
    # Destroy shields first
    shield = tgt.gauges.get("shield", 0)
    magic_shield = tgt.gauges.get("magic_shield", 0)
    tgt.gauges["shield"] = 0
    tgt.gauges["magic_shield"] = 0
    if shield + magic_shield > 0:
        b.log.append(f"{tgt.name}'s shields destroyed ({shield + magic_shield})!")
    
    hp_percent = float(p["hp_percent"])
    amount = tgt.stats.MAX_HP * hp_percent
    label = p["label"]
    apply_damage(b, tgt, amount, label)
