from sqlalchemy import Column, Integer, String, ForeignKey
from app.core.database import Base


class PlayerEquipmentLoadout(Base):
    __tablename__ = "player_equipment_loadout"

    loadout_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    player_id = Column(Integer, ForeignKey("players.player_id"), unique=True, nullable=False)

    # 7 slots — chaque slot référence un item_id JSON (comme l'inventaire)
    weapon_primary_id = Column(String(100), nullable=True)
    weapon_secondary_id = Column(String(100), nullable=True)
    head_id = Column(String(100), nullable=True)
    armor_id = Column(String(100), nullable=True)
    artifact_id = Column(String(100), nullable=True)
    blessing_id = Column(String(100), nullable=True)
    consumable_id = Column(String(100), nullable=True)
