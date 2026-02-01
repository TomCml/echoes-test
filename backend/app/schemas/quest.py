from pydantic import BaseModel
from typing import Optional
from enum import Enum

class QuestType(str, Enum):
    Unique = "Unique"
    Repeatable = "Repeatable"

class QuestCategory(str, Enum):
    MainStory = "Main Story"
    SideQuest = "Side Quest"
    Event = "Event"
    Daily = "Daily"
    Weekly = "Weekly"
    Monthly = "Monthly"

class QuestCreate(BaseModel):
    name: str
    description: Optional[str] = None
    quest_type: QuestType
    category: QuestCategory
    reward_xp: Optional[int] = None
    reward_gold: int = 10
    reward_chest: Optional[bool] = False

class QuestRead(BaseModel):
    quest_id: int
    name: str
    description: Optional[str] = None
    quest_type: QuestType
    category: QuestCategory
    reward_xp: Optional[int] = None
    reward_gold: int
    reward_chest: bool

    class Config:
        from_attributes = True

class QuestUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    quest_type: Optional[QuestType] = None
    category: Optional[QuestCategory] = None
    reward_xp: Optional[int] = None
    reward_gold: Optional[int] = None
    reward_chest: Optional[bool] = None

    class Config:
        from_attributes = True
