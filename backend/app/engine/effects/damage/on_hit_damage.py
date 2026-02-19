"""On-hit damage opcodes - Effets de dégâts on-hit.

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


@register("on_hit_damage")
def eff_on_hit_damage(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Dégâts on-hit basiques.
    
    Params: base (REQUIS), ap_ratio (REQUIS), ad_ratio (REQUIS), damage_type (REQUIS), label (REQUIS)
    """
    if not _require_param(b, "on_hit_damage", p, "base"): return
    if not _require_param(b, "on_hit_damage", p, "ap_ratio"): return
    if not _require_param(b, "on_hit_damage", p, "ad_ratio"): return
    if not _require_param(b, "on_hit_damage", p, "damage_type"): return
    if not _require_param(b, "on_hit_damage", p, "label"): return
    
    base = float(p["base"])
    ap_ratio = float(p["ap_ratio"])
    ad_ratio = float(p["ad_ratio"])
    damage_type = p["damage_type"]
    label = p["label"]
    
    amount = base + src.stats.AP * ap_ratio + src.stats.AD * ad_ratio
    
    if damage_type == "physical":
        amount = _mitigation(amount, tgt.stats.ARMOR)
    elif damage_type == "magical":
        amount = _mitigation(amount, tgt.stats.MR)
    
    apply_damage(b, tgt, amount, label)


@register("on_hit_crit_conversion")
def eff_on_hit_crit_conversion(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Convertit le crit en dégâts on-hit (Guinsoo's Rageblade).
    
    Params: conversion_rate (REQUIS), label (REQUIS)
    """
    if not _require_param(b, "on_hit_crit_conversion", p, "conversion_rate"): return
    if not _require_param(b, "on_hit_crit_conversion", p, "label"): return
    
    conversion_rate = float(p["conversion_rate"])
    label = p["label"]
    
    crit_chance = src.stats.CRIT_CHANCE
    on_hit_dmg = src.stats.AD * crit_chance * conversion_rate
    
    amount = _mitigation(on_hit_dmg, tgt.stats.ARMOR)
    apply_damage(b, tgt, amount, label)


@register("on_hit_percent_hp")
def eff_on_hit_percent_hp(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    On-hit % PV max de la cible (BotRK, Recurve).
    
    Params: percent (REQUIS), damage_type (REQUIS), label (REQUIS), bonus_if_debuff (optionnel)
    """
    if not _require_param(b, "on_hit_percent_hp", p, "percent"): return
    if not _require_param(b, "on_hit_percent_hp", p, "damage_type"): return
    if not _require_param(b, "on_hit_percent_hp", p, "label"): return
    
    percent = float(p["percent"])
    damage_type = p["damage_type"]
    label = p["label"]
    bonus_if_debuff = float(p.get("bonus_if_debuff", 0))
    
    # Bonus if target has debuffs
    if bonus_if_debuff > 0 and len(tgt.statuses) > 0:
        percent += bonus_if_debuff
    
    amount = tgt.stats.MAX_HP * percent
    
    if damage_type == "physical":
        amount = _mitigation(amount, tgt.stats.ARMOR)
    elif damage_type == "magical":
        amount = _mitigation(amount, tgt.stats.MR)
    
    apply_damage(b, tgt, amount, label)


@register("on_hit_mr_scaling")
def eff_on_hit_mr_scaling(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    On-hit basé sur la MR du lanceur (Wit's End style).
    
    Params: mr_ratio (REQUIS), label (REQUIS)
    """
    if not _require_param(b, "on_hit_mr_scaling", p, "mr_ratio"): return
    if not _require_param(b, "on_hit_mr_scaling", p, "label"): return
    
    mr_ratio = float(p["mr_ratio"])
    label = p["label"]
    
    amount = src.stats.MR * mr_ratio
    amount = _mitigation(amount, tgt.stats.MR)
    
    apply_damage(b, tgt, amount, label)


@register("spellblade_damage")
def eff_spellblade_damage(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Effet Spellblade (Sheen, Trinity, Lich Bane, etc.).
    
    Params: type (REQUIS - "triforce", "lich_bane", "gauntlet", "divine"), base_ad (REQUIS), ratio (REQUIS)
    Pour lich_bane: ap_ratio (REQUIS)
    Pour divine: hp_percent (REQUIS)
    """
    if not _require_param(b, "spellblade_damage", p, "type"): return
    if not _require_param(b, "spellblade_damage", p, "base_ad"): return
    if not _require_param(b, "spellblade_damage", p, "ratio"): return
    
    spellblade_type = p["type"]
    base_ad = float(p["base_ad"])
    ratio = float(p["ratio"])
    
    if spellblade_type == "triforce":
        # Trinity Force: 200% base AD
        amount = base_ad * ratio
        damage_type = "physical"
        label = "Spellblade (Trinity)"
    
    elif spellblade_type == "lich_bane":
        # Lich Bane: 75% base AD + 50% AP
        if not _require_param(b, "spellblade_damage", p, "ap_ratio"): return
        ap_ratio = float(p["ap_ratio"])
        amount = base_ad * ratio + src.stats.AP * ap_ratio
        damage_type = "magical"
        label = "Spellblade (Lich Bane)"
    
    elif spellblade_type == "gauntlet":
        # Iceborn Gauntlet: 150% base AD
        amount = base_ad * ratio
        damage_type = "physical"
        label = "Spellblade (Gauntlet)"
    
    elif spellblade_type == "divine":
        # Divine Sunderer: 9% target max HP (capped)
        if not _require_param(b, "spellblade_damage", p, "hp_percent"): return
        hp_percent = float(p["hp_percent"])
        amount = max(base_ad * ratio, tgt.stats.MAX_HP * hp_percent)
        damage_type = "physical"
        label = "Spellblade (Divine)"
    
    else:
        amount = base_ad * ratio
        damage_type = "physical"
        label = "Spellblade"
    
    if damage_type == "physical":
        amount = _mitigation(amount, tgt.stats.ARMOR)
    else:
        amount = _mitigation(amount, tgt.stats.MR)
    
    apply_damage(b, tgt, amount, label)
