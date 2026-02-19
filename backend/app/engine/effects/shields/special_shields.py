"""Special shields opcodes - Boucliers spéciaux.

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


@register("maw_shield")
def eff_maw_shield(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Bouclier Maw of Malmortius (anti-magie). Params: base (REQUIS), ad_ratio (REQUIS), base_ad (REQUIS)"""
    if not _require_param(b, "maw_shield", p, "base"): return
    if not _require_param(b, "maw_shield", p, "ad_ratio"): return
    if not _require_param(b, "maw_shield", p, "base_ad"): return
    
    base = float(p["base"])
    base_ad = float(p["base_ad"])
    ad_ratio = float(p["ad_ratio"])
    
    bonus_ad = max(0, src.stats.AD - base_ad)
    amount = int(base + bonus_ad * ad_ratio)
    src.gauges["magic_shield"] = src.gauges.get("magic_shield", 0) + amount
    b.log.append(f"{src.name} gains {amount} magic shield (Maw).")


@register("sterak_shield")
def eff_sterak_shield(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Bouclier Sterak's Gage (% HP bonus). Params: percent (REQUIS), base_hp (REQUIS)"""
    if not _require_param(b, "sterak_shield", p, "percent"): return
    if not _require_param(b, "sterak_shield", p, "base_hp"): return
    
    base_hp = int(p["base_hp"])
    percent = float(p["percent"])
    
    bonus_hp = max(0, src.stats.MAX_HP - base_hp)
    amount = int(bonus_hp * percent)
    src.gauges["shield"] = src.gauges.get("shield", 0) + amount
    b.log.append(f"{src.name} gains {amount} shield (Sterak's, {int(percent*100)}% of {bonus_hp} bonus HP).")


@register("gargoyle_shield")
def eff_gargoyle_shield(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Bouclier Gargoyle Stoneplate. Params: base (REQUIS), hp_ratio (REQUIS), base_hp (REQUIS)"""
    if not _require_param(b, "gargoyle_shield", p, "base"): return
    if not _require_param(b, "gargoyle_shield", p, "hp_ratio"): return
    if not _require_param(b, "gargoyle_shield", p, "base_hp"): return
    
    base = float(p["base"])
    base_hp = int(p["base_hp"])
    hp_ratio = float(p["hp_ratio"])
    
    bonus_hp = max(0, src.stats.MAX_HP - base_hp)
    amount = int(base + bonus_hp * hp_ratio)
    src.gauges["shield"] = src.gauges.get("shield", 0) + amount
    b.log.append(f"{src.name} gains {amount} shield (Gargoyle).")


@register("destroy_shield")
def eff_destroy_shield(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Détruit le bouclier d'une cible. Params: aucun"""
    shield = tgt.gauges.get("shield", 0)
    magic_shield = tgt.gauges.get("magic_shield", 0)
    
    tgt.gauges["shield"] = 0
    tgt.gauges["magic_shield"] = 0
    
    total = shield + magic_shield
    if total > 0:
        b.log.append(f"{tgt.name}'s shields destroyed ({total})!")
    else:
        b.log.append(f"{tgt.name} had no shields.")


@register("shield_decay")
def eff_shield_decay(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Diminue les boucliers au fil du temps. Params: decay_percent (REQUIS)"""
    if not _require_param(b, "shield_decay", p, "decay_percent"): return
    
    decay_percent = float(p["decay_percent"])
    
    shield = tgt.gauges.get("shield", 0)
    if shield > 0:
        decay = int(shield * decay_percent)
        tgt.gauges["shield"] = shield - decay
        b.log.append(f"{tgt.name}'s shield decays by {decay} ({int(decay_percent*100)}%).")
