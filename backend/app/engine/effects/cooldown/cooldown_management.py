"""Cooldown management opcodes - Gestion des cooldowns.

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


@register("set_cooldown")
def eff_set_cooldown(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Set un cooldown sur une ability. Params: ability (REQUIS), turns (REQUIS)"""
    if not _require_param(b, "set_cooldown", p, "ability"): return
    if not _require_param(b, "set_cooldown", p, "turns"): return
    
    ability = p["ability"]
    turns = int(p["turns"])
    
    src.cds[ability] = turns
    b.log.append(f"{src.name}'s {ability} on cooldown for {turns}t.")


@register("reduce_cooldown")
def eff_reduce_cooldown(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Réduit un cooldown. Params: reduction (REQUIS), ability (REQUIS si pas all), all (optionnel)"""
    if not _require_param(b, "reduce_cooldown", p, "reduction"): return
    
    reduction = int(p["reduction"])
    all_abilities = bool(p.get("all", False))
    
    if all_abilities:
        for ab, cd in src.cds.items():
            if cd > 0:
                src.cds[ab] = max(0, cd - reduction)
        b.log.append(f"{src.name}'s all cooldowns reduced by {reduction}t.")
    else:
        if not _require_param(b, "reduce_cooldown", p, "ability"): return
        ability = p["ability"]
        current = src.cds.get(ability, 0)
        src.cds[ability] = max(0, current - reduction)
        b.log.append(f"{src.name}'s {ability} cooldown reduced by {reduction}t.")


@register("reset_cooldown")
def eff_reset_cooldown(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Reset un cooldown. Params: ability (REQUIS si pas all), all (optionnel)"""
    all_abilities = bool(p.get("all", False))
    
    if all_abilities:
        src.cds.clear()
        b.log.append(f"{src.name}'s all cooldowns reset!")
    else:
        if not _require_param(b, "reset_cooldown", p, "ability"): return
        ability = p["ability"]
        src.cds[ability] = 0
        b.log.append(f"{src.name}'s {ability} cooldown reset!")


@register("check_cooldown")
def eff_check_cooldown(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Vérifie si une ability est en cooldown. Params: ability (REQUIS)"""
    if not _require_param(b, "check_cooldown", p, "ability"): return True  # Considéré en CD si erreur
    
    ability = p["ability"]
    cd = src.cds.get(ability, 0)
    
    if cd > 0:
        b.log.append(f"{ability} is on cooldown ({cd}t remaining).")
        return False
    return True


@register("tick_cooldowns")
def eff_tick_cooldowns(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Réduit tous les cooldowns de 1 (appelé chaque tour). Params: aucun requis"""
    for ability in list(src.cds.keys()):
        if src.cds[ability] > 0:
            src.cds[ability] -= 1
            if src.cds[ability] == 0:
                b.log.append(f"{src.name}'s {ability} is ready!")


@register("cooldown_reduction_percent")
def eff_cooldown_reduction_percent(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique une réduction de cooldown en %. Params: ability (REQUIS), percent (REQUIS)"""
    if not _require_param(b, "cooldown_reduction_percent", p, "ability"): return
    if not _require_param(b, "cooldown_reduction_percent", p, "percent"): return
    
    ability = p["ability"]
    percent = float(p["percent"])
    
    current = src.cds.get(ability, 0)
    reduction = int(current * percent)
    src.cds[ability] = current - reduction
    b.log.append(f"{src.name}'s {ability} cooldown reduced by {int(percent*100)}% (-{reduction}t).")


@register("extend_cooldown")
def eff_extend_cooldown(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Prolonge un cooldown (debuff). Params: ability (REQUIS), turns (REQUIS)"""
    if not _require_param(b, "extend_cooldown", p, "ability"): return
    if not _require_param(b, "extend_cooldown", p, "turns"): return
    
    ability = p["ability"]
    turns = int(p["turns"])
    
    current = tgt.cds.get(ability, 0)
    tgt.cds[ability] = current + turns
    b.log.append(f"{tgt.name}'s {ability} cooldown extended by {turns}t.")
