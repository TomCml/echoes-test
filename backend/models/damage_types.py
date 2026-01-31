from enum import StrEnum


class DamageType(StrEnum):
    """Types of damage that spells can inflict."""
    PHYSICAL = "physical"
    MAGICAL = "magical"
    TRUE = "true"  # True damage ignores resistances
    HEALING = "healing"  # For healing spells
