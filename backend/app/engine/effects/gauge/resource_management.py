"""Resource management opcodes - Gestion générique des ressources.

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


@register("build_gauge")
def eff_build_gauge(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Génère une ressource dans une jauge. Params: gauge (REQUIS), amount (REQUIS), max (REQUIS), only_if_target_has_status (optionnel)"""
    if not _require_param(b, "build_gauge", p, "gauge"): return
    if not _require_param(b, "build_gauge", p, "amount"): return
    if not _require_param(b, "build_gauge", p, "max"): return
    
    gauge = p["gauge"]
    amount = int(p["amount"])
    max_value = int(p["max"])
    
    only_if = p.get("only_if_target_has_status")
    if only_if and only_if not in tgt.statuses:
        return
    
    current = src.gauges.get(gauge, 0)
    new_value = min(max_value, current + amount)
    src.gauges[gauge] = new_value
    
    b.log.append(f"{src.name} gains {amount} {gauge} (total {new_value}).")


@register("drain_gauge")
def eff_drain_gauge(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Draine une jauge. Params: gauge (REQUIS), amount (REQUIS)"""
    if not _require_param(b, "drain_gauge", p, "gauge"): return
    if not _require_param(b, "drain_gauge", p, "amount"): return
    
    gauge = p["gauge"]
    amount = int(p["amount"])
    
    current = src.gauges.get(gauge, 0)
    drained = min(current, amount)
    src.gauges[gauge] = current - drained
    
    b.log.append(f"{src.name} loses {drained} {gauge} ({src.gauges[gauge]} remaining).")
    return drained


@register("set_gauge")
def eff_set_gauge(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Set une jauge à une valeur spécifique. Params: gauge (REQUIS), value (REQUIS)"""
    if not _require_param(b, "set_gauge", p, "gauge"): return
    if not _require_param(b, "set_gauge", p, "value"): return
    
    gauge = p["gauge"]
    value = int(p["value"])
    
    old = src.gauges.get(gauge, 0)
    src.gauges[gauge] = value
    
    b.log.append(f"{src.name}'s {gauge}: {old} -> {value}.")


@register("transfer_gauge")
def eff_transfer_gauge(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Transfère une jauge d'une entité à une autre. Params: gauge (REQUIS), amount (REQUIS si pas all), all (optionnel)"""
    if not _require_param(b, "transfer_gauge", p, "gauge"): return
    
    gauge = p["gauge"]
    transfer_all = bool(p.get("all", False))
    
    if not transfer_all and "amount" not in p:
        b.log.append(f"[WARN] transfer_gauge: 'amount' param missing (or use 'all': true)")
        return
    
    current = src.gauges.get(gauge, 0)
    
    if transfer_all:
        transferred = current
        src.gauges[gauge] = 0
    else:
        amount = int(p["amount"])
        transferred = min(current, amount)
        src.gauges[gauge] = current - transferred
    
    tgt_current = tgt.gauges.get(gauge, 0)
    tgt.gauges[gauge] = tgt_current + transferred
    
    b.log.append(f"{transferred} {gauge} transferred from {src.name} to {tgt.name}.")


@register("gauge_decay")
def eff_gauge_decay(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Réduit une jauge au fil du temps. Params: gauge (REQUIS), decay (REQUIS)"""
    if not _require_param(b, "gauge_decay", p, "gauge"): return
    if not _require_param(b, "gauge_decay", p, "decay"): return
    
    gauge = p["gauge"]
    decay = int(p["decay"])
    
    current = src.gauges.get(gauge, 0)
    new_value = max(0, current - decay)
    src.gauges[gauge] = new_value
    
    if current != new_value:
        b.log.append(f"{src.name}'s {gauge} decays by {decay} ({new_value}).")
