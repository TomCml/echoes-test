"""
Echoes Backend - Combat Domain Entities
Runtime entities for combat sessions.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from src.domain.enums.types import CombatStatus, DamageType
from src.domain.value_objects.effect import StatusInstance
from src.domain.value_objects.stats import StatsBlock


@dataclass
class DamageResult:
    """Result of applying damage to an entity."""
    raw_damage: int
    mitigated_damage: int
    final_damage: int
    damage_type: DamageType
    was_critical: bool = False
    overkill: int = 0


@dataclass
class CombatEntity:
    """
    Base entity participating in combat.
    Contains runtime combat state.
    """
    id: UUID
    name: str
    stats: StatsBlock
    current_hp: int
    max_hp: int
    statuses: Dict[str, StatusInstance] = field(default_factory=dict)
    gauges: Dict[str, int] = field(default_factory=dict)  # e.g., "shield"
    cooldowns: Dict[UUID, int] = field(default_factory=dict)  # spell_id -> turns remaining
    
    @property
    def is_dead(self) -> bool:
        """Check if the entity is dead."""
        return self.current_hp <= 0
    
    @property
    def hp_percent(self) -> float:
        """Get HP as a percentage."""
        if self.max_hp <= 0:
            return 0.0
        return self.current_hp / self.max_hp
    
    def take_damage(self, amount: int, damage_type: DamageType) -> DamageResult:
        """
        Apply damage with damage type mitigation.
        Returns detailed damage result.
        """
        # Check for shield first
        shield = self.gauges.get("shield", 0)
        if shield > 0:
            absorbed = min(shield, amount)
            self.gauges["shield"] = shield - absorbed
            amount -= absorbed
        
        # Calculate mitigation based on damage type
        if damage_type == DamageType.TRUE:
            mitigated = amount
        elif damage_type == DamageType.PHYSICAL:
            reduction = self.stats.armor / (100 + self.stats.armor) if self.stats.armor >= 0 else 0
            mitigated = int(amount * (1 - reduction))
        elif damage_type == DamageType.MAGIC:
            reduction = self.stats.mr / (100 + self.stats.mr) if self.stats.mr >= 0 else 0
            mitigated = int(amount * (1 - reduction))
        elif damage_type == DamageType.MIXED:
            # Split damage 50/50, apply both resistances
            phys = amount // 2
            magic = amount - phys
            phys_red = self.stats.armor / (100 + self.stats.armor) if self.stats.armor >= 0 else 0
            magic_red = self.stats.mr / (100 + self.stats.mr) if self.stats.mr >= 0 else 0
            mitigated = int(phys * (1 - phys_red)) + int(magic * (1 - magic_red))
        else:
            mitigated = amount
        
        # Apply damage
        actual = min(mitigated, self.current_hp)
        self.current_hp -= actual
        
        return DamageResult(
            raw_damage=amount,
            mitigated_damage=mitigated,
            final_damage=actual,
            damage_type=damage_type,
            was_critical=False,
            overkill=max(0, mitigated - actual),
        )
    
    def heal(self, amount: int) -> int:
        """
        Heal the entity.
        Returns actual amount healed.
        """
        actual = min(amount, self.max_hp - self.current_hp)
        self.current_hp += actual
        return actual
    
    def has_status(self, code: str) -> bool:
        """Check if entity has a status."""
        return code in self.statuses
    
    def get_status_stacks(self, code: str) -> int:
        """Get the number of stacks for a status."""
        if code in self.statuses:
            return self.statuses[code].stacks
        return 0
    
    def add_status(self, code: str, duration: int, stacks: int = 1, max_stacks: Optional[int] = None) -> None:
        """Add or refresh a status effect."""
        if code in self.statuses:
            existing = self.statuses[code]
            existing.remaining = max(existing.remaining, duration)
            existing.add_stacks(stacks, max_stacks)
        else:
            self.statuses[code] = StatusInstance(remaining=duration, stacks=stacks)
    
    def remove_status(self, code: str) -> bool:
        """Remove a status effect. Returns True if it existed."""
        if code in self.statuses:
            del self.statuses[code]
            return True
        return False
    
    def tick_cooldowns(self) -> None:
        """Decrement all cooldowns by 1."""
        expired = []
        for spell_id in self.cooldowns:
            self.cooldowns[spell_id] -= 1
            if self.cooldowns[spell_id] <= 0:
                expired.append(spell_id)
        for spell_id in expired:
            del self.cooldowns[spell_id]
    
    def set_cooldown(self, spell_id: UUID, turns: int) -> None:
        """Set a spell on cooldown."""
        if turns > 0:
            self.cooldowns[spell_id] = turns
    
    def is_on_cooldown(self, spell_id: UUID) -> bool:
        """Check if a spell is on cooldown."""
        return spell_id in self.cooldowns


@dataclass
class PlayerCombatEntity(CombatEntity):
    """
    Player entity in combat with Echo gauge.
    """
    player_id: UUID = field(default_factory=uuid4)
    echo_current: int = 0
    echo_max: int = 100
    available_spells: List = field(default_factory=list)  # List[Spell]
    consumable_uses_remaining: int = 1
    
    def add_echo(self, amount: int) -> int:
        """Add Echo. Returns actual amount added."""
        actual = min(amount, self.echo_max - self.echo_current)
        self.echo_current += actual
        return actual
    
    def consume_echo(self, cost: int) -> bool:
        """Consume Echo. Returns True if successful."""
        if self.echo_current >= cost:
            self.echo_current -= cost
            return True
        return False
    
    def can_use_spell(self, spell) -> Tuple[bool, str]:
        """
        Check if a spell can be used.
        Returns (can_use, reason).
        """
        if self.is_on_cooldown(spell.id):
            remaining = self.cooldowns.get(spell.id, 0)
            return False, f"On cooldown ({remaining} turns)"
        
        if spell.echo_cost > 0 and self.echo_current < spell.echo_cost:
            return False, f"Not enough Echo ({self.echo_current}/{spell.echo_cost})"
        
        return True, "OK"
    
    def use_consumable(self) -> bool:
        """Use the consumable. Returns True if uses remain."""
        if self.consumable_uses_remaining > 0:
            self.consumable_uses_remaining -= 1
            return True
        return False


@dataclass
class MonsterCombatEntity(CombatEntity):
    """
    Monster entity in combat.
    """
    blueprint_id: UUID = field(default_factory=uuid4)
    ai_behavior: str = "basic"
    abilities: List = field(default_factory=list)  # List[MonsterAbility]
    loot_table_id: Optional[UUID] = None
    xp_reward: int = 0
    gold_reward_min: int = 0
    gold_reward_max: int = 0


@dataclass
class CombatSession:
    """
    Complete combat session state.
    Persisted to database during combat.
    """
    id: UUID
    player_id: UUID
    monster_blueprint_id: UUID
    monster_level: int
    status: CombatStatus = CombatStatus.PENDING
    turn_count: int = 0
    current_turn_entity: str = "player"  # "player" or "monster"
    
    # Player state
    player_current_hp: int = 0
    player_max_hp: int = 0
    player_echo_current: int = 0
    player_echo_max: int = 100
    player_statuses: Dict[str, StatusInstance] = field(default_factory=dict)
    player_gauges: Dict[str, int] = field(default_factory=dict)
    
    # Monster state
    monster_current_hp: int = 0
    monster_max_hp: int = 0
    monster_statuses: Dict[str, StatusInstance] = field(default_factory=dict)
    
    # Timestamps
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    
    @classmethod
    def create(
        cls,
        player_id: UUID,
        monster_blueprint_id: UUID,
        monster_level: int,
        player_max_hp: int,
        monster_max_hp: int,
    ) -> "CombatSession":
        """Create a new combat session."""
        return cls(
            id=uuid4(),
            player_id=player_id,
            monster_blueprint_id=monster_blueprint_id,
            monster_level=monster_level,
            player_current_hp=player_max_hp,
            player_max_hp=player_max_hp,
            monster_current_hp=monster_max_hp,
            monster_max_hp=monster_max_hp,
        )
    
    def start(self) -> None:
        """Start the combat."""
        self.status = CombatStatus.PLAYER_TURN
        self.turn_count = 1
    
    def next_turn(self) -> None:
        """Advance to the next turn."""
        if self.current_turn_entity == "player":
            self.current_turn_entity = "monster"
            self.status = CombatStatus.MONSTER_TURN
        else:
            self.current_turn_entity = "player"
            self.status = CombatStatus.PLAYER_TURN
            self.turn_count += 1
    
    def end_victory(self) -> None:
        """End combat with player victory."""
        self.status = CombatStatus.VICTORY
        self.ended_at = datetime.utcnow()
    
    def end_defeat(self) -> None:
        """End combat with player defeat."""
        self.status = CombatStatus.DEFEAT
        self.ended_at = datetime.utcnow()
    
    def abandon(self) -> None:
        """Player abandoned/fled combat."""
        self.status = CombatStatus.ABANDONED
        self.ended_at = datetime.utcnow()
    
    @property
    def is_active(self) -> bool:
        """Check if combat is still active."""
        return self.status in (
            CombatStatus.PENDING,
            CombatStatus.IN_PROGRESS,
            CombatStatus.PLAYER_TURN,
            CombatStatus.MONSTER_TURN,
        )


@dataclass
class CombatLog:
    """
    Single log entry from combat.
    """
    id: UUID
    combat_session_id: UUID
    turn: int
    actor: str  # "player" or "monster"
    action_type: str  # "spell", "basic_attack", "consumable", "status_tick"
    spell_id: Optional[UUID] = None
    damage_dealt: int = 0
    damage_type: Optional[DamageType] = None
    was_critical: bool = False
    echo_gained: int = 0
    message: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def create(
        cls,
        combat_session_id: UUID,
        turn: int,
        actor: str,
        action_type: str,
        message: str,
        **kwargs,
    ) -> "CombatLog":
        """Create a combat log entry."""
        return cls(
            id=uuid4(),
            combat_session_id=combat_session_id,
            turn=turn,
            actor=actor,
            action_type=action_type,
            message=message,
            **kwargs,
        )
