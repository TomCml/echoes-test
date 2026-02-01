from sqlalchemy import Column, Integer, ForeignKey, String, Text, Boolean, Enum
from app.core.database import Base
from app.schemas.quest import QuestType, QuestCategory

class Quest(Base):
    __tablename__ = "quests"

    quest_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    quest_type = Column(Enum(QuestType, name='quest_type_enum'), nullable=False)
    category = Column(Enum(QuestCategory, name='quest_category_enum'), nullable=False)
    reward_xp = Column(Integer, nullable=True)
    reward_gold = Column(Integer, nullable=False, default=10)
    reward_chest = Column(Boolean, nullable=False, default=False)