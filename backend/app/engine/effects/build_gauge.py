from app.engine.combat import register
from app.engine.domain import Battle, Entity
from app.schemas.combat_events import GaugeChangeEvent
from typing import Dict, Any

@register("build_gauge")
def eff_build_gauge(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    need = p.get("only_if_target_has_status")
    if need and need not in tgt.statuses:
        return

    g = p["gauge"]
    amt = int(p.get("amount", 1))
    old_val = src.gauges.get(g, 0)
    src.gauges[g] = old_val + amt
    new_val = src.gauges[g]

    b.add_log(f"{src.name} gains {amt} {g} (total {new_val}).")

    b.emit(GaugeChangeEvent(
        turn=0, sequence=0,
        source=src.id,
        gauge_name=g,
        old_value=old_val,
        new_value=new_val,
        max_value=100,  # TODO: tirer depuis config
    ))
