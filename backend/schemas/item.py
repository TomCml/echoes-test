from pydantic import BaseModel, HttpUrl, Field
from typing import Any, Literal

class Effect(BaseModel):
    opcode: str
    params: dict[str, Any] = Field(default_factory=dict)
    trigger: Literal["on_use", "on_hit", "on_turn_start", "on_turn_end"] | None = None
    order: int | None = None

class Passive(BaseModel):
    name: str
    trigger: Literal["on_hit", "on_use", "on_turn_start", "on_turn_end"]
    effects: list[Effect]

class Spell(BaseModel):
    code: str
    name: str
    cooldown_turns: int = 0
    target: Literal["self", "single_enemy", "all_enemies", "all_allies"] = "single_enemy"
    flags: list[str] = []
    effects: list[Effect]

class Item(BaseModel):
    id: str
    name: str
    category: str | None = None
    tags: list[str] = []
    sprite_url: HttpUrl | str | None = None
    passives: list[Passive] = []
    spells: list[Spell] = []
