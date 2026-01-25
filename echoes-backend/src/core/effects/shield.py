"""
Echoes Backend - Shield Effect
Opcode for applying shields.
"""
from typing import Any, Dict, TYPE_CHECKING

from src.core.engine.effect_registry import register
from src.core.engine.formula_engine import eval_formula

if TYPE_CHECKING:
    from src.core.engine.combat_engine import Battle
    from src.domain.entities.combat import CombatEntity


@register("shield")
def effect_shield(
    battle: "Battle",
    source: "CombatEntity",
    target: "CombatEntity",
    params: Dict[str, Any],
) -> None:
    """
    Apply a shield to the target.
    
    Params:
        - formula: str - Shield amount formula
        - duration_turns: int - Optional duration (permanent if not set)
        - label: str - Label for combat log
    """
    formula = params.get("formula", "0")
    label = params.get("label", "shield")
    
    amount = int(eval_formula(formula, source, target))
    
    if amount <= 0:
        return
    
    # Add to shield gauge
    current_shield = target.gauges.get("shield", 0)
    target.gauges["shield"] = current_shield + amount
    
    battle.log(
        f"{target.name} gains {amount} {label} (total: {target.gauges['shield']})"
    )


@register("remove_shield")
def effect_remove_shield(
    battle: "Battle",
    source: "CombatEntity",
    target: "CombatEntity",
    params: Dict[str, Any],
) -> None:
    """
    Remove shield from target.
    
    Params:
        - amount: int - Amount to remove (all if not specified)
    """
    amount = params.get("amount")
    
    current_shield = target.gauges.get("shield", 0)
    
    if amount is None:
        # Remove all
        target.gauges["shield"] = 0
        battle.log(f"{target.name}'s shield removed ({current_shield})")
    else:
        removed = min(int(amount), current_shield)
        target.gauges["shield"] = current_shield - removed
        battle.log(f"{target.name}'s shield reduced by {removed}")
