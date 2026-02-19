"""Percent stat modifiers - Modifications de stats en pourcentage.

IMPORTANT: Tous les pourcentages doivent être fournis par les items JSON.
"""
from typing import Dict, Any
from app.engine.combat import register
from app.engine.domain import Battle, Entity


def _require_param(b: Battle, opcode: str, p: Dict, key: str) -> bool:
    if key not in p:
        b.log.append(f"[WARN] {opcode}: '{key}' param missing")
        return False
    return True


@register("modify_stat_percent")
def eff_modify_stat_percent(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Modifie une stat en %. Params: stat (REQUIS), percent (REQUIS)"""
    if not _require_param(b, "modify_stat_percent", p, "stat"): return
    if not _require_param(b, "modify_stat_percent", p, "percent"): return
    
    stat_name = p["stat"]
    percent = float(p["percent"])
    
    current = getattr(tgt.stats, stat_name, None)
    if current is None:
        b.log.append(f"[WARN] unknown stat: {stat_name}")
        return
    
    change = int(current * percent)
    setattr(tgt.stats, stat_name, current + change)
    sign = "+" if percent >= 0 else ""
    b.log.append(f"{tgt.name} {stat_name} {sign}{int(percent*100)}% ({sign}{change}, now {current + change})")


@register("modify_ad_percent")
def eff_modify_ad_percent(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Modifie l'AD en %. Params: percent (REQUIS)"""
    if not _require_param(b, "modify_ad_percent", p, "percent"): return
    
    percent = float(p["percent"])
    change = int(tgt.stats.AD * percent)
    tgt.stats.AD += change
    sign = "+" if percent >= 0 else ""
    b.log.append(f"{tgt.name} AD {sign}{int(percent*100)}% ({sign}{change}, now {tgt.stats.AD})")


@register("modify_ap_percent")
def eff_modify_ap_percent(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Modifie l'AP en %. Params: percent (REQUIS)"""
    if not _require_param(b, "modify_ap_percent", p, "percent"): return
    
    percent = float(p["percent"])
    change = int(tgt.stats.AP * percent)
    tgt.stats.AP += change
    sign = "+" if percent >= 0 else ""
    b.log.append(f"{tgt.name} AP {sign}{int(percent*100)}% ({sign}{change}, now {tgt.stats.AP})")


@register("modify_armor_percent")
def eff_modify_armor_percent(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Modifie l'armor en %. Params: percent (REQUIS)"""
    if not _require_param(b, "modify_armor_percent", p, "percent"): return
    
    percent = float(p["percent"])
    change = int(tgt.stats.ARMOR * percent)
    tgt.stats.ARMOR += change
    sign = "+" if percent >= 0 else ""
    b.log.append(f"{tgt.name} ARMOR {sign}{int(percent*100)}% ({sign}{change}, now {tgt.stats.ARMOR})")


@register("modify_mr_percent")
def eff_modify_mr_percent(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Modifie la MR en %. Params: percent (REQUIS)"""
    if not _require_param(b, "modify_mr_percent", p, "percent"): return
    
    percent = float(p["percent"])
    change = int(tgt.stats.MR * percent)
    tgt.stats.MR += change
    sign = "+" if percent >= 0 else ""
    b.log.append(f"{tgt.name} MR {sign}{int(percent*100)}% ({sign}{change}, now {tgt.stats.MR})")


@register("modify_resistances_percent")
def eff_modify_resistances_percent(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Modifie armor ET MR en % (Mur). Params: percent (REQUIS)"""
    if not _require_param(b, "modify_resistances_percent", p, "percent"): return
    
    percent = float(p["percent"])
    armor_change = int(tgt.stats.ARMOR * percent)
    mr_change = int(tgt.stats.MR * percent)
    
    tgt.stats.ARMOR += armor_change
    tgt.stats.MR += mr_change
    
    sign = "+" if percent >= 0 else ""
    b.log.append(f"{tgt.name} resistances {sign}{int(percent*100)}% (ARMOR {sign}{armor_change}, MR {sign}{mr_change})")


@register("reduce_armor_percent")
def eff_reduce_armor_percent(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Réduit l'armor en % (pénétration). Params: percent (REQUIS)"""
    if not _require_param(b, "reduce_armor_percent", p, "percent"): return
    
    percent = float(p["percent"])
    reduction = int(tgt.stats.ARMOR * percent)
    tgt.stats.ARMOR = max(0, tgt.stats.ARMOR - reduction)
    b.log.append(f"{tgt.name} ARMOR reduced by {int(percent*100)}% (-{reduction}, now {tgt.stats.ARMOR})")


@register("reduce_mr_percent")
def eff_reduce_mr_percent(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Réduit la MR en %. Params: percent (REQUIS)"""
    if not _require_param(b, "reduce_mr_percent", p, "percent"): return
    
    percent = float(p["percent"])
    reduction = int(tgt.stats.MR * percent)
    tgt.stats.MR = max(0, tgt.stats.MR - reduction)
    b.log.append(f"{tgt.name} MR reduced by {int(percent*100)}% (-{reduction}, now {tgt.stats.MR})")
