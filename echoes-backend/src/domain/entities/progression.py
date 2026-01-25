"""
Echoes Backend - Progression Domain Entities
Achievements, quests, dungeons.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from src.domain.enums.types import AchievementCategory, QuestType


@dataclass
class Achievement:
    """
    Achievement definition.
    """
    id: UUID
    name: str
    description: str
    category: AchievementCategory
    condition_type: str  # e.g., "monsters_killed", "level_reached"
    condition_value: int
    condition_target_id: Optional[UUID] = None  # e.g., specific monster blueprint
    reward_xp: int = 0
    reward_gold: int = 0
    reward_item_blueprint_id: Optional[UUID] = None
    icon_key: str = ""
    is_hidden: bool = False


@dataclass
class PlayerAchievement:
    """
    Player's progress on an achievement.
    """
    id: UUID
    player_id: UUID
    achievement_id: UUID
    progress: int = 0
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    
    def add_progress(self, amount: int, target: int) -> bool:
        """
        Add progress. Returns True if just completed.
        """
        if self.is_completed:
            return False
        
        self.progress += amount
        if self.progress >= target:
            self.is_completed = True
            self.completed_at = datetime.utcnow()
            return True
        return False


@dataclass
class Quest:
    """
    Quest definition.
    """
    id: UUID
    name: str
    description: str
    quest_type: QuestType
    objective_type: str  # e.g., "kill_monster", "win_combat"
    objective_target: int  # Number to achieve
    objective_target_id: Optional[UUID] = None  # e.g., specific monster
    reward_xp: int = 0
    reward_gold: int = 0
    reward_item_blueprint_id: Optional[UUID] = None
    is_repeatable: bool = False
    reset_period_hours: Optional[int] = None  # For daily/weekly quests


@dataclass
class PlayerQuest:
    """
    Player's active quest instance.
    """
    id: UUID
    player_id: UUID
    quest_id: UUID
    progress: int = 0
    is_completed: bool = False
    assigned_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    def add_progress(self, amount: int, target: int) -> bool:
        """
        Add progress. Returns True if just completed.
        """
        if self.is_completed:
            return False
        
        self.progress += amount
        if self.progress >= target:
            self.is_completed = True
            self.completed_at = datetime.utcnow()
            return True
        return False
    
    @property
    def is_expired(self) -> bool:
        """Check if the quest has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


@dataclass
class Dungeon:
    """
    Dungeon definition.
    """
    id: UUID
    name: str
    description: str
    level_requirement: int = 1
    recommended_level: int = 1
    boss_blueprint_id: Optional[UUID] = None
    background_key: str = ""


@dataclass
class DungeonMonsterSequence:
    """
    Monster sequence in a dungeon.
    """
    id: UUID
    dungeon_id: UUID
    monster_blueprint_id: UUID
    sequence_order: int
    monster_level_override: Optional[int] = None


@dataclass
class PlayerDungeonProgress:
    """
    Player's progress in a dungeon.
    """
    id: UUID
    player_id: UUID
    dungeon_id: UUID
    is_unlocked: bool = False
    best_clear_time_ms: Optional[int] = None
    clear_count: int = 0
    last_cleared_at: Optional[datetime] = None
    
    def record_clear(self, clear_time_ms: int) -> bool:
        """
        Record a dungeon clear.
        Returns True if this is a new best time.
        """
        self.clear_count += 1
        self.last_cleared_at = datetime.utcnow()
        
        is_new_best = False
        if self.best_clear_time_ms is None or clear_time_ms < self.best_clear_time_ms:
            self.best_clear_time_ms = clear_time_ms
            is_new_best = True
        
        return is_new_best


@dataclass
class LeaderboardEntry:
    """
    Entry in a leaderboard.
    """
    id: UUID
    player_id: UUID
    leaderboard_type: str  # LeaderboardType enum value
    score: int
    rank: int = 0
    metadata: dict = field(default_factory=dict)
    updated_at: datetime = field(default_factory=datetime.utcnow)
