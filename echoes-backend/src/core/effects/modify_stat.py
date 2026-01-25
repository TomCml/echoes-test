"""
Echoes Backend - Modify Stat Effect
Opcodes for temporary stat modifications.
"""
from typing import Any, Dict, TYPE_CHECKING

from src.core.engine.effect_registry import register
from src.core.engine.formula_engine import eval_formula

if TYPE_CHECKING:
    from src.core.engine.combat_engine import Battle
    from src.domain.entities.combat import CombatEntity


@register("modify_stat")
def effect_modify_stat(
    battle: "Battle",
    source: "CombatEntity",
    target: "CombatEntity",
    params: Dict[str, Any],
) -> None:
    """
    Temporarily modify a stat via a buff/debuff status.
    The actual stat modification is handled by status effects.
    
    Params:
        - stat: str - Stat name (AD, AP, ARMOR, MR, SPEED)
        - formula: str - Amount formula
        - duration_turns: int - Duration of the buff/debuff
        - is_debuff: bool - Whether this is a debuff (default: False)
    """
    stat = params.get("stat", "AD")
    formula = params.get("formula", "0")
    duration = int(params.get("duration_turns", 2))
    is_debuff = params.get("is_debuff", False)
    
    amount = int(eval_formula(formula, source, target))
    
    if amount == 0:
        return
    
    # Create a dynamic buff/debuff status
    sign = "-" if amount < 0 else "+"
    status_code = f"STAT_{stat}_{sign}{abs(amount)}"
    
    target.add_status(status_code, duration)
    
    effect_type = "debuff" if is_debuff else "buff"
    battle.log(
        f"{target.name} gains {effect_type}: {stat} {sign}{abs(amount)} for {duration} turns"
    )


@register("steal_stat")
def effect_steal_stat(
    battle: "Battle",
    source: "CombatEntity",
    target: "CombatEntity",
    params: Dict[str, Any],
) -> None:
    """
    Steal stats from target to source.
    
    Params:
        - stat: str - Stat to steal
        - amount: int - Amount to steal
        - duration_turns: int - Duration
    """
    stat = params.get("stat", "AD")
    amount = int(params.get("amount", 10))
    duration = int(params.get("duration_turns", 2))
    
    # Debuff target
    target.add_status(f"STAT_{stat}_-{amount}", duration)
    
    # Buff source
    source.add_status(f"STAT_{stat}_+{amount}", duration)
    
    battle.log(
        f"{source.name} steals {amount} {stat} from {target.name} for {duration} turns"
    )
