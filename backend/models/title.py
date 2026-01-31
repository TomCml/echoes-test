from sqlalchemy import Column, Integer, String
from core.database import Base

class Title(Base):
    __tablename__ = "titles"

    title_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title_name = Column(String(100), nullable=False)