"""Indirect damage opcodes - Dégâts indirects (reflect, explosion, drain).

IMPORTANT: Tous les paramètres doivent être fournis par les items JSON.
"""
import math
from typing import Dict, Any
from app.engine.combat import register, apply_damage
from app.engine.domain import Battle, Entity


def _require_param(b: Battle, opcode: str, p: Dict, key: str) -> bool:
    if key not in p:
        b.log.append(f"[WARN] {opcode}: '{key}' param missing")
        return False
    return True


def _mitigation(raw: float, resistance: float) -> float:
    if resistance <= 0:
        return raw
    return raw * math.exp(-resistance / 448.6)


@register("reflect_damage")
def eff_reflect_damage(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Renvoie un % des dégâts reçus (Thornmail).
    
    Params: percent (REQUIS), damage_received (REQUIS)
    """
    if not _require_param(b, "reflect_damage", p, "percent"): return
    if not _require_param(b, "reflect_damage", p, "damage_received"): return
    
    percent = float(p["percent"])
    damage_received = float(p["damage_received"])
    
    reflect = damage_received * percent
    apply_damage(b, tgt, reflect, f"reflected {int(percent*100)}%")


@register("explosion_damage")
def eff_explosion_damage(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Explosion de Sunfire/Égide (scale avec armor et HP bonus).
    
    Params: base (REQUIS), armor_ratio (REQUIS), bonus_hp_ratio (REQUIS), 
            damage_type (REQUIS), base_hp (REQUIS)
    """
    if not _require_param(b, "explosion_damage", p, "base"): return
    if not _require_param(b, "explosion_damage", p, "armor_ratio"): return
    if not _require_param(b, "explosion_damage", p, "bonus_hp_ratio"): return
    if not _require_param(b, "explosion_damage", p, "damage_type"): return
    if not _require_param(b, "explosion_damage", p, "base_hp"): return
    
    base = float(p["base"])
    armor_ratio = float(p["armor_ratio"])
    bonus_hp_ratio = float(p["bonus_hp_ratio"])
    damage_type = p["damage_type"]
    base_hp = int(p["base_hp"])
    
    bonus_hp = max(0, src.stats.MAX_HP - base_hp)
    
    amount = base + src.stats.ARMOR * armor_ratio + bonus_hp * bonus_hp_ratio
    
    if damage_type == "magical":
        amount = _mitigation(amount, tgt.stats.MR)
    else:
        amount = _mitigation(amount, tgt.stats.ARMOR)
    
    apply_damage(b, tgt, amount, "explosion")


@register("drain_damage")
def eff_drain_damage(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Dégâts + soin du même montant (drain de vie).
    
    Params: base (REQUIS), ap_ratio (REQUIS), label (REQUIS)
    """
    if not _require_param(b, "drain_damage", p, "base"): return
    if not _require_param(b, "drain_damage", p, "ap_ratio"): return
    if not _require_param(b, "drain_damage", p, "label"): return
    
    base = float(p["base"])
    ap_ratio = float(p["ap_ratio"])
    label = p["label"]
    
    amount = base + src.stats.AP * ap_ratio
    amount = _mitigation(amount, tgt.stats.MR)
    
    apply_damage(b, tgt, amount, label)
    
    # Heal the source
    heal = amount
    old_hp = src.stats.HP
    src.stats.HP = min(src.stats.MAX_HP, src.stats.HP + int(heal))
    b.log.append(f"{src.name} drains {int(heal)} HP (healed {src.stats.HP - old_hp}).")
