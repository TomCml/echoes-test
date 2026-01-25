"""
Echoes Backend - Gauge Effects
Opcodes for building/consuming Echo and other gauges.
"""
from typing import Any, Dict, TYPE_CHECKING

from src.core.engine.effect_registry import register
from src.core.engine.formula_engine import eval_formula

if TYPE_CHECKING:
    from src.core.engine.combat_engine import Battle
    from src.domain.entities.combat import CombatEntity


@register("build_gauge")
def effect_build_gauge(
    battle: "Battle",
    source: "CombatEntity",
    target: "CombatEntity",
    params: Dict[str, Any],
) -> None:
    """
    Add or remove from a gauge (echo, custom gauges).
    
    Params:
        - gauge: str - Gauge name ("echo" or custom)
        - amount: int - Amount to add (negative to remove)
        - formula: str - Optional formula instead of fixed amount
        - only_if_target_has_status: str - Conditional on target status
        - target_self: bool - Apply to source instead of target (default: True for echo)
    """
    gauge = params.get("gauge", "echo")
    amount = int(params.get("amount", 0))
    formula = params.get("formula")
    condition_status = params.get("only_if_target_has_status")
    target_self = params.get("target_self", True if gauge == "echo" else False)
    
    # Check condition
    if condition_status and not target.has_status(condition_status):
        return
    
    # Calculate amount from formula if provided
    if formula:
        amount = int(eval_formula(formula, source, target))
    
    # Determine which entity to modify
    entity = source if target_self else target
    
    # Handle echo gauge specially for player entities
    if gauge == "echo" and hasattr(entity, 'echo_current'):
        if amount > 0:
            added = entity.add_echo(amount)
            battle.log(f"{entity.name} gains {added} Echo (total: {entity.echo_current})")
        else:
            entity.echo_current = max(0, entity.echo_current + amount)
            battle.log(f"{entity.name} loses {-amount} Echo (total: {entity.echo_current})")
    else:
        # Generic gauge
        old_value = entity.gauges.get(gauge, 0)
        new_value = max(0, old_value + amount)
        entity.gauges[gauge] = new_value
        
        if amount > 0:
            battle.log(f"{entity.name} gains {amount} {gauge} (total: {new_value})")
        else:
            battle.log(f"{entity.name} loses {-amount} {gauge} (total: {new_value})")


@register("consume_gauge")
def effect_consume_gauge(
    battle: "Battle",
    source: "CombatEntity",
    target: "CombatEntity",
    params: Dict[str, Any],
) -> None:
    """
    Consume a gauge to power an effect.
    Use in combination with conditionals.
    
    Params:
        - gauge: str - Gauge name
        - amount: int - Amount to consume
        - require_full: bool - Require the full amount to proceed
    """
    gauge = params.get("gauge", "echo")
    amount = int(params.get("amount", 0))
    require_full = params.get("require_full", True)
    
    if gauge == "echo" and hasattr(source, 'echo_current'):
        if require_full and source.echo_current < amount:
            battle.log(f"Not enough Echo ({source.echo_current}/{amount})")
            return
        
        consumed = min(amount, source.echo_current)
        source.echo_current -= consumed
        battle.log(f"{source.name} consumed {consumed} Echo")
    else:
        current = source.gauges.get(gauge, 0)
        if require_full and current < amount:
            battle.log(f"Not enough {gauge} ({current}/{amount})")
            return
        
        consumed = min(amount, current)
        source.gauges[gauge] = current - consumed
        battle.log(f"{source.name} consumed {consumed} {gauge}")


@register("set_gauge")
def effect_set_gauge(
    battle: "Battle",
    source: "CombatEntity",
    target: "CombatEntity",
    params: Dict[str, Any],
) -> None:
    """
    Set a gauge to a specific value.
    
    Params:
        - gauge: str - Gauge name
        - value: int - Value to set
        - target_self: bool - Apply to source (default: True)
    """
    gauge = params.get("gauge", "echo")
    value = int(params.get("value", 0))
    target_self = params.get("target_self", True)
    
    entity = source if target_self else target
    
    if gauge == "echo" and hasattr(entity, 'echo_current'):
        entity.echo_current = min(value, entity.echo_max)
        battle.log(f"{entity.name}'s Echo set to {entity.echo_current}")
    else:
        entity.gauges[gauge] = value
        battle.log(f"{entity.name}'s {gauge} set to {value}")
