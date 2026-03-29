from app.engine.combat import register, eval_formula, apply_status
from app.engine.domain import Battle, Entity
from app.schemas.combat_events import StatusResistEvent
from typing import Dict, Any

def clamp01(x: float) -> float: return max(0.0, min(1.0, x))

@register("apply_status")
def eff_apply_status(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    chance_expr = str(p.get("chance", "1"))
    chance = clamp01(float(eval_formula(chance_expr, src, tgt)))
    if b.rng.random() <= chance:
        code = p["status_code"]
        duration = int(p["duration_turns"])
        apply_status(b, tgt, code, duration, source=src)
    else:
        b.add_log(f"{tgt.name} resisted {p.get('status_code')}.")
        b.emit(StatusResistEvent(
            turn=0, sequence=0,
            source=src.id,
            target=tgt.id,
            status_code=p.get("status_code", "unknown"),
        ))
