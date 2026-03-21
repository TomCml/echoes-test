from sqlalchemy import Column, Integer, String, ForeignKey
from app.core.database import Base

class Inventory(Base):
    __tablename__ = "inventories"

    inventory_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("players.player_id"), nullable=False)
    # item_id fait référence aux fichiers JSON, pas à une table DB
    item_id = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    
    # Emplacement où l'objet est équipé (ex: "weapon_1", null si non-équipé)
    equipped_slot = Column(String(50), nullable=True)
    # Niveau de l'item (gacha : fusion de doublons pour level up)
    item_level = Column(Integer, nullable=False, default=1)
    # XP accumulée (réservé pour usage futur)
    item_xp = Column(Integer, nullable=False, default=0)
