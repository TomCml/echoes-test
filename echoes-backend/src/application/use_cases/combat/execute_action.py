"""
Echoes Backend - Execute Combat Action Use Case
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from src.application.interfaces.repositories import (
    IPlayerRepository,
    IMonsterRepository,
    ICombatRepository,
    IItemRepository,
)
from src.application.dto.combat_dto import (
    CombatStateDTO,
    CombatActionResultDTO,
    CombatRewardDTO,
    EntityStateDTO,
    PlayerStateDTO,
)
from src.domain.entities.combat import PlayerCombatEntity, MonsterCombatEntity
from src.domain.entities.spell import Spell
from src.domain.value_objects.stats import StatsBlock
from src.domain.enums.types import CombatStatus, SpellType
from src.core.engine.combat_engine import Battle


@dataclass
class ExecuteActionInput:
    """Input for executing a combat action."""
    player_id: UUID
    session_id: UUID
    action_type: str  # "spell", "basic_attack", "consumable"
    spell_id: Optional[UUID] = None


class ExecuteActionUseCase:
    """
    Use case for executing a combat action.
    Handles spell casting, basic attacks, and consumable usage.
    Also triggers monster turn after player acts.
    """
    
    def __init__(
        self,
        player_repository: IPlayerRepository,
        monster_repository: IMonsterRepository,
        combat_repository: ICombatRepository,
        item_repository: IItemRepository,
    ):
        self.player_repo = player_repository
        self.monster_repo = monster_repository
        self.combat_repo = combat_repository
        self.item_repo = item_repository
    
    async def execute(self, input_data: ExecuteActionInput) -> Tuple[Optional[CombatActionResultDTO], Optional[str]]:
        """
        Execute a combat action.
        
        Returns:
            Tuple of (result, error_message)
        """
        # Get combat session
        session = await self.combat_repo.get_session_by_id(input_data.session_id)
        if not session:
            return None, "Combat session not found"
        
        # Verify ownership
        if session.player_id != input_data.player_id:
            return None, "This is not your combat session"
        
        # Check session is active and it's player's turn
        if session.status != CombatStatus.PLAYER_TURN:
            return None, "It's not your turn or combat has ended"
        
        # Build battle instance
        battle = await self._build_battle(session)
        
        # Execute based on action type
        success = False
        message = ""
        
        if input_data.action_type == "basic_attack":
            success, message = battle.player_basic_attack()
        
        elif input_data.action_type == "spell":
            if not input_data.spell_id:
                return None, "Spell ID required for spell action"
            
            # Find the spell
            spell = self._find_spell(battle.player.available_spells, input_data.spell_id)
            if not spell:
                return None, "Spell not found or not available"
            
            success, message = battle.player_cast_spell(spell)
        
        elif input_data.action_type == "consumable":
            # Get consumable effects from equipped consumable
            consumable_effects = await self._get_consumable_effects(input_data.player_id)
            if not consumable_effects:
                return None, "No consumable equipped"
            
            success, message = battle.player_use_consumable(consumable_effects)
        
        else:
            return None, f"Unknown action type: {input_data.action_type}"
        
        if not success:
            return CombatActionResultDTO(
                success=False,
                message=message,
                combat_state=self._session_to_state(session, battle),
            ), None
        
        # Check if combat ended after player action
        result = battle.check_victory_conditions()
        if result:
            battle.sync_to_session()
            await self.combat_repo.update_session(session)
            
            rewards = None
            if result == "victory":
                rewards = await self._process_rewards(session, battle)
            
            return CombatActionResultDTO(
                success=True,
                message=message,
                combat_state=self._session_to_state(session, battle),
                combat_ended=True,
                result=result,
            ), None
        
        # End player turn and process monster turn
        battle.player_end_turn()
        
        # Check after turn end effects
        result = battle.check_victory_conditions()
        if not result and battle.session.status == CombatStatus.MONSTER_TURN:
            # Monster takes turn
            battle.monster_take_turn()
            result = battle.check_victory_conditions()
        
        # Sync state back to session
        battle.sync_to_session()
        await self.combat_repo.update_session(session)
        
        # Build response
        rewards = None
        if result == "victory":
            rewards = await self._process_rewards(session, battle)
        
        return CombatActionResultDTO(
            success=True,
            message=message,
            combat_state=self._session_to_state(session, battle),
            combat_ended=result is not None,
            result=result,
        ), None
    
    async def _build_battle(self, session) -> Battle:
        """Build a Battle instance from session data."""
        # Get player
        player = await self.player_repo.get_by_id(session.player_id)
        
        # Get monster blueprint
        monster_bp = await self.monster_repo.get_blueprint_by_id(session.monster_blueprint_id)
        
        # Calculate stats
        player_stats = await self._get_player_stats(session.player_id, player.level)
        monster_stats = self._get_monster_stats(monster_bp, session.monster_level)
        
        # Get available spells
        spells = await self._get_player_spells(session.player_id)
        
        # Build player entity
        player_entity = PlayerCombatEntity(
            id=session.player_id,
            name=player.user.username if hasattr(player, 'user') else "Player",
            stats=player_stats,
            current_hp=session.player_current_hp,
            max_hp=session.player_max_hp,
            echo_current=session.player_echo_current,
            echo_max=session.player_echo_max,
            statuses=dict(session.player_statuses) if session.player_statuses else {},
            gauges=dict(session.player_gauges) if session.player_gauges else {},
            available_spells=spells,
        )
        
        # Build monster entity
        monster_entity = MonsterCombatEntity(
            id=session.monster_blueprint_id,
            name=monster_bp.name,
            stats=monster_stats,
            current_hp=session.monster_current_hp,
            max_hp=session.monster_max_hp,
            statuses=dict(session.monster_statuses) if session.monster_statuses else {},
            blueprint_id=session.monster_blueprint_id,
            ai_behavior=monster_bp.ai_behavior,
            abilities=list(monster_bp.abilities) if hasattr(monster_bp, 'abilities') else [],
            xp_reward=monster_bp.xp_reward,
            gold_reward_min=monster_bp.gold_reward_min,
            gold_reward_max=monster_bp.gold_reward_max,
        )
        
        # Get status definitions
        status_defs = await self.combat_repo.get_all_status_definitions()
        
        # Create battle
        battle = Battle(
            session=session,
            player=player_entity,
            monster=monster_entity,
        )
        battle.register_status_definitions(status_defs)
        
        # Restore cooldowns
        for spell_cd in session.spell_cooldowns if hasattr(session, 'spell_cooldowns') else []:
            player_entity.cooldowns[spell_cd.spell_id] = spell_cd.remaining_turns
        
        return battle
    
    async def _get_player_stats(self, player_id: UUID, level: int) -> StatsBlock:
        """Get calculated player stats."""
        base = StatsBlock(
            max_hp=100 + (level * 10),
            ad=10 + (level * 2),
            ap=10 + (level * 2),
            armor=5 + level,
            mr=5 + level,
            speed=10,
            crit_chance=0.05,
            crit_damage=1.5,
        )
        
        inventory = await self.item_repo.get_player_inventory(player_id)
        for item in inventory:
            if item.is_equipped and hasattr(item, 'blueprint'):
                bp = item.blueprint
                item_level = item.item_level
                
                equip_stats = StatsBlock(
                    max_hp=int((getattr(bp, 'base_max_hp', 0) or 0) + 
                              (getattr(bp, 'scaling_hp_per_level', 0) or 0) * item_level),
                    ad=int((getattr(bp, 'base_ad', 0) or 0) + 
                          (getattr(bp, 'scaling_ad_per_level', 0) or 0) * item_level),
                    ap=int((getattr(bp, 'base_ap', 0) or 0) + 
                          (getattr(bp, 'scaling_ap_per_level', 0) or 0) * item_level),
                    armor=int((getattr(bp, 'base_armor', 0) or 0) + 
                             (getattr(bp, 'scaling_armor_per_level', 0) or 0) * item_level),
                    mr=int((getattr(bp, 'base_mr', 0) or 0) + 
                          (getattr(bp, 'scaling_mr_per_level', 0) or 0) * item_level),
                    speed=getattr(bp, 'base_speed', 0) or 0,
                    crit_chance=getattr(bp, 'base_crit_chance', 0) or 0,
                )
                base = base + equip_stats
        
        return base
    
    def _get_monster_stats(self, monster_bp, level: int) -> StatsBlock:
        """Get calculated monster stats."""
        return StatsBlock(
            max_hp=int((monster_bp.base_max_hp or 0) + 
                      (monster_bp.scaling_hp_per_level or 0) * level),
            ad=int((monster_bp.base_ad or 0) + 
                  (monster_bp.scaling_ad_per_level or 0) * level),
            ap=int((monster_bp.base_ap or 0) + 
                  (monster_bp.scaling_ap_per_level or 0) * level),
            armor=int((monster_bp.base_armor or 0) + 
                     (monster_bp.scaling_armor_per_level or 0) * level),
            mr=int((monster_bp.base_mr or 0) + 
                  (monster_bp.scaling_mr_per_level or 0) * level),
            speed=monster_bp.base_speed or 0,
        )
    
    async def _get_player_spells(self, player_id: UUID) -> List[Spell]:
        """Get available spells from equipped weapons."""
        spells = []
        inventory = await self.item_repo.get_player_inventory(player_id)
        
        for item in inventory:
            if item.is_equipped and hasattr(item, 'blueprint'):
                bp = item.blueprint
                if hasattr(bp, 'spells'):
                    for spell_model in bp.spells:
                        spell = Spell(
                            id=spell_model.id,
                            weapon_blueprint_id=spell_model.weapon_blueprint_id,
                            name=spell_model.name,
                            description=spell_model.description,
                            spell_type=spell_model.spell_type,
                            spell_order=spell_model.spell_order,
                            cooldown_turns=spell_model.cooldown_turns,
                            echo_cost=spell_model.echo_cost,
                            effects=spell_model.effects or [],
                        )
                        spells.append(spell)
        
        return spells
    
    async def _get_consumable_effects(self, player_id: UUID) -> Optional[List[Dict[str, Any]]]:
        """Get effects from equipped consumable."""
        inventory = await self.item_repo.get_player_inventory(player_id)
        
        for item in inventory:
            if item.is_equipped and hasattr(item, 'blueprint'):
                bp = item.blueprint
                if hasattr(bp, 'consumable') and bp.consumable:
                    return bp.consumable.effects
        
        return None
    
    def _find_spell(self, spells: List[Spell], spell_id: UUID) -> Optional[Spell]:
        """Find a spell by ID."""
        for spell in spells:
            if spell.id == spell_id:
                return spell
        return None
    
    def _session_to_state(self, session, battle: Battle) -> CombatStateDTO:
        """Convert session to DTO."""
        return CombatStateDTO(
            session_id=session.id,
            status=session.status,
            turn_count=session.turn_count,
            current_turn=session.current_turn_entity,
            player=PlayerStateDTO(
                name=battle.player.name,
                current_hp=battle.player.current_hp,
                max_hp=battle.player.max_hp,
                echo_current=battle.player.echo_current,
                echo_max=battle.player.echo_max,
                statuses={k: v.stacks for k, v in battle.player.statuses.items()},
                shield=battle.player.gauges.get("shield", 0),
                spell_cooldowns=dict(battle.player.cooldowns),
                consumable_uses=battle.player.consumable_uses_remaining,
            ),
            monster=EntityStateDTO(
                name=battle.monster.name,
                current_hp=battle.monster.current_hp,
                max_hp=battle.monster.max_hp,
                statuses={k: v.stacks for k, v in battle.monster.statuses.items()},
            ),
            logs=[log.message for log in battle.logs[-10:]],
        )
    
    async def _process_rewards(self, session, battle: Battle) -> CombatRewardDTO:
        """Process rewards for victory."""
        rewards = battle.calculate_rewards()
        
        # Apply XP and gold
        level, levels_gained = await self.player_repo.add_xp(session.player_id, rewards.xp_gained)
        await self.player_repo.add_gold(session.player_id, rewards.gold_gained)
        
        return CombatRewardDTO(
            xp_gained=rewards.xp_gained,
            gold_gained=rewards.gold_gained,
            levels_gained=levels_gained,
        )
