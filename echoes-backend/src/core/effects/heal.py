"""
Echoes Backend - Heal Effect
Opcode for healing entities.
"""
from typing import Any, Dict, TYPE_CHECKING

from src.core.engine.effect_registry import register
from src.core.engine.formula_engine import eval_formula

if TYPE_CHECKING:
    from src.core.engine.combat_engine import Battle
    from src.domain.entities.combat import CombatEntity


@register("heal")
def effect_heal(
    battle: "Battle",
    source: "CombatEntity",
    target: "CombatEntity",
    params: Dict[str, Any],
) -> None:
    """
    Heal the target.
    
    Params:
        - formula: str - Heal amount formula (e.g., "AP * 0.5 + 100")
        - label: str - Label for combat log (default: "heal")
    """
    formula = params.get("formula", "0")
    label = params.get("label", "heal")
    
    # Calculate heal amount
    amount = int(eval_formula(formula, source, target))
    
    # Apply heal
    healed = target.heal(amount)
    
    battle.log(
        f"{target.name} heals {healed} ({label}). HP: {target.current_hp}/{target.max_hp}"
    )


@register("heal_percent_max_hp")
def effect_heal_percent_max_hp(
    battle: "Battle",
    source: "CombatEntity",
    target: "CombatEntity",
    params: Dict[str, Any],
) -> None:
    """
    Heal based on percentage of target's max HP.
    
    Params:
        - percent: float - Percentage of max HP to heal
        - label: str - Label for combat log
    """
    percent = float(params.get("percent", 0.1))
    label = params.get("label", "% max HP heal")
    
    amount = int(target.max_hp * percent)
    healed = target.heal(amount)
    
    battle.log(
        f"{target.name} heals {healed} ({label}). HP: {target.current_hp}/{target.max_hp}"
    )


@register("heal_percent_missing_hp")
def effect_heal_percent_missing_hp(
    battle: "Battle",
    source: "CombatEntity",
    target: "CombatEntity",
    params: Dict[str, Any],
) -> None:
    """
    Heal based on percentage of target's missing HP.
    
    Params:
        - percent: float - Percentage of missing HP to heal
        - label: str - Label for combat log
    """
    percent = float(params.get("percent", 0.2))
    label = params.get("label", "recovery")
    
    missing_hp = target.max_hp - target.current_hp
    amount = int(missing_hp * percent)
    healed = target.heal(amount)
    
    battle.log(
        f"{target.name} heals {healed} ({label}). HP: {target.current_hp}/{target.max_hp}"
    )


@register("lifesteal")
def effect_lifesteal(
    battle: "Battle",
    source: "CombatEntity",
    target: "CombatEntity",
    params: Dict[str, Any],
) -> None:
    """
    Heal source based on last damage dealt.
    Should be used after a damage effect.
    
    Params:
        - percent: float - Percentage of damage to heal (default: 0.2)
        - label: str - Label for combat log
    """
    percent = float(params.get("percent", 0.2))
    label = params.get("label", "lifesteal")
    
    # Get last damage dealt
    last_damage = getattr(battle, 'last_damage', None)
    if not last_damage:
        return
    
    amount = int(last_damage.final_damage * percent)
    healed = source.heal(amount)
    
    battle.log(
        f"{source.name} heals {healed} ({label}). HP: {source.current_hp}/{source.max_hp}"
    )
