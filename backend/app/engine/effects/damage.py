from app.engine.combat import register, eval_formula, apply_damage
from app.engine.domain import Battle, Entity
from typing import Dict, Any
import random

@register("damage")
def eff_damage(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    base = eval_formula(p["formula"], src, tgt)
    variance = float(p.get("variance", 0.0))
    roll = 1.0 + (b.rng.random() * 2 - 1) * variance
    amount = base * roll
    can_crit = bool(p.get("can_crit", False))
    label = p.get("label", "damage")
    if can_crit and b.rng.random() < 0.2:
        amount *= 1.5
        label += " (crit)"
    apply_damage(b, tgt, amount, label)
