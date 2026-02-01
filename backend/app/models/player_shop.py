from sqlalchemy import Column, Integer
from app.core.database import Base


class PlayerShop(Base):
    __tablename__ = "player_shop"

    player_shop_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
