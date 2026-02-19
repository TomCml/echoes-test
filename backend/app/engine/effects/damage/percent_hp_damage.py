"""Percent HP damage opcodes - Dégâts basés sur % PV.

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


@register("percent_max_hp_damage")
def eff_percent_max_hp_damage(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Dégâts basés sur % PV max de la cible.
    
    Params: percent (REQUIS), damage_type (REQUIS), can_crit (REQUIS), label (REQUIS)
    """
    if not _require_param(b, "percent_max_hp_damage", p, "percent"): return
    if not _require_param(b, "percent_max_hp_damage", p, "damage_type"): return
    if not _require_param(b, "percent_max_hp_damage", p, "can_crit"): return
    if not _require_param(b, "percent_max_hp_damage", p, "label"): return
    
    percent = float(p["percent"])
    damage_type = p["damage_type"]
    can_crit = bool(p["can_crit"])
    label = p["label"]
    
    amount = tgt.stats.MAX_HP * percent
    
    crit_mult, is_crit = _check_crit(b, src, can_crit)
    amount *= crit_mult
    if is_crit:
        label += " (crit)"
    
    if damage_type == "physical":
        amount = _mitigation(amount, tgt.stats.ARMOR)
    elif damage_type == "magical":
        amount = _mitigation(amount, tgt.stats.MR)
    
    apply_damage(b, tgt, amount, label)


@register("percent_current_hp_damage")
def eff_percent_current_hp_damage(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Dégâts basés sur % PV actuels de la cible.
    
    Params: percent (REQUIS), damage_type (REQUIS), can_crit (REQUIS), label (REQUIS)
    """
    if not _require_param(b, "percent_current_hp_damage", p, "percent"): return
    if not _require_param(b, "percent_current_hp_damage", p, "damage_type"): return
    if not _require_param(b, "percent_current_hp_damage", p, "can_crit"): return
    if not _require_param(b, "percent_current_hp_damage", p, "label"): return
    
    percent = float(p["percent"])
    damage_type = p["damage_type"]
    can_crit = bool(p["can_crit"])
    label = p["label"]
    
    amount = tgt.stats.HP * percent
    
    crit_mult, is_crit = _check_crit(b, src, can_crit)
    amount *= crit_mult
    if is_crit:
        label += " (crit)"
    
    if damage_type == "physical":
        amount = _mitigation(amount, tgt.stats.ARMOR)
    elif damage_type == "magical":
        amount = _mitigation(amount, tgt.stats.MR)
    
    apply_damage(b, tgt, amount, label)


@register("percent_missing_hp_damage")
def eff_percent_missing_hp_damage(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Dégâts avec bonus par PV manquants (exécution).
    
    Params: base (REQUIS), ratio (REQUIS), ratio_stat (REQUIS), missing_hp_ratio (REQUIS), 
            damage_type (REQUIS), label (REQUIS)
    """
    if not _require_param(b, "percent_missing_hp_damage", p, "base"): return
    if not _require_param(b, "percent_missing_hp_damage", p, "ratio"): return
    if not _require_param(b, "percent_missing_hp_damage", p, "ratio_stat"): return
    if not _require_param(b, "percent_missing_hp_damage", p, "missing_hp_ratio"): return
    if not _require_param(b, "percent_missing_hp_damage", p, "damage_type"): return
    if not _require_param(b, "percent_missing_hp_damage", p, "label"): return
    
    base = float(p["base"])
    ratio = float(p["ratio"])
    ratio_stat = p["ratio_stat"]
    missing_hp_ratio = float(p["missing_hp_ratio"])
    damage_type = p["damage_type"]
    label = p["label"]
    
    stat_value = src.stats.AD if ratio_stat == "AD" else src.stats.AP
    missing_hp = tgt.stats.MAX_HP - tgt.stats.HP
    
    amount = base + stat_value * ratio + missing_hp * missing_hp_ratio
    
    if damage_type == "physical":
        amount = _mitigation(amount, tgt.stats.ARMOR)
    elif damage_type == "magical":
        amount = _mitigation(amount, tgt.stats.MR)
    
    apply_damage(b, tgt, amount, label)


@register("damage_per_burn_stack")
def eff_damage_per_burn_stack(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Dégâts bonus par stack de brûlure sur la cible.
    
    Params: percent_per_stack (REQUIS), consume_stacks (REQUIS), damage_type (REQUIS), label (REQUIS)
    """
    if not _require_param(b, "damage_per_burn_stack", p, "percent_per_stack"): return
    if not _require_param(b, "damage_per_burn_stack", p, "consume_stacks"): return
    if not _require_param(b, "damage_per_burn_stack", p, "damage_type"): return
    if not _require_param(b, "damage_per_burn_stack", p, "label"): return
    
    percent_per_stack = float(p["percent_per_stack"])
    consume_stacks = bool(p["consume_stacks"])
    damage_type = p["damage_type"]
    label = p["label"]
    
    burn_status = tgt.statuses.get("burn")
    if not burn_status:
        b.log.append(f"{tgt.name} has no burn stacks.")
        return
    
    stacks = burn_status.get("stacks", 0)
    amount = tgt.stats.MAX_HP * percent_per_stack * stacks
    
    if consume_stacks:
        del tgt.statuses["burn"]
        b.log.append(f"Consumed {stacks} burn stacks.")
    
    if damage_type == "physical":
        amount = _mitigation(amount, tgt.stats.ARMOR)
    elif damage_type == "magical":
        amount = _mitigation(amount, tgt.stats.MR)
    
    apply_damage(b, tgt, amount, label)
