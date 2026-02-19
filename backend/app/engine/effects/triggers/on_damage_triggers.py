"""On-damage triggers - Déclencheurs lors de dégâts.

IMPORTANT: Tous les paramètres doivent être fournis par les items JSON.
"""
from typing import Dict, Any
from app.engine.combat import register, REGISTRY
from app.engine.domain import Battle, Entity


def _require_param(b: Battle, opcode: str, p: Dict, key: str) -> bool:
    if key not in p:
        b.log.append(f"[WARN] {opcode}: '{key}' param missing")
        return False
    return True


@register("on_damage_dealt")
def eff_on_damage_dealt(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Déclenche des effets après avoir infligé des dégâts. Params: damage_dealt (REQUIS), effects (REQUIS)"""
    if not _require_param(b, "on_damage_dealt", p, "damage_dealt"): return
    if not _require_param(b, "on_damage_dealt", p, "effects"): return
    
    damage_dealt = float(p["damage_dealt"])
    effects = p["effects"]
    
    for effect in effects:
        opcode = effect.get("opcode")
        params = effect.get("params", {})
        params["damage_dealt"] = damage_dealt
        if opcode in REGISTRY:
            REGISTRY[opcode](b, src, tgt, params)


@register("on_damage_taken")
def eff_on_damage_taken(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Déclenche des effets après avoir reçu des dégâts. Params: damage_taken (REQUIS), effects (REQUIS)"""
    if not _require_param(b, "on_damage_taken", p, "damage_taken"): return
    if not _require_param(b, "on_damage_taken", p, "effects"): return
    
    damage_taken = float(p["damage_taken"])
    effects = p["effects"]
    
    for effect in effects:
        opcode = effect.get("opcode")
        params = effect.get("params", {})
        params["damage_taken"] = damage_taken
        if opcode in REGISTRY:
            REGISTRY[opcode](b, tgt, src, params)


@register("damage_reflection")
def eff_damage_reflection(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Renvoie un % des dégâts reçus. Params: damage_taken (REQUIS), percent (REQUIS)"""
    if not _require_param(b, "damage_reflection", p, "damage_taken"): return
    if not _require_param(b, "damage_reflection", p, "percent"): return
    
    damage_taken = float(p["damage_taken"])
    reflect_percent = float(p["percent"])
    
    reflect_damage = damage_taken * reflect_percent
    from app.engine.combat import apply_damage
    apply_damage(b, src, reflect_damage, f"reflected {int(reflect_percent*100)}%")


@register("on_kill")
def eff_on_kill(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Déclenche des effets lors d'un kill. Params: effects (REQUIS)"""
    if not _require_param(b, "on_kill", p, "effects"): return
    
    if tgt.stats.HP > 0:
        return
    
    effects = p["effects"]
    for effect in effects:
        opcode = effect.get("opcode")
        params = effect.get("params", {})
        if opcode in REGISTRY:
            REGISTRY[opcode](b, src, tgt, params)
    
    b.log.append(f"{src.name} killed {tgt.name}! On-kill effects triggered.")


@register("on_low_hp")
def eff_on_low_hp(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Déclenche des effets quand les PV sont bas. Params: threshold (REQUIS), effects (REQUIS), target_self (optionnel)"""
    if not _require_param(b, "on_low_hp", p, "threshold"): return
    if not _require_param(b, "on_low_hp", p, "effects"): return
    
    threshold = float(p["threshold"])
    target_self = bool(p.get("target_self", True))
    
    check_entity = src if target_self else tgt
    hp_percent = check_entity.stats.HP / check_entity.stats.MAX_HP
    
    if hp_percent <= threshold:
        effects = p["effects"]
        for effect in effects:
            opcode = effect.get("opcode")
            params = effect.get("params", {})
            if opcode in REGISTRY:
                REGISTRY[opcode](b, src, tgt, params)
        b.log.append(f"{check_entity.name} below {int(threshold*100)}% HP! Effects triggered.")
