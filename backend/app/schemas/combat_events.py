"""
Combat Events — Schémas Pydantic pour l'event sourcing du moteur de combat.

14 types d'événements + discriminated union AnyCombatEvent.
Consommés par le frontend Phaser pour animer les combats.

Chaque event porte :
  - type       : discriminateur Literal (ex: "DAMAGE")
  - turn       : numéro du tour (injecté par Battle.emit())
  - sequence   : ordre d'émission dans le tour (injecté par Battle.emit())
  - timestamp  : horodatage de création (auto)
"""
from datetime import datetime, timezone
from typing import Annotated, List, Literal, Union
from pydantic import BaseModel, Field


# ─── Base ─────────────────────────────────────────────────────────────────────

class _BaseEvent(BaseModel):
    """Champs communs à tous les événements."""
    turn: int = 0
    sequence: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"extra": "forbid"}


# ─── Player Actions ───────────────────────────────────────────────────────────

class SpellCastEvent(_BaseEvent):
    type: Literal["SPELL_CAST"] = "SPELL_CAST"
    source: str
    spell_code: str
    spell_name: str
    target: str


class ItemConsumedEvent(_BaseEvent):
    type: Literal["ITEM_CONSUMED"] = "ITEM_CONSUMED"
    source: str
    item_id: str
    item_name: str


# ─── Monster Actions ──────────────────────────────────────────────────────────

class MonsterActionEvent(_BaseEvent):
    type: Literal["MONSTER_ACTION"] = "MONSTER_ACTION"
    source: str
    action_name: str
    target: str


# ─── Damage & Heal ────────────────────────────────────────────────────────────

class DamageEvent(_BaseEvent):
    type: Literal["DAMAGE"] = "DAMAGE"
    source: str
    target: str
    amount: int
    damage_type: str          # "physical" | "magic" | "true" | "mixed"
    is_crit: bool = False
    label: str = "damage"
    target_hp_after: int
    target_max_hp: int


class HealEvent(_BaseEvent):
    type: Literal["HEAL"] = "HEAL"
    source: str
    target: str
    amount: int
    target_hp_after: int
    target_max_hp: int


# ─── Status ───────────────────────────────────────────────────────────────────

class StatusAppliedEvent(_BaseEvent):
    type: Literal["STATUS_APPLIED"] = "STATUS_APPLIED"
    source: str
    target: str
    status_code: str
    duration: int
    stacks: int = 1


class StatusResistEvent(_BaseEvent):
    type: Literal["STATUS_RESIST"] = "STATUS_RESIST"
    source: str
    target: str
    status_code: str


class StatusTickEvent(_BaseEvent):
    type: Literal["STATUS_TICK"] = "STATUS_TICK"
    target: str
    status_code: str
    effect_type: str          # opcode déclenché (ex: "heal", "damage")


class StatusExpiredEvent(_BaseEvent):
    type: Literal["STATUS_EXPIRED"] = "STATUS_EXPIRED"
    target: str
    status_code: str


# ─── Gauge ────────────────────────────────────────────────────────────────────

class GaugeChangeEvent(_BaseEvent):
    type: Literal["GAUGE_CHANGE"] = "GAUGE_CHANGE"
    source: str
    gauge_name: str
    old_value: int
    new_value: int
    max_value: int


# ─── Entity ───────────────────────────────────────────────────────────────────

class EntityDeathEvent(_BaseEvent):
    type: Literal["ENTITY_DEATH"] = "ENTITY_DEATH"
    target: str
    killer: str


# ─── Battle End ───────────────────────────────────────────────────────────────

class BattleEndEvent(_BaseEvent):
    type: Literal["BATTLE_END"] = "BATTLE_END"
    winner: str
    result: str               # "VICTORY" | "DEFEAT"


class BattleEndLootEvent(_BaseEvent):
    type: Literal["BATTLE_END_LOOT"] = "BATTLE_END_LOOT"
    xp_gained: int = 0
    gold_gained: int = 0
    items_dropped: List[str] = Field(default_factory=list)


# ─── Discriminated Union ──────────────────────────────────────────────────────

AnyCombatEvent = Annotated[
    Union[
        SpellCastEvent,
        ItemConsumedEvent,
        MonsterActionEvent,
        DamageEvent,
        HealEvent,
        StatusAppliedEvent,
        StatusResistEvent,
        StatusTickEvent,
        StatusExpiredEvent,
        GaugeChangeEvent,
        EntityDeathEvent,
        BattleEndEvent,
        BattleEndLootEvent,
    ],
    Field(discriminator="type"),
]
