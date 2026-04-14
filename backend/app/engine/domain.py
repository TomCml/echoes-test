"""
Engine Domain — Classes runtime du moteur de combat.

Aligné sur le diagramme UML v4 Opcode Engine :
- StatsBlock complet (9 stats)
- CombatStatus enum
- CombatLogEntry structuré
- Battle player/monster avec gestion d'état
"""
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Dict, Any, List, Set
import random


# ─── Enums ───────────────────────────────────────────────

class CombatStatus(StrEnum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    PLAYER_TURN = "PLAYER_TURN"
    MONSTER_TURN = "MONSTER_TURN"
    VICTORY = "VICTORY"
    DEFEAT = "DEFEAT"
    ABANDONED = "ABANDONED"


# ─── Value Objects ───────────────────────────────────────

@dataclass
class Stats:
    """
    StatsBlock complet — compatible avec les formules du moteur.

    Les préfixes dans eval_formula :
      - S_AD, S_AP, S_ARMOR ... → stats du caster (src)
      - T_AD, T_AP, T_ARMOR ... → stats de la cible (tgt)
      - Sans préfixe → stats du caster (rétro-compatible)
    """
    MAX_HP: int
    HP: int
    AD: int
    AP: int = 0
    ARMOR: int = 0
    MR: int = 0
    SPEED: int = 10
    CRIT_CHANCE: float = 0.0    # 0.0 → 1.0
    CRIT_DAMAGE: float = 1.5    # Multiplicateur critique


@dataclass
class CombatLogEntry:
    """Entrée structurée du journal de combat."""
    turn: int
    message: str


# ─── Combat Entities ─────────────────────────────────────

@dataclass
class Entity:
    """
    État runtime d'une entité en combat.

    - statuses: Dict[code → {remaining, stacks}]
    - gauges:   Dict[name → value]  (ex: gauges["echo"])
    - cds:      Dict[spell_code → remaining turns]
    """
    id: str
    name: str
    stats: Stats
    tags: Set[str] = field(default_factory=set)
    statuses: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    gauges: Dict[str, int] = field(default_factory=dict)
    cds: Dict[str, int] = field(default_factory=dict)

    @property
    def is_alive(self) -> bool:
        return self.stats.HP > 0


# ─── Battle Session ──────────────────────────────────────

@dataclass
class Battle:
    """
    Session de combat — orchestre les entités et le moteur d'effets.

    Flux :
      1. start()       → status = IN_PROGRESS, turn = 1
      2. execute_spell(caster, spell, target) → run_effects
      3. end_turn(who)  → tick statuses, décrementer cooldowns
      4. next_turn()    → incrémenter turn, alterner PLAYER_TURN / MONSTER_TURN
      5. Répéter jusqu'à is_finished()
    """
    player: Entity
    monster: Entity
    turn: int = 0
    status: CombatStatus = CombatStatus.PENDING
    status_defs: Dict[str, Any] = field(default_factory=dict)
    log: List[CombatLogEntry] = field(default_factory=list)
    rng: random.Random = field(default_factory=random.Random)

    def other(self, who: "Entity") -> "Entity":
        """Retourne l'adversaire de `who`."""
        return self.monster if who.id == self.player.id else self.player

    def add_log(self, message: str) -> None:
        """Ajoute une entrée au journal avec le numéro de tour courant."""
        self.log.append(CombatLogEntry(turn=self.turn, message=message))

    def start(self) -> None:
        """Initialise le combat."""
        self.turn = 1
        self.status = CombatStatus.PLAYER_TURN
        self.add_log(f"Combat begins: {self.player.name} vs {self.monster.name}")

    def next_turn(self) -> None:
        """Passe au tour suivant en alternant les joueurs."""
        self.turn += 1
        if self.status == CombatStatus.PLAYER_TURN:
            self.status = CombatStatus.MONSTER_TURN
        elif self.status == CombatStatus.MONSTER_TURN:
            self.status = CombatStatus.PLAYER_TURN

    def is_finished(self) -> bool:
        """Vérifie si le combat est terminé."""
        if not self.player.is_alive:
            self.status = CombatStatus.DEFEAT
            return True
        if not self.monster.is_alive:
            self.status = CombatStatus.VICTORY
            return True
        return False

    def get_winner(self) -> "Entity | None":
        """Retourne le gagnant ou None si le combat n'est pas fini."""
        if self.status == CombatStatus.VICTORY:
            return self.player
        if self.status == CombatStatus.DEFEAT:
            return self.monster
        return None
