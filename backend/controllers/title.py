import logging
from sqlalchemy.orm import Session
from typing import List, Optional
from models.title import Title
from schemas.title import TitleCreate, TitleUpdate

logger = logging.getLogger(__name__)

def get_title(db: Session, title_id: int) -> Optional[Title]:
    return db.query(Title).filter(Title.title_id == title_id).first()

def get_titles(db: Session, skip: int = 0, limit: int = 100) -> List[Title]:
    return db.query(Title).offset(skip).limit(limit).all()

def create_title(db: Session, payload: TitleCreate) -> Title:
    db_title = Title(title_name=payload.title_name)
    db.add(db_title)
    db.commit()
    db.refresh(db_title)
    logger.debug(f"Title created: {db_title.title_id}")
    return db_title

def update_title(db: Session, title_id: int, payload: TitleUpdate) -> Optional[Title]:
    db_title = db.query(Title).filter(Title.title_id == title_id).first()
    if not db_title:
        return None
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if hasattr(db_title, key):
            setattr(db_title, key, value)
    db.add(db_title)
    db.commit()
    db.refresh(db_title)
    return db_title

def delete_title(db: Session, title_id: int) -> bool:
    db_title = db.query(Title).filter(Title.title_id == title_id).first()
    if not db_title:
        return False
    db.delete(db_title)
    db.commit()
    return True