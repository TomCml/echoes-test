"""
Echoes Backend - Combat Engine
Main combat orchestration class.
"""
from dataclasses import dataclass, field
from random import Random
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from src.domain.entities.combat import (
    CombatEntity,
    CombatLog,
    CombatSession,
    DamageResult,
    MonsterCombatEntity,
    PlayerCombatEntity,
)
from src.domain.entities.spell import Spell
from src.domain.enums.types import CombatStatus
from src.domain.value_objects.effect import EffectPayload, StatusDefinition
from src.domain.value_objects.loot import CombatReward, LootDrop

# Import effects to register them
from src.core import effects  # noqa: F401
from src.core.engine.effect_registry import run_effects
from src.core.engine import status_engine


@dataclass
class Battle:
    """
    Runtime combat instance.
    Manages combat flow, effect execution, and victory/defeat conditions.
    """
    session: CombatSession
    player: PlayerCombatEntity
    monster: MonsterCombatEntity
    
    # Status definitions cache
    status_definitions: Dict[str, StatusDefinition] = field(default_factory=dict)
    
    # Combat log
    logs: List[CombatLog] = field(default_factory=list)
    
    # Random number generator (seeded for reproducibility if needed)
    rng: Random = field(default_factory=Random)
    
    # Last damage result (for conditional effects like lifesteal)
    last_damage: Optional[DamageResult] = None
    
    def log(self, message: str) -> None:
        """Add a message to the combat log."""
        log_entry = CombatLog.create(
            combat_session_id=self.session.id,
            turn=self.session.turn_count,
            actor=self.session.current_turn_entity,
            action_type="log",
            message=message,
        )
        self.logs.append(log_entry)
    
    def get_status_definition(self, code: str) -> Optional[StatusDefinition]:
        """Get a status definition by code."""
        return self.status_definitions.get(code)
    
    def register_status_definitions(self, definitions: List[StatusDefinition]) -> None:
        """Register status definitions for this battle."""
        for definition in definitions:
            self.status_definitions[definition.code] = definition
    
    # =========================================================================
    # Combat Flow
    # =========================================================================
    
    def start(self) -> None:
        """Start the combat."""
        self.session.start()
        self.log(f"Combat started! {self.player.name} vs {self.monster.name}")
        self.log(f"Player HP: {self.player.current_hp}/{self.player.max_hp}")
        self.log(f"Monster HP: {self.monster.current_hp}/{self.monster.max_hp}")
    
    def is_active(self) -> bool:
        """Check if combat is still active."""
        return self.session.is_active and not self.player.is_dead and not self.monster.is_dead
    
    def check_victory_conditions(self) -> Optional[str]:
        """
        Check for victory/defeat.
        Returns 'victory', 'defeat', or None if combat continues.
        """
        if self.monster.is_dead:
            self.session.end_victory()
            self.log(f"{self.monster.name} has been defeated!")
            return "victory"
        
        if self.player.is_dead:
            self.session.end_defeat()
            self.log(f"{self.player.name} has been defeated!")
            return "defeat"
        
        return None
    
    # =========================================================================
    # Player Actions
    # =========================================================================
    
    def player_cast_spell(self, spell: Spell) -> Tuple[bool, str]:
        """
        Player casts a spell.
        Returns (success, message).
        """
        if self.session.status != CombatStatus.PLAYER_TURN:
            return False, "Not your turn"
        
        # Check if spell can be used
        can_use, reason = self.player.can_use_spell(spell)
        if not can_use:
            return False, reason
        
        # Consume Echo if required
        if spell.echo_cost > 0:
            self.player.consume_echo(spell.echo_cost)
            self.log(f"{self.player.name} uses {spell.echo_cost} Echo")
        
        # Execute spell effects
        self.log(f"{self.player.name} casts {spell.name}!")
        
        effects_data = [e.to_dict() if hasattr(e, 'to_dict') else e for e in spell.effects]
        run_effects(self, self.player, self.monster, effects_data)
        
        # Set cooldown
        if spell.cooldown_turns > 0:
            self.player.set_cooldown(spell.id, spell.cooldown_turns)
        
        # Base Echo gain for attacking
        if not spell.is_ultimate:
            echo_gain = 5 + (10 if spell.spell_type.value == "SKILL" else 0)
            self.player.add_echo(echo_gain)
        
        return True, "OK"
    
    def player_basic_attack(self) -> Tuple[bool, str]:
        """Player performs a basic attack."""
        if self.session.status != CombatStatus.PLAYER_TURN:
            return False, "Not your turn"
        
        self.log(f"{self.player.name} attacks!")
        
        # Basic attack effect
        basic_effect = {
            "opcode": "damage",
            "params": {
                "formula": "AD * 1.0",
                "damage_type": "PHYSICAL",
                "can_crit": True,
                "variance": 0.1,
                "label": "attack",
            }
        }
        
        run_effects(self, self.player, self.monster, [basic_effect])
        
        # Echo gain for basic attacks
        self.player.add_echo(5)
        
        return True, "OK"
    
    def player_use_consumable(self, effects_data: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """Player uses their consumable."""
        if self.session.status != CombatStatus.PLAYER_TURN:
            return False, "Not your turn"
        
        if not self.player.use_consumable():
            return False, "No consumable uses remaining"
        
        self.log(f"{self.player.name} uses a consumable!")
        run_effects(self, self.player, self.player, effects_data)
        
        return True, "OK"
    
    def player_end_turn(self) -> None:
        """End the player's turn."""
        # Process end-of-turn status effects
        status_engine.process_turn_end(self, self.player)
        
        # Check victory conditions
        if self.check_victory_conditions():
            return
        
        # Switch to monster turn
        self.session.next_turn()
        self.log(f"--- Monster's Turn (Turn {self.session.turn_count}) ---")
        
        # Process start-of-turn for monster
        status_engine.process_turn_start(self, self.monster)
    
    # =========================================================================
    # Monster Actions
    # =========================================================================
    
    def monster_take_turn(self) -> None:
        """Monster takes its turn using AI."""
        from src.core.ai.monster_ai import select_monster_action
        
        if self.session.status != CombatStatus.MONSTER_TURN:
            return
        
        # Select and execute action
        ability = select_monster_action(self, self.monster, self.player)
        
        if ability:
            self.log(f"{self.monster.name} uses {ability.name}!")
            effects_data = [e.to_dict() if hasattr(e, 'to_dict') else e for e in ability.effects]
            run_effects(self, self.monster, self.player, effects_data)
            
            # Set cooldown
            if ability.cooldown > 0:
                self.monster.set_cooldown(ability.id, ability.cooldown)
        else:
            # Fallback basic attack
            self.log(f"{self.monster.name} attacks!")
            basic_effect = {
                "opcode": "damage",
                "params": {
                    "formula": "AD * 1.0",
                    "damage_type": "PHYSICAL",
                    "label": "attack",
                }
            }
            run_effects(self, self.monster, self.player, [basic_effect])
        
        self.monster_end_turn()
    
    def monster_end_turn(self) -> None:
        """End the monster's turn."""
        # Process end-of-turn status effects
        status_engine.process_turn_end(self, self.monster)
        
        # Check victory conditions
        if self.check_victory_conditions():
            return
        
        # Switch to player turn
        self.session.next_turn()
        self.log(f"--- Player's Turn (Turn {self.session.turn_count}) ---")
        
        # Process start-of-turn for player
        status_engine.process_turn_start(self, self.player)
    
    # =========================================================================
    # Flee
    # =========================================================================
    
    def player_flee(self) -> Tuple[bool, str]:
        """
        Attempt to flee from combat.
        Returns (success, message).
        """
        # Flee chance based on speed difference
        speed_diff = self.player.stats.speed - self.monster.stats.speed
        flee_chance = 0.5 + (speed_diff * 0.01)  # +1% per speed difference
        flee_chance = max(0.1, min(0.9, flee_chance))  # Clamp 10-90%
        
        if self.rng.random() < flee_chance:
            self.session.abandon()
            self.log(f"{self.player.name} fled from combat!")
            return True, "Escaped!"
        else:
            self.log(f"{self.player.name} failed to flee!")
            # Failed flee attempt ends turn
            self.player_end_turn()
            return False, "Failed to escape!"
    
    # =========================================================================
    # Rewards
    # =========================================================================
    
    def calculate_rewards(self) -> CombatReward:
        """Calculate rewards for victory."""
        if self.session.status != CombatStatus.VICTORY:
            return CombatReward(xp_gained=0, gold_gained=0)
        
        # XP reward
        xp = self.monster.xp_reward
        
        # Gold reward (random in range)
        gold = self.rng.randint(
            self.monster.gold_reward_min,
            self.monster.gold_reward_max,
        )
        
        # TODO: Roll loot table for drops
        loot_drops: List[LootDrop] = []
        
        return CombatReward(
            xp_gained=xp,
            gold_gained=gold,
            loot_drops=tuple(loot_drops),
        )
    
    # =========================================================================
    # State Sync
    # =========================================================================
    
    def sync_to_session(self) -> None:
        """Sync combat entity state back to session for persistence."""
        self.session.player_current_hp = self.player.current_hp
        self.session.player_max_hp = self.player.max_hp
        self.session.player_echo_current = self.player.echo_current
        self.session.player_echo_max = self.player.echo_max
        self.session.player_statuses = self.player.statuses.copy()
        self.session.player_gauges = self.player.gauges.copy()
        
        self.session.monster_current_hp = self.monster.current_hp
        self.session.monster_max_hp = self.monster.max_hp
        self.session.monster_statuses = self.monster.statuses.copy()
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get a summary of the current combat state."""
        return {
            "turn": self.session.turn_count,
            "status": self.session.status.value,
            "current_turn": self.session.current_turn_entity,
            "player": {
                "name": self.player.name,
                "hp": self.player.current_hp,
                "max_hp": self.player.max_hp,
                "echo": self.player.echo_current,
                "echo_max": self.player.echo_max,
                "statuses": status_engine.get_status_summary(self.player),
                "shield": self.player.gauges.get("shield", 0),
            },
            "monster": {
                "name": self.monster.name,
                "hp": self.monster.current_hp,
                "max_hp": self.monster.max_hp,
                "statuses": status_engine.get_status_summary(self.monster),
            },
            "logs": [log.message for log in self.logs[-10:]],  # Last 10 logs
        }
