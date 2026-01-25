"""
Echoes Backend - Monster AI
Selects actions for monsters based on behavior patterns.
"""
from typing import TYPE_CHECKING, List, Optional

from src.core.engine.formula_engine import eval_formula

if TYPE_CHECKING:
    from src.core.engine.combat_engine import Battle
    from src.domain.entities.combat import CombatEntity, MonsterCombatEntity
    from src.domain.entities.monster import MonsterAbility


def select_monster_action(
    battle: "Battle",
    monster: "MonsterCombatEntity",
    target: "CombatEntity",
) -> Optional["MonsterAbility"]:
    """
    Select the best action for a monster based on its AI behavior.
    
    Returns the selected ability, or None for basic attack.
    """
    behavior = monster.ai_behavior
    
    # Get available abilities (not on cooldown)
    available = [
        ability for ability in monster.abilities
        if not monster.is_on_cooldown(ability.id)
    ]
    
    if not available:
        return None
    
    # Filter by conditions
    valid_abilities = []
    for ability in available:
        if _check_ability_condition(battle, monster, target, ability):
            valid_abilities.append(ability)
    
    if not valid_abilities:
        return None
    
    # Select based on behavior
    if behavior == "basic":
        return _select_basic(valid_abilities, battle)
    elif behavior == "aggressive":
        return _select_aggressive(valid_abilities, monster, target, battle)
    elif behavior == "defensive":
        return _select_defensive(valid_abilities, monster, target, battle)
    elif behavior == "healer":
        return _select_healer(valid_abilities, monster, battle)
    elif behavior == "balanced":
        return _select_balanced(valid_abilities, monster, target, battle)
    elif behavior == "boss":
        return _select_boss(valid_abilities, monster, target, battle)
    else:
        return _select_basic(valid_abilities, battle)


def _check_ability_condition(
    battle: "Battle",
    monster: "MonsterCombatEntity",
    target: "CombatEntity",
    ability: "MonsterAbility",
) -> bool:
    """Check if ability's condition is met."""
    if not ability.condition_expr:
        return True
    
    try:
        result = eval_formula(ability.condition_expr, monster, target)
        return bool(result)
    except Exception:
        return True  # Default to allowed on error


def _select_basic(
    abilities: List["MonsterAbility"],
    battle: "Battle",
) -> Optional["MonsterAbility"]:
    """
    Basic AI: Random selection weighted by priority.
    """
    if not abilities:
        return None
    
    # Weight by priority
    total_weight = sum(a.priority for a in abilities)
    roll = battle.rng.random() * total_weight
    
    cumulative = 0
    for ability in abilities:
        cumulative += ability.priority
        if roll <= cumulative:
            return ability
    
    return abilities[0]


def _select_aggressive(
    abilities: List["MonsterAbility"],
    monster: "MonsterCombatEntity",
    target: "CombatEntity",
    battle: "Battle",
) -> Optional["MonsterAbility"]:
    """
    Aggressive AI: Prioritize high-damage abilities.
    More likely to use abilities when target is low HP.
    """
    if not abilities:
        return None
    
    # Sort by priority (assuming higher priority = more damage)
    sorted_abilities = sorted(abilities, key=lambda a: a.priority, reverse=True)
    
    # If target is low HP, always use highest priority
    if target.hp_percent < 0.3:
        return sorted_abilities[0]
    
    # 70% chance to use high priority, 30% random
    if battle.rng.random() < 0.7:
        return sorted_abilities[0]
    
    return _select_basic(abilities, battle)


def _select_defensive(
    abilities: List["MonsterAbility"],
    monster: "MonsterCombatEntity",
    target: "CombatEntity",
    battle: "Battle",
) -> Optional["MonsterAbility"]:
    """
    Defensive AI: Prioritize healing/shielding when low HP.
    """
    if not abilities:
        return None
    
    # If low HP, look for healing abilities
    if monster.hp_percent < 0.4:
        healing_abilities = [
            a for a in abilities
            if any(
                e.opcode in ("heal", "heal_percent_max_hp", "shield")
                for e in a.effects if hasattr(e, 'opcode')
            ) or "heal" in a.name.lower()
        ]
        if healing_abilities:
            return healing_abilities[0]
    
    return _select_basic(abilities, battle)


def _select_healer(
    abilities: List["MonsterAbility"],
    monster: "MonsterCombatEntity",
    battle: "Battle",
) -> Optional["MonsterAbility"]:
    """
    Healer AI: Always prioritize healing when possible.
    """
    # Look for healing abilities
    healing_abilities = [
        a for a in abilities
        if any(
            getattr(e, 'opcode', '') in ("heal", "heal_percent_max_hp")
            for e in a.effects
        ) or "heal" in a.name.lower()
    ]
    
    if healing_abilities and monster.hp_percent < 0.8:
        return healing_abilities[0]
    
    return _select_basic(abilities, battle)


def _select_balanced(
    abilities: List["MonsterAbility"],
    monster: "MonsterCombatEntity",
    target: "CombatEntity",
    battle: "Battle",
) -> Optional["MonsterAbility"]:
    """
    Balanced AI: Mix of offense and defense based on situation.
    """
    # Low HP: defensive
    if monster.hp_percent < 0.3:
        return _select_defensive(abilities, monster, target, battle)
    
    # Target low HP: aggressive
    if target.hp_percent < 0.3:
        return _select_aggressive(abilities, monster, target, battle)
    
    # Otherwise: weighted random
    return _select_basic(abilities, battle)


def _select_boss(
    abilities: List["MonsterAbility"],
    monster: "MonsterCombatEntity",
    target: "CombatEntity",
    battle: "Battle",
) -> Optional["MonsterAbility"]:
    """
    Boss AI: Smarter pattern-based selection.
    Uses high-priority abilities more often, creates varied attack patterns.
    """
    if not abilities:
        return None
    
    turn = battle.session.turn_count
    
    # Phase-based behavior
    if monster.hp_percent > 0.7:
        # Phase 1: Normal attacks
        return _select_basic(abilities, battle)
    
    elif monster.hp_percent > 0.4:
        # Phase 2: More aggressive
        sorted_abilities = sorted(abilities, key=lambda a: a.priority, reverse=True)
        if battle.rng.random() < 0.6:
            return sorted_abilities[0]
        return _select_basic(abilities, battle)
    
    else:
        # Phase 3: Enraged - always use strongest
        sorted_abilities = sorted(abilities, key=lambda a: a.priority, reverse=True)
        return sorted_abilities[0]
