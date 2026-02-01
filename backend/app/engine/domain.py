from dataclasses import dataclass, field
from typing import Dict, Any, List, Set
import random


@dataclass
class Stats:
    MAX_HP: int
    HP: int
    AD: int
    AP: int = 0
    ARMOR: int = 0
    MR: int = 0
    SPEED: int = 0
    CRIT_CHANCE: float = 0.0
    CRIT_DAMAGE: float = 1.5

    @property
    def DEF(self) -> int:
        """Alias rétrocompat — certaines formules utilisent DEF."""
        return self.ARMOR


@dataclass
class Entity:
    id: str
    name: str
    stats: Stats
    tags: Set[str] = field(default_factory=set)
    statuses: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # code -> {remaining, stacks}
    gauges: Dict[str, int] = field(default_factory=dict)
    cds: Dict[str, int] = field(default_factory=dict)


@dataclass
class Battle:
    a: Entity
    b: Entity
    turn: int = 1
    status_defs: Dict[str, Any] = field(default_factory=dict)
    log: List[str] = field(default_factory=list)
    rng: random.Random = field(default_factory=lambda: random.Random(42))

    def other(self, who: "Entity") -> "Entity":
        return self.b if who.id == self.a.id else self.a
