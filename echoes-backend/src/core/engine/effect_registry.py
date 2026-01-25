"""
Echoes Backend - Effect Registry
Central registry for effect opcodes with decorator-based registration.
"""
from typing import TYPE_CHECKING, Any, Callable, Dict, List
import logging

if TYPE_CHECKING:
    from src.core.engine.combat_engine import Battle
    from src.domain.entities.combat import CombatEntity

logger = logging.getLogger(__name__)

# Type alias for effect functions
EffectFn = Callable[["Battle", "CombatEntity", "CombatEntity", Dict[str, Any]], None]

# Global registry of opcodes
REGISTRY: Dict[str, EffectFn] = {}


def register(opcode: str) -> Callable[[EffectFn], EffectFn]:
    """
    Decorator to register an effect opcode.
    
    Usage:
        @register("damage")
        def effect_damage(battle, source, target, params):
            ...
    """
    def decorator(fn: EffectFn) -> EffectFn:
        if opcode in REGISTRY:
            logger.warning(f"Overwriting existing opcode: {opcode}")
        REGISTRY[opcode] = fn
        logger.debug(f"Registered opcode: {opcode}")
        return fn
    return decorator


def run_effects(
    battle: "Battle",
    source: "CombatEntity",
    target: "CombatEntity",
    effects: List[Dict[str, Any]],
) -> None:
    """
    Execute a list of effects in order.
    
    Args:
        battle: The Battle instance for context and logging
        source: The entity performing the action
        target: The entity receiving the action
        effects: List of effect payloads to execute
    """
    # Sort effects by order
    sorted_effects = sorted(effects, key=lambda e: e.get("order", 0))
    
    for effect in sorted_effects:
        opcode = effect.get("opcode")
        params = effect.get("params", {})
        
        if not opcode:
            battle.log("[WARN] Effect missing opcode")
            continue
        
        fn = REGISTRY.get(opcode)
        if not fn:
            battle.log(f"[WARN] Unknown opcode: {opcode}")
            continue
        
        try:
            fn(battle, source, target, params)
        except Exception as e:
            battle.log(f"[ERROR] Effect {opcode} failed: {e}")
            logger.exception(f"Effect {opcode} raised an exception")
            raise


def get_registered_opcodes() -> List[str]:
    """Get list of all registered opcodes."""
    return list(REGISTRY.keys())


def is_opcode_registered(opcode: str) -> bool:
    """Check if an opcode is registered."""
    return opcode in REGISTRY
