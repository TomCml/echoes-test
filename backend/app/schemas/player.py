from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LoginRequest(BaseModel):
    twitch_id: int

class PlayerCreate(BaseModel):
    twitch_id: int
    username: str

class PlayerRead(BaseModel):
    player_id: int
    twitch_id: int
    username: str
    level: int
    gold: int
    echo_current: int
    echo_max: int
    experience: int
    health_points: int
    attack_damage: int
    ability_power: int
    armor: int
    magic_resistance: int
    attack_speed: int
    ability_haste: int
    crit_chance: int
    dodge: int
    speed: int
    life_steal: int
    spell_vamp: int
    is_watching: bool
    start_watch: Optional[datetime] = None
    title_id: Optional[int] = None
    player_shop_id: Optional[int] = None
    shop_level: int
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class PlayerUpdate(BaseModel):
    username: Optional[str] = None
    level: Optional[int] = None
    gold: Optional[int] = None
    echo_current: Optional[int] = None
    echo_max: Optional[int] = None
    experience: Optional[int] = None
    health_points: Optional[int] = None
    attack_damage: Optional[int] = None
    ability_power: Optional[int] = None
    armor: Optional[int] = None
    magic_resistance: Optional[int] = None
    attack_speed: Optional[int] = None
    ability_haste: Optional[int] = None
    crit_chance: Optional[int] = None
    dodge: Optional[int] = None
    speed: Optional[int] = None
    life_steal: Optional[int] = None
    spell_vamp: Optional[int] = None
    is_watching: Optional[bool] = None
    start_watch: Optional[datetime] = None
    title_id: Optional[int] = None
    player_shop_id: Optional[int] = None
    shop_level: Optional[int] = None

    class Config:
        from_attributes = True
