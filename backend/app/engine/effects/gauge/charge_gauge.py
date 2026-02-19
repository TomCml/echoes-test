"""Charge gauge opcodes - Gestion des charges (Onde Orageuse, etc.).

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


@register("build_charge")
def eff_build_charge(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Génère des charges. Params: amount (REQUIS), max (REQUIS), gauge (REQUIS)"""
    if not _require_param(b, "build_charge", p, "amount"): return
    if not _require_param(b, "build_charge", p, "max"): return
    if not _require_param(b, "build_charge", p, "gauge"): return
    
    amount = int(p["amount"])
    max_charges = int(p["max"])
    gauge_name = p["gauge"]
    
    current = src.gauges.get(gauge_name, 0)
    new_value = min(max_charges, current + amount)
    src.gauges[gauge_name] = new_value
    
    b.log.append(f"{src.name} gains {amount} {gauge_name} ({new_value}/{max_charges}).")


@register("consume_charges")
def eff_consume_charges(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Consomme des charges. Params: gauge (REQUIS), amount (REQUIS si pas all), all (optionnel)"""
    if not _require_param(b, "consume_charges", p, "gauge"): return
    
    gauge_name = p["gauge"]
    all_charges = bool(p.get("all", False))
    
    if not all_charges and "amount" not in p:
        b.log.append(f"[WARN] consume_charges: 'amount' param missing (or use 'all': true)")
        return
    
    current = src.gauges.get(gauge_name, 0)
    
    if all_charges:
        consumed = current
        src.gauges[gauge_name] = 0
    else:
        amount = int(p["amount"])
        consumed = min(current, amount)
        src.gauges[gauge_name] = current - consumed
    
    b.log.append(f"{src.name} consumes {consumed} {gauge_name} ({src.gauges[gauge_name]} remaining).")
    return consumed


@register("check_charges")
def eff_check_charges(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Vérifie si assez de charges pour un effet. Params: required (REQUIS), gauge (REQUIS)"""
    if not _require_param(b, "check_charges", p, "required"): return False
    if not _require_param(b, "check_charges", p, "gauge"): return False
    
    required = int(p["required"])
    gauge_name = p["gauge"]
    
    current = src.gauges.get(gauge_name, 0)
    return current >= required


@register("charge_scaling_effect")
def eff_charge_scaling_effect(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Effet qui scale avec le nombre de charges. Params: gauge (REQUIS), per_charge (REQUIS), effect_type (REQUIS)"""
    if not _require_param(b, "charge_scaling_effect", p, "gauge"): return 0
    if not _require_param(b, "charge_scaling_effect", p, "per_charge"): return 0
    if not _require_param(b, "charge_scaling_effect", p, "effect_type"): return 0
    
    gauge_name = p["gauge"]
    per_charge = float(p["per_charge"])
    effect_type = p["effect_type"]
    
    charges = src.gauges.get(gauge_name, 0)
    bonus = per_charge * charges
    
    if effect_type == "damage":
        b.log.append(f"+{int(bonus)} damage from {charges} charges.")
    elif effect_type == "heal":
        b.log.append(f"+{int(bonus)} heal from {charges} charges.")
    
    return bonus


@register("threshold_effect")
def eff_threshold_effect(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Déclenche un effet si jauge atteint un seuil. Params: gauge (REQUIS), threshold (REQUIS), effect_opcode (REQUIS), effect_params (REQUIS), consume (optionnel)"""
    if not _require_param(b, "threshold_effect", p, "gauge"): return False
    if not _require_param(b, "threshold_effect", p, "threshold"): return False
    if not _require_param(b, "threshold_effect", p, "effect_opcode"): return False
    if not _require_param(b, "threshold_effect", p, "effect_params"): return False
    
    gauge_name = p["gauge"]
    threshold = int(p["threshold"])
    consume = bool(p.get("consume", True))
    effect_opcode = p["effect_opcode"]
    effect_params = p["effect_params"]
    
    current = src.gauges.get(gauge_name, 0)
    
    if current >= threshold:
        b.log.append(f"{gauge_name} threshold reached ({current}/{threshold})!")
        
        if consume:
            src.gauges[gauge_name] = 0
            b.log.append(f"Charges consumed.")
        
        from app.engine.combat import REGISTRY
        if effect_opcode in REGISTRY:
            REGISTRY[effect_opcode](b, src, tgt, effect_params)
        
        return True
    
    return False
