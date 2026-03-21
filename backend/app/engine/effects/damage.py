"""
Opcode: damage

Calcule et applique des dégâts avec :
  - eval_formula() pour le montant brut
  - variance aléatoire
  - critical hit basé sur src.stats.CRIT_CHANCE / CRIT_DAMAGE
  - mitigation par ARMOR (physical) ou MR (magic)

Params attendus dans l'EffectPayload :
  formula     : str   — expression (ex: "140 + S_AD * 0.90")
  damage_type : str   — "physical"|"magic"|"true"|"mixed" (default: "physical")
  variance    : float — ex: 0.05 → ±5% (default: 0)
  can_crit    : bool  — autorise le crit (default: false)
  label       : str   — étiquette dans le log (default: "damage")
"""
import math
from app.engine.combat import register, eval_formula, apply_damage
from app.engine.domain import Battle, Entity
from typing import Dict, Any


# ─── Mitigation Constants ────────────────────────────────
# Formule exponentielle : mult = e^(-resistance / DIVISOR)
# À 100 ARMOR → ~20% réduction | 200 → ~36% | 400 → ~59%
MITIGATION_DIVISOR = 448.6


def _mitigate(raw: float, resistance: float) -> float:
    """Applique la réduction par armure/MR (formule exponentielle)."""
    if resistance <= 0:
        return raw
    mult = math.exp(-resistance / MITIGATION_DIVISOR)
    return raw * mult


@register("damage")
def eff_damage(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    # 1. Raw damage from formula
    base = eval_formula(p["formula"], src, tgt)

    # 2. Variance roll (±X%)
    variance = float(p.get("variance", 0.0))
    roll = 1.0 + (b.rng.random() * 2 - 1) * variance
    amount = base * roll

    # 3. Critical hit (from entity stats)
    can_crit = bool(p.get("can_crit", False))
    label = p.get("label", "damage")
    is_crit = False

    if can_crit and b.rng.random() < src.stats.CRIT_CHANCE:
        amount *= src.stats.CRIT_DAMAGE
        is_crit = True
        label += " 💥crit"

    # 4. Mitigation (ARMOR pour physical, MR pour magic)
    damage_type = p.get("damage_type", "physical").lower()

    if damage_type == "physical":
        amount = _mitigate(amount, tgt.stats.ARMOR)
    elif damage_type == "magic":
        amount = _mitigate(amount, tgt.stats.MR)
    elif damage_type == "mixed":
        phys_part = _mitigate(amount * 0.5, tgt.stats.ARMOR)
        magic_part = _mitigate(amount * 0.5, tgt.stats.MR)
        amount = phys_part + magic_part
    # "true" → no mitigation

    # 5. Apply
    apply_damage(b, tgt, amount, label)
