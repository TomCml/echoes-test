"""
Echoes Backend - Damage Effect
Opcode for dealing damage to targets.
"""
from typing import Any, Dict, TYPE_CHECKING

from src.core.engine.effect_registry import register
from src.core.engine.formula_engine import eval_formula
from src.domain.enums.types import DamageType

if TYPE_CHECKING:
    from src.core.engine.combat_engine import Battle
    from src.domain.entities.combat import CombatEntity


@register("damage")
def effect_damage(
    battle: "Battle",
    source: "CombatEntity",
    target: "CombatEntity",
    params: Dict[str, Any],
) -> None:
    """
    Inflict damage to the target.
    
    Params:
        - formula: str - Damage formula (e.g., "AD * 1.5 + 50")
        - damage_type: str - PHYSICAL, MAGIC, TRUE, MIXED (default: PHYSICAL)
        - variance: float - Random variance 0.0-0.2 (default: 0.0)
        - can_crit: bool - Whether this can critically strike (default: False)
        - label: str - Label for combat log (default: "damage")
    """
    formula = params.get("formula", "0")
    damage_type_str = params.get("damage_type", "PHYSICAL")
    variance = float(params.get("variance", 0.0))
    can_crit = bool(params.get("can_crit", False))
    label = params.get("label", "damage")
    
    # Calculate base damage
    base_damage = eval_formula(formula, source, target)
    
    # Apply variance
    if variance > 0 and battle.rng:
        roll = 1.0 + (battle.rng.random() * 2 - 1) * variance
        base_damage *= roll
    
    # Check for critical hit
    is_crit = False
    if can_crit and battle.rng and battle.rng.random() < source.stats.crit_chance:
        base_damage *= source.stats.crit_damage
        is_crit = True
    
    # Get damage type enum
    try:
        damage_type = DamageType[damage_type_str]
    except KeyError:
        damage_type = DamageType.PHYSICAL
    
    # Apply damage
    result = target.take_damage(int(base_damage), damage_type)
    result.was_critical = is_crit
    
    # Build log message
    crit_text = " (CRIT!)" if is_crit else ""
    battle.log(
        f"{source.name} deals {result.final_damage} {label}{crit_text} to {target.name}. "
        f"HP: {target.current_hp}/{target.max_hp}"
    )
    
    # Store last damage for conditional effects
    battle.last_damage = result


@register("damage_percent_max_hp")
def effect_damage_percent_max_hp(
    battle: "Battle",
    source: "CombatEntity",
    target: "CombatEntity",
    params: Dict[str, Any],
) -> None:
    """
    Deal damage based on percentage of target's max HP.
    
    Params:
        - percent: float - Percentage of max HP (e.g., 0.1 for 10%)
        - damage_type: str - Damage type (default: TRUE)
        - label: str - Label for combat log
    """
    percent = float(params.get("percent", 0.05))
    damage_type_str = params.get("damage_type", "TRUE")
    label = params.get("label", "% max HP damage")
    
    damage = int(target.max_hp * percent)
    
    try:
        damage_type = DamageType[damage_type_str]
    except KeyError:
        damage_type = DamageType.TRUE
    
    result = target.take_damage(damage, damage_type)
    battle.log(
        f"{source.name} deals {result.final_damage} {label} to {target.name}. "
        f"HP: {target.current_hp}/{target.max_hp}"
    )


@register("damage_percent_missing_hp")
def effect_damage_percent_missing_hp(
    battle: "Battle",
    source: "CombatEntity",
    target: "CombatEntity",
    params: Dict[str, Any],
) -> None:
    """
    Deal damage based on percentage of target's missing HP.
    Execute-style damage, stronger against low HP targets.
    
    Params:
        - percent: float - Percentage of missing HP
        - damage_type: str - Damage type (default: PHYSICAL)
        - label: str - Label for combat log
    """
    percent = float(params.get("percent", 0.1))
    damage_type_str = params.get("damage_type", "PHYSICAL")
    label = params.get("label", "execute damage")
    
    missing_hp = target.max_hp - target.current_hp
    damage = int(missing_hp * percent)
    
    try:
        damage_type = DamageType[damage_type_str]
    except KeyError:
        damage_type = DamageType.PHYSICAL
    
    result = target.take_damage(damage, damage_type)
    battle.log(
        f"{source.name} deals {result.final_damage} {label} to {target.name}. "
        f"HP: {target.current_hp}/{target.max_hp}"
    )
