"""Lifesteal opcodes - Vol de vie.

IMPORTANT: Tous les paramètres doivent être fournis par les items JSON.
"""
from typing import Dict, Any
from app.engine.combat import register
from app.engine.domain import Battle, Entity


def _require_param(b: Battle, opcode: str, p: Dict, key: str) -> bool:
    if key not in p:
        b.log.append(f"[WARN] {opcode}: '{key}' param missing")
        return False
    return True


def _apply_antiheal_reduction(entity: Entity, amount: float) -> float:
    antiheal = entity.statuses.get("antiheal")
    if antiheal:
        stacks = antiheal.get("stacks", 1)
        reduction = min(0.8, stacks * 0.4)
        return amount * (1 - reduction)
    return amount


@register("lifesteal")
def eff_lifesteal(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Vol de vie sur dégâts physiques. Params: damage_dealt (REQUIS), lifesteal_percent (REQUIS)"""
    if not _require_param(b, "lifesteal", p, "damage_dealt"): return
    if not _require_param(b, "lifesteal", p, "lifesteal_percent"): return
    
    damage_dealt = float(p["damage_dealt"])
    lifesteal_percent = float(p["lifesteal_percent"])
    
    heal = damage_dealt * lifesteal_percent
    heal = _apply_antiheal_reduction(src, heal)
    
    old_hp = src.stats.HP
    src.stats.HP = min(src.stats.MAX_HP, src.stats.HP + int(heal))
    actual_heal = src.stats.HP - old_hp
    
    b.log.append(f"{src.name} lifesteals {actual_heal} ({int(lifesteal_percent*100)}% of {int(damage_dealt)}).")


@register("omnivamp")
def eff_omnivamp(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Vol de vie sur tous dégâts. Params: damage_dealt (REQUIS), omnivamp_percent (REQUIS), is_aoe (REQUIS)"""
    if not _require_param(b, "omnivamp", p, "damage_dealt"): return
    if not _require_param(b, "omnivamp", p, "omnivamp_percent"): return
    if not _require_param(b, "omnivamp", p, "is_aoe"): return
    
    damage_dealt = float(p["damage_dealt"])
    omnivamp_percent = float(p["omnivamp_percent"])
    is_aoe = bool(p["is_aoe"])
    
    effective_percent = omnivamp_percent * (0.33 if is_aoe else 1.0)
    heal = damage_dealt * effective_percent
    heal = _apply_antiheal_reduction(src, heal)
    
    old_hp = src.stats.HP
    src.stats.HP = min(src.stats.MAX_HP, src.stats.HP + int(heal))
    actual_heal = src.stats.HP - old_hp
    
    b.log.append(f"{src.name} omnivamps {actual_heal}.")


@register("spellvamp")
def eff_spellvamp(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Vol de vie sur dégâts de sorts. Params: damage_dealt (REQUIS), spellvamp_percent (REQUIS)"""
    if not _require_param(b, "spellvamp", p, "damage_dealt"): return
    if not _require_param(b, "spellvamp", p, "spellvamp_percent"): return
    
    damage_dealt = float(p["damage_dealt"])
    spellvamp_percent = float(p["spellvamp_percent"])
    
    heal = damage_dealt * spellvamp_percent
    heal = _apply_antiheal_reduction(src, heal)
    
    old_hp = src.stats.HP
    src.stats.HP = min(src.stats.MAX_HP, src.stats.HP + int(heal))
    actual_heal = src.stats.HP - old_hp
    
    b.log.append(f"{src.name} spellvamps {actual_heal}.")
