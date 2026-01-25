"""
Echoes Backend - Progression SQLAlchemy Models
Achievements, quests, dungeons, leaderboards.
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.connection import Base
from src.domain.enums.types import AchievementCategory, LeaderboardType, QuestType


class AchievementModel(Base):
    """Achievement definition."""
    
    __tablename__ = "achievements"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="")
    category: Mapped[AchievementCategory] = mapped_column(
        Enum(AchievementCategory, name="achievement_category", create_constraint=True),
        nullable=False,
    )
    condition_type: Mapped[str] = mapped_column(String(50), nullable=False)
    condition_value: Mapped[int] = mapped_column(Integer, nullable=False)
    condition_target_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    reward_xp: Mapped[int] = mapped_column(Integer, default=0)
    reward_gold: Mapped[int] = mapped_column(Integer, default=0)
    reward_item_blueprint_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("item_blueprints.id", ondelete="SET NULL"),
        nullable=True,
    )
    icon_key: Mapped[str] = mapped_column(String(100), default="")
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)


class PlayerAchievementModel(Base):
    """Player's progress on achievements."""
    
    __tablename__ = "player_achievements"
    __table_args__ = (
        UniqueConstraint("player_id", "achievement_id", name="uq_player_achievement"),
    )
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    player_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    achievement_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("achievements.id", ondelete="CASCADE"),
        nullable=False,
    )
    progress: Mapped[int] = mapped_column(Integer, default=0)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class QuestModel(Base):
    """Quest definition."""
    
    __tablename__ = "quests"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="")
    quest_type: Mapped[QuestType] = mapped_column(
        Enum(QuestType, name="quest_type", create_constraint=True),
        nullable=False,
    )
    objective_type: Mapped[str] = mapped_column(String(50), nullable=False)
    objective_target: Mapped[int] = mapped_column(Integer, nullable=False)
    objective_target_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    reward_xp: Mapped[int] = mapped_column(Integer, default=0)
    reward_gold: Mapped[int] = mapped_column(Integer, default=0)
    reward_item_blueprint_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("item_blueprints.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_repeatable: Mapped[bool] = mapped_column(Boolean, default=False)
    reset_period_hours: Mapped[int] = mapped_column(Integer, nullable=True)


class PlayerQuestModel(Base):
    """Player's active quest instance."""
    
    __tablename__ = "player_quests"
    __table_args__ = (
        UniqueConstraint("player_id", "quest_id", name="uq_player_quest"),
    )
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    player_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quest_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quests.id", ondelete="CASCADE"),
        nullable=False,
    )
    progress: Mapped[int] = mapped_column(Integer, default=0)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class DungeonModel(Base):
    """Dungeon definition."""
    
    __tablename__ = "dungeons"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="")
    level_requirement: Mapped[int] = mapped_column(Integer, default=1)
    recommended_level: Mapped[int] = mapped_column(Integer, default=1)
    boss_blueprint_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("monster_blueprints.id", ondelete="SET NULL"),
        nullable=True,
    )
    background_key: Mapped[str] = mapped_column(String(100), default="")
    
    # Relationships
    monster_sequence: Mapped[list["DungeonMonsterSequenceModel"]] = relationship(
        "DungeonMonsterSequenceModel",
        back_populates="dungeon",
    )


class DungeonMonsterSequenceModel(Base):
    """Monster encounter sequence in a dungeon."""
    
    __tablename__ = "dungeon_monster_sequence"
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    dungeon_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dungeons.id", ondelete="CASCADE"),
        nullable=False,
    )
    monster_blueprint_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("monster_blueprints.id", ondelete="CASCADE"),
        nullable=False,
    )
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)
    monster_level_override: Mapped[int] = mapped_column(Integer, nullable=True)
    
    # Relationships
    dungeon: Mapped["DungeonModel"] = relationship(
        "DungeonModel",
        back_populates="monster_sequence",
    )


class PlayerDungeonProgressModel(Base):
    """Player's progress in dungeons."""
    
    __tablename__ = "player_dungeon_progress"
    __table_args__ = (
        UniqueConstraint("player_id", "dungeon_id", name="uq_player_dungeon"),
    )
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    player_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dungeon_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dungeons.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_unlocked: Mapped[bool] = mapped_column(Boolean, default=False)
    best_clear_time_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    clear_count: Mapped[int] = mapped_column(Integer, default=0)
    last_cleared_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class LeaderboardEntryModel(Base):
    """Leaderboard entry."""
    
    __tablename__ = "leaderboard_entries"
    __table_args__ = (
        UniqueConstraint("player_id", "leaderboard_type", name="uq_player_leaderboard"),
    )
    
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    player_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    leaderboard_type: Mapped[LeaderboardType] = mapped_column(
        Enum(LeaderboardType, name="leaderboard_type", create_constraint=True),
        nullable=False,
    )
    score: Mapped[int] = mapped_column(Integer, default=0)
    rank: Mapped[int] = mapped_column(Integer, default=0)
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
