from sqlalchemy import Column, Integer, String, ForeignKey
from app.core.database import Base

class Inventory(Base):
    __tablename__ = "inventories"

    inventory_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("players.player_id"), nullable=False)
    # item_id fait référence aux fichiers JSON, pas à une table DB
    item_id = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
