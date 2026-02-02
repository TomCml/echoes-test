import math
from app.engine.combat import register, eval_formula, apply_damage
from app.engine.domain import Battle, Entity
from typing import Dict, Any


def _mitigation(raw: float, resistance: float) -> float:
    """Réduction exponentielle par la résistance (armor ou MR)."""
    if resistance <= 0:
        return raw
    mult = math.exp(-resistance / 448.6)
    return raw * mult


@register("damage")
def eff_damage(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    base = eval_formula(p["formula"], src, tgt)

    # Variance
    variance = float(p.get("variance", 0.0))
    roll = 1.0 + (b.rng.random() * 2 - 1) * variance
    amount = base * roll

    # Crit
    can_crit = bool(p.get("can_crit", False))
    label = p.get("label", "damage")
    is_crit = False
    if can_crit and b.rng.random() < src.stats.CRIT_CHANCE:
        amount *= src.stats.CRIT_DAMAGE
        is_crit = True
        label += " (crit)"

    # Type de dégât + mitigation
    dmg_type = p.get("damage_type", "physical")

    if dmg_type == "physical":
        amount = _mitigation(amount, tgt.stats.ARMOR)
    elif dmg_type == "magical":
        amount = _mitigation(amount, tgt.stats.MR)
    elif dmg_type == "true":
        pass  # true damage ignore les résistances
    elif dmg_type == "mixed":
        # 50/50 physique/magique
        phys = _mitigation(amount * 0.5, tgt.stats.ARMOR)
        magic = _mitigation(amount * 0.5, tgt.stats.MR)
        amount = phys + magic

    apply_damage(b, tgt, amount, label)
