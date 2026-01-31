import logging
from sqlalchemy.orm import Session
from typing import List, Optional
from models.quest import Quest
from schemas.quest import QuestCreate, QuestUpdate

logger = logging.getLogger(__name__)

def get_quest(db: Session, quest_id: int) -> Optional[Quest]:
    return db.query(Quest).filter(Quest.quest_id == quest_id).first()

def get_quests(db: Session, skip: int = 0, limit: int = 100) -> List[Quest]:
    return db.query(Quest).offset(skip).limit(limit).all()

def create_quest(db: Session, payload: QuestCreate) -> Quest:
    new_quest = Quest(
        name=payload.name,
        description=payload.description,
        quest_type=payload.quest_type,
        category=payload.category,
        reward_xp=payload.reward_xp,
        reward_gold=payload.reward_gold,
        reward_chest=payload.reward_chest or False
    )
    db.add(new_quest)
    db.commit()
    db.refresh(new_quest)
    logger.debug(f"Quest created: {new_quest.quest_id}")
    return new_quest

def update_quest(db: Session, quest_id: int, payload: QuestUpdate) -> Optional[Quest]:
    quest = db.query(Quest).filter(Quest.quest_id == quest_id).first()
    if not quest:
        return None
    updates = payload.model_dump(exclude_unset=True)
    updates.pop("quest_id", None)
    for k, v in updates.items():
        if hasattr(quest, k):
            setattr(quest, k, v)
    db.add(quest)
    db.commit()
    db.refresh(quest)
    return quest

def delete_quest(db: Session, quest_id: int) -> bool:
    quest = db.query(Quest).filter(Quest.quest_id == quest_id).first()
    if not quest:
        return False
    db.delete(quest)
    db.commit()
    return True