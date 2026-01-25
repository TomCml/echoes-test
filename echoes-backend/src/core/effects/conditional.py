"""
Echoes Backend - Conditional Effects
Opcodes that apply effects conditionally.
"""
from typing import Any, Dict, TYPE_CHECKING

from src.core.engine.effect_registry import register
from src.core.engine.formula_engine import eval_formula
from src.domain.enums.types import DamageType

if TYPE_CHECKING:
    from src.core.engine.combat_engine import Battle
    from src.domain.entities.combat import CombatEntity


@register("bonus_damage_if_target_has_status")
def effect_bonus_damage_if_status(
    battle: "Battle",
    source: "CombatEntity",
    target: "CombatEntity",
    params: Dict[str, Any],
) -> None:
    """
    Deal bonus damage if target has a specific status.
    
    Params:
        - status_code: str - Status to check for
        - formula: str - Bonus damage formula
        - damage_type: str - Damage type (default: PHYSICAL)
        - consume_status: bool - Remove status after bonus (default: False)
    """
    status_code = params.get("status_code", "")
    formula = params.get("formula", "0")
    damage_type_str = params.get("damage_type", "PHYSICAL")
    consume_status = params.get("consume_status", False)
    
    if not target.has_status(status_code):
        return
    
    # Calculate bonus damage
    bonus = int(eval_formula(formula, source, target))
    if bonus <= 0:
        return
    
    try:
        damage_type = DamageType[damage_type_str]
    except KeyError:
        damage_type = DamageType.PHYSICAL
    
    result = target.take_damage(bonus, damage_type)
    battle.log(
        f"{source.name} deals {result.final_damage} bonus damage ({status_code}). "
        f"HP: {target.current_hp}/{target.max_hp}"
    )
    
    if consume_status:
        target.remove_status(status_code)
        battle.log(f"{status_code} consumed")


@register("bonus_damage_per_stack")
def effect_bonus_damage_per_stack(
    battle: "Battle",
    source: "CombatEntity",
    target: "CombatEntity",
    params: Dict[str, Any],
) -> None:
    """
    Deal bonus damage per stack of a status.
    
    Params:
        - status_code: str - Status to count stacks
        - damage_per_stack: int - Damage per stack
        - damage_type: str - Damage type
        - consume_stacks: bool - Remove stacks after damage
    """
    status_code = params.get("status_code", "")
    damage_per_stack = int(params.get("damage_per_stack", 10))
    damage_type_str = params.get("damage_type", "MAGIC")
    consume_stacks = params.get("consume_stacks", False)
    
    stacks = target.get_status_stacks(status_code)
    if stacks <= 0:
        return
    
    total_damage = damage_per_stack * stacks
    
    try:
        damage_type = DamageType[damage_type_str]
    except KeyError:
        damage_type = DamageType.MAGIC
    
    result = target.take_damage(total_damage, damage_type)
    battle.log(
        f"{source.name} deals {result.final_damage} damage ({stacks} {status_code} stacks). "
        f"HP: {target.current_hp}/{target.max_hp}"
    )
    
    if consume_stacks:
        target.remove_status(status_code)


@register("execute_if_low_hp")
def effect_execute_if_low_hp(
    battle: "Battle",
    source: "CombatEntity",
    target: "CombatEntity",
    params: Dict[str, Any],
) -> None:
    """
    Instantly kill target if below HP threshold.
    
    Params:
        - threshold_percent: float - HP percentage threshold (e.g., 0.15)
        - ignore_bosses: bool - Don't execute boss monsters (default: True)
    """
    threshold = float(params.get("threshold_percent", 0.15))
    ignore_bosses = params.get("ignore_bosses", True)
    
    # Check for boss
    if ignore_bosses and hasattr(target, 'is_boss') and target.is_boss:
        return
    
    if target.hp_percent <= threshold:
        overkill = target.current_hp
        target.current_hp = 0
        battle.log(f"{source.name} executes {target.name}!")


@register("if_condition")
def effect_if_condition(
    battle: "Battle",
    source: "CombatEntity",
    target: "CombatEntity",
    params: Dict[str, Any],
) -> None:
    """
    Execute effects only if a condition is met.
    
    Params:
        - condition: str - Condition expression (e.g., "T_HP_PERCENT < 0.5")
        - then_effects: list - Effects to run if condition is true
        - else_effects: list - Effects to run if condition is false (optional)
    """
    from src.core.engine.effect_registry import run_effects
    
    condition = params.get("condition", "1")
    then_effects = params.get("then_effects", [])
    else_effects = params.get("else_effects", [])
    
    # Evaluate condition
    result = eval_formula(condition, source, target)
    
    if result:
        if then_effects:
            run_effects(battle, source, target, then_effects)
    else:
        if else_effects:
            run_effects(battle, source, target, else_effects)
