from app.engine.combat import register, eval_formula, apply_status
from app.engine.domain import Battle, Entity
from typing import Dict, Any

def clamp01(x: float) -> float: return max(0.0, min(1.0, x))

@register("apply_status")
def eff_apply_status(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    chance_expr = str(p.get("chance", "1"))
    chance = clamp01(float(eval_formula(chance_expr, src, tgt)))
    if b.rng.random() <= chance:
        code = p["status_code"]
        duration = int(p["duration_turns"])
        apply_status(b, tgt, code, duration)
    else:
        b.log.append(f"{tgt.name} resisted {p.get('status_code')}.")
