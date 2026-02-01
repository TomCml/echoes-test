from app.engine.combat import register, eval_formula
from app.engine.domain import Battle, Entity
from typing import Dict, Any


@register("shield")
def eff_shield(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    base = eval_formula(p["formula"], src, tgt)
    amount = max(1, int(round(base)))
    tgt.gauges["shield"] = tgt.gauges.get("shield", 0) + amount
    b.log.append(f"{tgt.name} gains {amount} shield (total {tgt.gauges['shield']}).")
