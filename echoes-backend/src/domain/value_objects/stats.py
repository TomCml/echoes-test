"""
Echoes Backend - Stats Value Objects
Immutable data structures for character/item statistics.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class StatsBlock:
    """
    Immutable block of combat statistics.
    Used for base stats, equipment bonuses, and calculated totals.
    """
    max_hp: int = 0
    ad: int = 0  # Attack Damage
    ap: int = 0  # Ability Power
    armor: int = 0
    mr: int = 0  # Magic Resistance
    speed: int = 0
    crit_chance: float = 0.0
    crit_damage: float = 1.5
    
    def __add__(self, other: "StatsBlock") -> "StatsBlock":
        """Add two StatsBlocks together."""
        return StatsBlock(
            max_hp=self.max_hp + other.max_hp,
            ad=self.ad + other.ad,
            ap=self.ap + other.ap,
            armor=self.armor + other.armor,
            mr=self.mr + other.mr,
            speed=self.speed + other.speed,
            crit_chance=self.crit_chance + other.crit_chance,
            crit_damage=self.crit_damage,  # Crit damage doesn't stack additively
        )
    
    def __mul__(self, factor: float) -> "StatsBlock":
        """Multiply all stats by a factor."""
        return StatsBlock(
            max_hp=int(self.max_hp * factor),
            ad=int(self.ad * factor),
            ap=int(self.ap * factor),
            armor=int(self.armor * factor),
            mr=int(self.mr * factor),
            speed=int(self.speed * factor),
            crit_chance=self.crit_chance * factor,
            crit_damage=self.crit_damage,
        )
    
    def scale(self, level: int, scaling: "StatsScaling") -> "StatsBlock":
        """Apply level scaling to produce final stats."""
        return StatsBlock(
            max_hp=self.max_hp + int(scaling.hp_per_level * level),
            ad=self.ad + int(scaling.ad_per_level * level),
            ap=self.ap + int(scaling.ap_per_level * level),
            armor=self.armor + int(scaling.armor_per_level * level),
            mr=self.mr + int(scaling.mr_per_level * level),
            speed=self.speed,
            crit_chance=self.crit_chance,
            crit_damage=self.crit_damage,
        )
    
    @classmethod
    def zero(cls) -> "StatsBlock":
        """Create a StatsBlock with all zeros."""
        return cls()


@dataclass(frozen=True)
class StatsScaling:
    """
    Scaling factors applied per level.
    Used for both player and monster level scaling.
    """
    hp_per_level: float = 0.0
    ad_per_level: float = 0.0
    ap_per_level: float = 0.0
    armor_per_level: float = 0.0
    mr_per_level: float = 0.0
    
    @classmethod
    def zero(cls) -> "StatsScaling":
        """Create a StatsScaling with all zeros."""
        return cls()
