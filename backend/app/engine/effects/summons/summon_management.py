"""Summon management opcodes - Gestion des invocations.

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


@register("summon_entity")
def eff_summon_entity(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Invoque une entité. 
    Params: summon_id (REQUIS), name (REQUIS), base_hp (REQUIS), base_ad (REQUIS), 
            base_ap (REQUIS), duration (REQUIS), hp_ratio (optionnel), ad_ratio (optionnel), ap_ratio (optionnel)
    """
    if not _require_param(b, "summon_entity", p, "summon_id"): return
    if not _require_param(b, "summon_entity", p, "name"): return
    if not _require_param(b, "summon_entity", p, "base_hp"): return
    if not _require_param(b, "summon_entity", p, "base_ad"): return
    if not _require_param(b, "summon_entity", p, "base_ap"): return
    if not _require_param(b, "summon_entity", p, "duration"): return
    
    summon_id = p["summon_id"]
    summon_name = p["name"]
    
    base_hp = int(p["base_hp"])
    hp_ratio = float(p.get("hp_ratio", 0))
    base_ad = int(p["base_ad"])
    ad_ratio = float(p.get("ad_ratio", 0))
    base_ap = int(p["base_ap"])
    ap_ratio = float(p.get("ap_ratio", 0))
    
    summon_hp = base_hp + int(src.stats.MAX_HP * hp_ratio)
    summon_ad = base_ad + int(src.stats.AD * ad_ratio)
    summon_ap = base_ap + int(src.stats.AP * ap_ratio)
    
    summon_data = {
        "id": f"{src.id}_{summon_id}",
        "name": summon_name,
        "hp": summon_hp,
        "max_hp": summon_hp,
        "ad": summon_ad,
        "ap": summon_ap,
        "owner": src.id,
        "duration": int(p["duration"])
    }
    
    src.gauges[f"summon_{summon_id}"] = 1
    src.gauges[f"summon_{summon_id}_data"] = summon_data
    
    b.log.append(f"{src.name} summons {summon_name} (HP: {summon_hp}, AD: {summon_ad}).")


@register("dismiss_summon")
def eff_dismiss_summon(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Renvoie une invocation. Params: summon_id (REQUIS)"""
    if not _require_param(b, "dismiss_summon", p, "summon_id"): return
    
    summon_id = p["summon_id"]
    
    if src.gauges.get(f"summon_{summon_id}"):
        del src.gauges[f"summon_{summon_id}"]
        if f"summon_{summon_id}_data" in src.gauges:
            del src.gauges[f"summon_{summon_id}_data"]
        b.log.append(f"{src.name}'s summon dismissed.")
    else:
        b.log.append(f"{src.name} has no summon to dismiss.")


@register("summon_attack")
def eff_summon_attack(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """L'invocation attaque. Params: summon_id (REQUIS)"""
    if not _require_param(b, "summon_attack", p, "summon_id"): return
    
    summon_id = p["summon_id"]
    summon_data = src.gauges.get(f"summon_{summon_id}_data")
    if not summon_data:
        b.log.append(f"No summon to attack with.")
        return
    
    damage = summon_data.get("ad", 10)
    label = f"{summon_data.get('name', 'Summon')} attack"
    
    from app.engine.combat import apply_damage
    apply_damage(b, tgt, damage, label)


@register("summon_ability")
def eff_summon_ability(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """L'invocation utilise une capacité. Params: summon_id (REQUIS), damage (REQUIS), damage_type (REQUIS), ap_ratio (REQUIS)"""
    if not _require_param(b, "summon_ability", p, "summon_id"): return
    if not _require_param(b, "summon_ability", p, "damage"): return
    if not _require_param(b, "summon_ability", p, "damage_type"): return
    if not _require_param(b, "summon_ability", p, "ap_ratio"): return
    
    summon_id = p["summon_id"]
    summon_data = src.gauges.get(f"summon_{summon_id}_data")
    if not summon_data:
        return
    
    ability_damage = float(p["damage"])
    ability_type = p["damage_type"]
    ap_ratio = float(p["ap_ratio"])
    
    damage = ability_damage + summon_data.get("ap", 0) * ap_ratio
    label = f"{summon_data.get('name', 'Summon')} ability"
    
    import math
    if ability_type == "physical":
        resistance = tgt.stats.ARMOR
    else:
        resistance = tgt.stats.MR
    
    if resistance > 0:
        damage *= math.exp(-resistance / 448.6)
    
    from app.engine.combat import apply_damage
    apply_damage(b, tgt, damage, label)


@register("heal_summon")
def eff_heal_summon(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Soigne une invocation. Params: summon_id (REQUIS), amount (REQUIS)"""
    if not _require_param(b, "heal_summon", p, "summon_id"): return
    if not _require_param(b, "heal_summon", p, "amount"): return
    
    summon_id = p["summon_id"]
    amount = int(p["amount"])
    
    summon_data = src.gauges.get(f"summon_{summon_id}_data")
    if not summon_data:
        return
    
    current_hp = summon_data.get("hp", 0)
    max_hp = summon_data.get("max_hp", 100)
    new_hp = min(max_hp, current_hp + amount)
    summon_data["hp"] = new_hp
    
    b.log.append(f"{summon_data.get('name', 'Summon')} healed for {amount} ({new_hp}/{max_hp}).")
