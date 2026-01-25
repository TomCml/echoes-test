"""
Echoes Backend - Formula Engine
Evaluates damage formulas with entity stats.
"""
from typing import TYPE_CHECKING, Dict, Any, Optional
import re

if TYPE_CHECKING:
    from src.domain.entities.combat import CombatEntity


# Allowed functions in formula evaluation
SAFE_FUNCTIONS = {
    "min": min,
    "max": max,
    "abs": abs,
    "int": int,
    "float": float,
}


def eval_formula(
    expr: str,
    source: "CombatEntity",
    target: "CombatEntity",
    extra_vars: Optional[Dict[str, Any]] = None,
) -> float:
    """
    Evaluate a damage/heal formula with entity stats.
    
    Available variables:
    - AD, AP, ARMOR, MR, SPEED, MAX_HP, HP, CRIT_CHANCE, CRIT_DAMAGE (source stats)
    - S_AD, S_AP, S_ARMOR, S_MR, S_MAX_HP, S_HP (source with prefix)
    - T_AD, T_AP, T_ARMOR, T_MR, T_MAX_HP, T_HP, T_HP_PERCENT (target with prefix)
    
    Example formulas:
    - "AD * 1.5 + 50"
    - "AP * 0.8 + T_MAX_HP * 0.1"
    - "100 + max(AD, AP) * 0.5"
    
    Args:
        expr: The formula expression to evaluate
        source: The entity performing the action
        target: The entity receiving the action
        extra_vars: Additional variables to inject
    
    Returns:
        The calculated numeric result
    """
    # Build the variable scope
    scope: Dict[str, Any] = {}
    
    # Source stats (no prefix for convenience)
    scope["AD"] = source.stats.ad
    scope["AP"] = source.stats.ap
    scope["ARMOR"] = source.stats.armor
    scope["MR"] = source.stats.mr
    scope["SPEED"] = source.stats.speed
    scope["MAX_HP"] = source.max_hp
    scope["HP"] = source.current_hp
    scope["CRIT_CHANCE"] = source.stats.crit_chance
    scope["CRIT_DAMAGE"] = source.stats.crit_damage
    
    # Source stats with S_ prefix
    scope["S_AD"] = source.stats.ad
    scope["S_AP"] = source.stats.ap
    scope["S_ARMOR"] = source.stats.armor
    scope["S_MR"] = source.stats.mr
    scope["S_MAX_HP"] = source.max_hp
    scope["S_HP"] = source.current_hp
    scope["S_HP_PERCENT"] = source.current_hp / source.max_hp if source.max_hp > 0 else 0
    
    # Target stats with T_ prefix
    scope["T_AD"] = target.stats.ad
    scope["T_AP"] = target.stats.ap
    scope["T_ARMOR"] = target.stats.armor
    scope["T_MR"] = target.stats.mr
    scope["T_MAX_HP"] = target.max_hp
    scope["T_HP"] = target.current_hp
    scope["T_HP_PERCENT"] = target.current_hp / target.max_hp if target.max_hp > 0 else 0
    scope["T_MISSING_HP"] = target.max_hp - target.current_hp
    scope["T_MISSING_HP_PERCENT"] = 1 - scope["T_HP_PERCENT"]
    
    # Echo for player entities
    if hasattr(source, 'echo_current'):
        scope["ECHO"] = source.echo_current
        scope["ECHO_MAX"] = source.echo_max
        scope["S_ECHO"] = source.echo_current
    
    # Status stacks
    for status_code, instance in source.statuses.items():
        scope[f"S_STACKS_{status_code}"] = instance.stacks
    for status_code, instance in target.statuses.items():
        scope[f"T_STACKS_{status_code}"] = instance.stacks
    
    # Shield values
    scope["S_SHIELD"] = source.gauges.get("shield", 0)
    scope["T_SHIELD"] = target.gauges.get("shield", 0)
    
    # Extra variables
    if extra_vars:
        scope.update(extra_vars)
    
    # Add safe functions
    scope.update(SAFE_FUNCTIONS)
    
    # Evaluate with no builtins for security
    try:
        result = eval(expr, {"__builtins__": {}}, scope)
        return float(result)
    except Exception as e:
        # Log error and return 0 on failure
        print(f"[ERROR] Formula evaluation failed: {expr} -> {e}")
        return 0.0


def validate_formula(expr: str) -> tuple[bool, str]:
    """
    Validate a formula expression without executing it.
    Returns (is_valid, error_message).
    """
    # Check for dangerous patterns
    dangerous_patterns = [
        r'__',  # Double underscore (dunder methods)
        r'import',
        r'exec',
        r'eval',
        r'compile',
        r'open',
        r'file',
        r'input',
        r'os\.',
        r'sys\.',
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, expr, re.IGNORECASE):
            return False, f"Forbidden pattern: {pattern}"
    
    # Check for basic syntax errors
    try:
        compile(expr, '<string>', 'eval')
        return True, "OK"
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
