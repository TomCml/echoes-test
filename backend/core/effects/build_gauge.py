from core.engine import register
from models.domain import Battle, Entity
from typing import Dict, Any

@register("build_gauge")
def eff_build_gauge(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    need = p.get("only_if_target_has_status")
    if need and need not in tgt.statuses:
        return
    g = p["gauge"]; amt = int(p.get("amount", 1))
    src.gauges[g] = src.gauges.get(g, 0) + amt
    b.log.append(f"{src.name} gains {amt} {g} (total {src.gauges[g]}).")
