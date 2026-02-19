"""Flat stat modifiers - Modifications de stats fixes.

IMPORTANT: Tous les montants doivent être fournis par les items JSON.
"""
from typing import Dict, Any
from app.engine.combat import register
from app.engine.domain import Battle, Entity


def _require_param(b: Battle, opcode: str, p: Dict, key: str) -> bool:
    """Vérifie qu'un paramètre requis est présent."""
    if key not in p:
        b.log.append(f"[WARN] {opcode}: '{key}' param missing")
        return False
    return True


@register("modify_stat")
def eff_modify_stat(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Modifie une stat de manière flat. Params: stat (REQUIS), amount (REQUIS)"""
    if not _require_param(b, "modify_stat", p, "stat"): return
    if not _require_param(b, "modify_stat", p, "amount"): return
    
    stat_name = p["stat"]
    amount = int(p["amount"])
    
    current = getattr(tgt.stats, stat_name, None)
    if current is None:
        b.log.append(f"[WARN] unknown stat: {stat_name}")
        return
    
    setattr(tgt.stats, stat_name, current + amount)
    sign = "+" if amount >= 0 else ""
    b.log.append(f"{tgt.name} {stat_name} {sign}{amount} (now {current + amount})")


@register("modify_ad")
def eff_modify_ad(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Modifie l'AD. Params: amount (REQUIS)"""
    if not _require_param(b, "modify_ad", p, "amount"): return
    
    amount = int(p["amount"])
    tgt.stats.AD += amount
    sign = "+" if amount >= 0 else ""
    b.log.append(f"{tgt.name} AD {sign}{amount} (now {tgt.stats.AD})")


@register("modify_ap")
def eff_modify_ap(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Modifie l'AP. Params: amount (REQUIS)"""
    if not _require_param(b, "modify_ap", p, "amount"): return
    
    amount = int(p["amount"])
    tgt.stats.AP += amount
    sign = "+" if amount >= 0 else ""
    b.log.append(f"{tgt.name} AP {sign}{amount} (now {tgt.stats.AP})")


@register("modify_armor")
def eff_modify_armor(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Modifie l'armor. Params: amount (REQUIS)"""
    if not _require_param(b, "modify_armor", p, "amount"): return
    
    amount = int(p["amount"])
    tgt.stats.ARMOR += amount
    sign = "+" if amount >= 0 else ""
    b.log.append(f"{tgt.name} ARMOR {sign}{amount} (now {tgt.stats.ARMOR})")


@register("modify_mr")
def eff_modify_mr(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Modifie la MR. Params: amount (REQUIS)"""
    if not _require_param(b, "modify_mr", p, "amount"): return
    
    amount = int(p["amount"])
    tgt.stats.MR += amount
    sign = "+" if amount >= 0 else ""
    b.log.append(f"{tgt.name} MR {sign}{amount} (now {tgt.stats.MR})")


@register("modify_speed")
def eff_modify_speed(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Modifie la vitesse. Params: amount (REQUIS)"""
    if not _require_param(b, "modify_speed", p, "amount"): return
    
    amount = int(p["amount"])
    tgt.stats.SPEED += amount
    sign = "+" if amount >= 0 else ""
    b.log.append(f"{tgt.name} SPEED {sign}{amount} (now {tgt.stats.SPEED})")


@register("modify_max_hp")
def eff_modify_max_hp(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Modifie les PV max. Params: amount (REQUIS)"""
    if not _require_param(b, "modify_max_hp", p, "amount"): return
    
    amount = int(p["amount"])
    tgt.stats.MAX_HP += amount
    if amount > 0:
        tgt.stats.HP += amount
    sign = "+" if amount >= 0 else ""
    b.log.append(f"{tgt.name} MAX_HP {sign}{amount} (now {tgt.stats.MAX_HP})")


@register("modify_crit_chance")
def eff_modify_crit_chance(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Modifie la chance de crit. Params: amount (REQUIS) - ex: 0.15 pour +15%"""
    if not _require_param(b, "modify_crit_chance", p, "amount"): return
    
    amount = float(p["amount"])
    tgt.stats.CRIT_CHANCE = min(1.0, max(0.0, tgt.stats.CRIT_CHANCE + amount))
    sign = "+" if amount >= 0 else ""
    b.log.append(f"{tgt.name} CRIT_CHANCE {sign}{int(amount*100)}% (now {int(tgt.stats.CRIT_CHANCE*100)}%)")


@register("modify_crit_damage")
def eff_modify_crit_damage(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Modifie les dégâts critiques. Params: amount (REQUIS) - ex: 0.25 pour +25%"""
    if not _require_param(b, "modify_crit_damage", p, "amount"): return
    
    amount = float(p["amount"])
    tgt.stats.CRIT_DAMAGE += amount
    sign = "+" if amount >= 0 else ""
    b.log.append(f"{tgt.name} CRIT_DAMAGE {sign}{int(amount*100)}% (now {int(tgt.stats.CRIT_DAMAGE*100)}%)")
