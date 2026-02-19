"""Status management opcodes - Gestion des statuts.

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


@register("remove_status")
def eff_remove_status(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Retire un statut spécifique. Params: status_code (REQUIS)"""
    if not _require_param(b, "remove_status", p, "status_code"): return
    
    code = p["status_code"]
    if code in tgt.statuses:
        del tgt.statuses[code]
        b.log.append(f"{tgt.name} loses {code}.")
    else:
        b.log.append(f"{tgt.name} didn't have {code}.")


@register("cleanse_debuffs")
def eff_cleanse_debuffs(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Retire tous les debuffs (Purification). Params: aucun requis"""
    debuff_codes = [
        "burn", "laceration", "fatigue", "slow", "stun", "vulnerability",
        "antiheal", "armor_reduction", "mr_reduction", "glancing_glow",
        "critiquable", "exposed", "silence", "root", "fear", "charm", "sleep"
    ]
    
    removed = []
    for code in debuff_codes:
        if code in tgt.statuses:
            del tgt.statuses[code]
            removed.append(code)
    
    if removed:
        b.log.append(f"{tgt.name} cleansed: {', '.join(removed)}.")
    else:
        b.log.append(f"{tgt.name} had no debuffs to cleanse.")


@register("cleanse_buffs")
def eff_cleanse_buffs(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Retire tous les buffs d'une cible (dispel). Params: aucun requis"""
    buff_codes = [
        "regeneration", "meditation", "puissance", "haste", "rythme",
        "mur", "impact", "focus", "concentration", "volonte", "voile"
    ]
    
    removed = []
    for code in buff_codes:
        if code in tgt.statuses:
            del tgt.statuses[code]
            removed.append(code)
    
    if removed:
        b.log.append(f"{tgt.name}'s buffs removed: {', '.join(removed)}.")
    else:
        b.log.append(f"{tgt.name} had no buffs to remove.")


@register("extend_status_duration")
def eff_extend_status_duration(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Prolonge la durée d'un statut. Params: status_code (REQUIS), extra_turns (REQUIS)"""
    if not _require_param(b, "extend_status_duration", p, "status_code"): return
    if not _require_param(b, "extend_status_duration", p, "extra_turns"): return
    
    code = p["status_code"]
    extra_turns = int(p["extra_turns"])
    
    if code in tgt.statuses:
        tgt.statuses[code]["remaining"] += extra_turns
        b.log.append(f"{tgt.name}'s {code} extended by {extra_turns}t.")
    else:
        b.log.append(f"{tgt.name} doesn't have {code}.")


@register("add_status_stacks")
def eff_add_status_stacks(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Ajoute des stacks à un statut existant. Params: status_code (REQUIS), stacks (REQUIS)"""
    if not _require_param(b, "add_status_stacks", p, "status_code"): return
    if not _require_param(b, "add_status_stacks", p, "stacks"): return
    
    code = p["status_code"]
    stacks = int(p["stacks"])
    
    if code in tgt.statuses:
        tgt.statuses[code]["stacks"] = tgt.statuses[code].get("stacks", 0) + stacks
        b.log.append(f"{tgt.name}'s {code} gains {stacks} stacks.")
    else:
        b.log.append(f"{tgt.name} doesn't have {code}, cannot add stacks.")


@register("reduce_status_stacks")
def eff_reduce_status_stacks(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Réduit les stacks d'un statut. Params: status_code (REQUIS), stacks (REQUIS)"""
    if not _require_param(b, "reduce_status_stacks", p, "status_code"): return
    if not _require_param(b, "reduce_status_stacks", p, "stacks"): return
    
    code = p["status_code"]
    stacks = int(p["stacks"])
    
    if code in tgt.statuses:
        current = tgt.statuses[code].get("stacks", 1)
        new_stacks = current - stacks
        if new_stacks <= 0:
            del tgt.statuses[code]
            b.log.append(f"{tgt.name} loses {code}.")
        else:
            tgt.statuses[code]["stacks"] = new_stacks
            b.log.append(f"{tgt.name}'s {code} reduced to {new_stacks} stacks.")
    else:
        b.log.append(f"{tgt.name} doesn't have {code}.")


@register("transfer_status")
def eff_transfer_status(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Transfère un statut d'une entité à une autre. Params: status_code (REQUIS)"""
    if not _require_param(b, "transfer_status", p, "status_code"): return
    
    code = p["status_code"]
    
    if code in src.statuses:
        tgt.statuses[code] = src.statuses.pop(code)
        b.log.append(f"{code} transferred from {src.name} to {tgt.name}.")
    else:
        b.log.append(f"{src.name} doesn't have {code} to transfer.")
