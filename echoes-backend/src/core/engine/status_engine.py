"""
Echoes Backend - Status Engine
Handles status effect ticks and duration management.
"""
from typing import TYPE_CHECKING, List

from src.core.engine.effect_registry import run_effects

if TYPE_CHECKING:
    from src.core.engine.combat_engine import Battle
    from src.domain.entities.combat import CombatEntity


def process_turn_start(battle: "Battle", entity: "CombatEntity") -> None:
    """
    Process status effects at the start of a turn.
    Execute ON_TURN_START tick effects.
    """
    _process_status_ticks(battle, entity, "ON_TURN_START")


def process_turn_end(battle: "Battle", entity: "CombatEntity") -> None:
    """
    Process status effects at the end of a turn.
    Execute ON_TURN_END tick effects and decrement durations.
    """
    _process_status_ticks(battle, entity, "ON_TURN_END")
    _decrement_status_durations(battle, entity)
    entity.tick_cooldowns()


def _process_status_ticks(
    battle: "Battle",
    entity: "CombatEntity",
    trigger: str,
) -> None:
    """
    Execute tick effects for all statuses with the given trigger.
    """
    for status_code, instance in list(entity.statuses.items()):
        status_def = battle.get_status_definition(status_code)
        if not status_def:
            # Unknown status, skip tick processing
            continue
        
        if status_def.tick_trigger == trigger and status_def.tick_effect:
            # Execute tick effect once per stack if stackable, else once
            tick_count = instance.stacks if status_def.is_stackable else 1
            
            for _ in range(tick_count):
                # For tick effects, source is the entity itself
                run_effects(
                    battle,
                    entity,
                    entity,
                    [status_def.tick_effect.to_dict()],
                )


def _decrement_status_durations(battle: "Battle", entity: "CombatEntity") -> None:
    """
    Decrement duration of all status effects and remove expired ones.
    """
    expired: List[str] = []
    
    for code, instance in entity.statuses.items():
        instance.remaining -= 1
        if instance.remaining <= 0:
            expired.append(code)
    
    for code in expired:
        del entity.statuses[code]
        battle.log(f"{entity.name}'s {code} expired")


def process_on_hit(
    battle: "Battle",
    attacker: "CombatEntity",
    target: "CombatEntity",
) -> None:
    """
    Process ON_HIT triggers when an attack lands.
    """
    # Attacker's ON_HIT statuses
    for status_code, instance in list(attacker.statuses.items()):
        status_def = battle.get_status_definition(status_code)
        if status_def and status_def.tick_trigger == "ON_HIT" and status_def.tick_effect:
            run_effects(
                battle,
                attacker,
                target,
                [status_def.tick_effect.to_dict()],
            )


def process_on_damaged(
    battle: "Battle",
    target: "CombatEntity",
    attacker: "CombatEntity",
) -> None:
    """
    Process ON_DAMAGED triggers when an entity takes damage.
    """
    for status_code, instance in list(target.statuses.items()):
        status_def = battle.get_status_definition(status_code)
        if status_def and status_def.tick_trigger == "ON_DAMAGED" and status_def.tick_effect:
            run_effects(
                battle,
                target,
                attacker,
                [status_def.tick_effect.to_dict()],
            )


def get_active_status_codes(entity: "CombatEntity") -> List[str]:
    """Get list of all active status codes on an entity."""
    return list(entity.statuses.keys())


def get_status_summary(entity: "CombatEntity") -> str:
    """Get a human-readable summary of active statuses."""
    if not entity.statuses:
        return "No active statuses"
    
    parts = []
    for code, instance in entity.statuses.items():
        if instance.stacks > 1:
            parts.append(f"{code} x{instance.stacks} ({instance.remaining}t)")
        else:
            parts.append(f"{code} ({instance.remaining}t)")
    
    return ", ".join(parts)
