from dataclasses import dataclass, field
from typing import Dict, Any, List, Set
import random

@dataclass
class Stats:
    MAX_HP: int
    HP: int
    AD: int
    DEF: int
  
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
