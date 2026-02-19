"""Apply status opcode.

IMPORTANT: Tous les paramètres doivent être fournis par les items JSON.
"""
from app.engine.combat import register, eval_formula, apply_status
from app.engine.domain import Battle, Entity
from typing import Dict, Any


def _require_param(b: Battle, opcode: str, p: Dict, key: str) -> bool:
    if key not in p:
        b.log.append(f"[WARN] {opcode}: '{key}' param missing")
        return False
    return True


def clamp01(x: float) -> float: 
    return max(0.0, min(1.0, x))


@register("apply_status")
def eff_apply_status(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Applique un statut avec chance de résistance.
    
    Params: status_code (REQUIS), duration_turns (REQUIS), chance (REQUIS)
    """
    if not _require_param(b, "apply_status", p, "status_code"): return
    if not _require_param(b, "apply_status", p, "duration_turns"): return
    if not _require_param(b, "apply_status", p, "chance"): return
    
    chance_expr = str(p["chance"])
    chance = clamp01(float(eval_formula(chance_expr, src, tgt)))
    
    if b.rng.random() <= chance:
        code = p["status_code"]
        duration = int(p["duration_turns"])
        apply_status(b, tgt, code, duration)
    else:
        b.log.append(f"{tgt.name} resisted {p['status_code']}.")
