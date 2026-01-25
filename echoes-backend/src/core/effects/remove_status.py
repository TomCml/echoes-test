"""
Echoes Backend - Remove Status Effect
Re-export for backwards compatibility.
"""
# The remove_status opcode is defined in apply_status.py
from src.core.effects.apply_status import effect_remove_status as remove_status

__all__ = ["remove_status"]
