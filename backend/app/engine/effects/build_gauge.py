"""Build gauge opcode - Construction de jauge (legacy).

IMPORTANT: Tous les paramètres doivent être fournis par les items JSON.
"""
from app.engine.combat import register
from app.engine.domain import Battle, Entity
from typing import Dict, Any


def _require_param(b: Battle, opcode: str, p: Dict, key: str) -> bool:
    if key not in p:
        b.log.append(f"[WARN] {opcode}: '{key}' param missing")
        return False
    return True


@register("build_gauge")
def eff_build_gauge(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Build gauge générique.
    
    Params: gauge (REQUIS), amount (REQUIS)
    Optionnel: only_if_target_has_status
    """
    if not _require_param(b, "build_gauge", p, "gauge"): return
    if not _require_param(b, "build_gauge", p, "amount"): return
    
    need = p.get("only_if_target_has_status")
    if need and need not in tgt.statuses:
        return
    
    gauge = p["gauge"]
    amount = int(p["amount"])
    
    src.gauges[gauge] = src.gauges.get(gauge, 0) + amount
    b.log.append(f"{src.name} gains {amount} {gauge} (total {src.gauges[gauge]}).")
