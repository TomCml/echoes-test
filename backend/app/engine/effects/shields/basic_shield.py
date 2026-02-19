"""Basic shield opcodes - Boucliers standard.

IMPORTANT: Tous les paramètres doivent être fournis par les items JSON.
"""
from typing import Dict, Any
from app.engine.combat import register, eval_formula
from app.engine.domain import Battle, Entity


def _require_param(b: Battle, opcode: str, p: Dict, key: str) -> bool:
    if key not in p:
        b.log.append(f"[WARN] {opcode}: '{key}' param missing")
        return False
    return True


@register("shield")
def eff_shield(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique un bouclier avec formule. Params: formula (REQUIS)"""
    if not _require_param(b, "shield", p, "formula"): return
    
    base = eval_formula(p["formula"], src, tgt)
    amount = max(1, int(round(base)))
    tgt.gauges["shield"] = tgt.gauges.get("shield", 0) + amount
    b.log.append(f"{tgt.name} gains {amount} shield (total {tgt.gauges['shield']}).")


@register("shield_flat")
def eff_shield_flat(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Bouclier fixe. Params: amount (REQUIS)"""
    if not _require_param(b, "shield_flat", p, "amount"): return
    
    amount = int(p["amount"])
    tgt.gauges["shield"] = tgt.gauges.get("shield", 0) + amount
    b.log.append(f"{tgt.name} gains {amount} shield (total {tgt.gauges['shield']}).")


@register("shield_percent_hp")
def eff_shield_percent_hp(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Bouclier en % des PV max. Params: percent (REQUIS), use_target_hp (optionnel, default: False)"""
    if not _require_param(b, "shield_percent_hp", p, "percent"): return
    
    percent = float(p["percent"])
    use_target_hp = bool(p.get("use_target_hp", False))
    
    base_hp = tgt.stats.MAX_HP if use_target_hp else src.stats.MAX_HP
    amount = int(base_hp * percent)
    
    tgt.gauges["shield"] = tgt.gauges.get("shield", 0) + amount
    b.log.append(f"{tgt.name} gains {amount} shield ({int(percent*100)}% max HP).")


@register("self_shield")
def eff_self_shield(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Bouclier sur le lanceur. Params: formula (REQUIS)"""
    if not _require_param(b, "self_shield", p, "formula"): return
    
    base = eval_formula(p["formula"], src, src)
    amount = max(1, int(round(base)))
    src.gauges["shield"] = src.gauges.get("shield", 0) + amount
    b.log.append(f"{src.name} gains {amount} self-shield (total {src.gauges['shield']}).")


@register("shield_ap_scaling")
def eff_shield_ap_scaling(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Bouclier avec ratio AP. Params: base (REQUIS), ap_ratio (REQUIS)"""
    if not _require_param(b, "shield_ap_scaling", p, "base"): return
    if not _require_param(b, "shield_ap_scaling", p, "ap_ratio"): return
    
    base = float(p["base"])
    ap_ratio = float(p["ap_ratio"])
    
    amount = int(base + src.stats.AP * ap_ratio)
    tgt.gauges["shield"] = tgt.gauges.get("shield", 0) + amount
    b.log.append(f"{tgt.name} gains {amount} AP shield (total {tgt.gauges['shield']}).")


@register("shield_ad_scaling")
def eff_shield_ad_scaling(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Bouclier avec ratio AD. Params: base (REQUIS), ad_ratio (REQUIS)"""
    if not _require_param(b, "shield_ad_scaling", p, "base"): return
    if not _require_param(b, "shield_ad_scaling", p, "ad_ratio"): return
    
    base = float(p["base"])
    ad_ratio = float(p["ad_ratio"])
    
    amount = int(base + src.stats.AD * ad_ratio)
    tgt.gauges["shield"] = tgt.gauges.get("shield", 0) + amount
    b.log.append(f"{tgt.name} gains {amount} AD shield (total {tgt.gauges['shield']}).")
