"""
Echoes Backend - Status Effects
Opcodes for applying and removing status effects.
"""
from typing import Any, Dict, TYPE_CHECKING

from src.core.engine.effect_registry import register
from src.core.engine.formula_engine import eval_formula

if TYPE_CHECKING:
    from src.core.engine.combat_engine import Battle
    from src.domain.entities.combat import CombatEntity


@register("apply_status")
def effect_apply_status(
    battle: "Battle",
    source: "CombatEntity",
    target: "CombatEntity",
    params: Dict[str, Any],
) -> None:
    """
    Apply a status effect to the target.
    
    Params:
        - status_code: str - The status code (e.g., "BURN", "FREEZE")
        - duration_turns: int - Duration in turns
        - stacks: int - Number of stacks to apply (default: 1)
        - chance: str - Formula for application chance (default: "1")
        - max_stacks: int - Maximum stacks (optional)
    """
    status_code = params.get("status_code", "")
    if not status_code:
        battle.log("[WARN] apply_status missing status_code")
        return
    
    duration = int(params.get("duration_turns", 1))
    stacks = int(params.get("stacks", 1))
    chance_expr = str(params.get("chance", "1"))
    max_stacks = params.get("max_stacks")
    
    # Calculate chance
    chance = min(1.0, max(0.0, eval_formula(chance_expr, source, target)))
    
    # Roll for application
    if battle.rng and battle.rng.random() > chance:
        battle.log(f"{target.name} resisted {status_code}")
        return
    
    # Apply status
    max_stacks_int = int(max_stacks) if max_stacks is not None else None
    target.add_status(status_code, duration, stacks, max_stacks_int)
    
    battle.log(f"{target.name} gains {status_code} ({duration} turns, {stacks} stacks)")


@register("remove_status")
def effect_remove_status(
    battle: "Battle",
    source: "CombatEntity",
    target: "CombatEntity",
    params: Dict[str, Any],
) -> None:
    """
    Remove a status effect from the target.
    
    Params:
        - status_code: str - The status code to remove
        - all_debuffs: bool - Remove all debuffs instead (optional)
        - all_buffs: bool - Remove all buffs instead (optional)
    """
    status_code = params.get("status_code")
    all_debuffs = params.get("all_debuffs", False)
    all_buffs = params.get("all_buffs", False)
    
    if all_debuffs:
        # Get debuffs from status definitions
        removed = []
        for code in list(target.statuses.keys()):
            status_def = battle.get_status_definition(code)
            if status_def and status_def.is_debuff:
                target.remove_status(code)
                removed.append(code)
        if removed:
            battle.log(f"{target.name} cleansed: {', '.join(removed)}")
        return
    
    if all_buffs:
        removed = []
        for code in list(target.statuses.keys()):
            status_def = battle.get_status_definition(code)
            if status_def and not status_def.is_debuff:
                target.remove_status(code)
                removed.append(code)
        if removed:
            battle.log(f"{target.name} lost buffs: {', '.join(removed)}")
        return
    
    if status_code:
        if target.remove_status(status_code):
            battle.log(f"{target.name} lost {status_code}")
        else:
            battle.log(f"{target.name} doesn't have {status_code}")


@register("extend_status")
def effect_extend_status(
    battle: "Battle",
    source: "CombatEntity",
    target: "CombatEntity",
    params: Dict[str, Any],
) -> None:
    """
    Extend the duration of a status effect.
    
    Params:
        - status_code: str - The status code to extend
        - duration_turns: int - Turns to add
    """
    status_code = params.get("status_code", "")
    duration = int(params.get("duration_turns", 1))
    
    if status_code in target.statuses:
        target.statuses[status_code].remaining += duration
        battle.log(f"{target.name}'s {status_code} extended by {duration} turns")


@register("transfer_status")
def effect_transfer_status(
    battle: "Battle",
    source: "CombatEntity",
    target: "CombatEntity",
    params: Dict[str, Any],
) -> None:
    """
    Transfer a status from source to target.
    
    Params:
        - status_code: str - The status code to transfer
    """
    status_code = params.get("status_code", "")
    
    if status_code in source.statuses:
        instance = source.statuses[status_code]
        target.add_status(status_code, instance.remaining, instance.stacks)
        source.remove_status(status_code)
        battle.log(f"{status_code} transferred from {source.name} to {target.name}")
