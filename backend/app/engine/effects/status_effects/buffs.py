"""Buff opcodes - Effets positifs.

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


def _apply_buff(b: Battle, tgt: Entity, code: str, duration: int, stacks: int):
    """Helper pour appliquer un buff."""
    current = tgt.statuses.get(code)
    if current:
        current["stacks"] = current.get("stacks", 0) + stacks
        current["remaining"] = max(current["remaining"], duration)
    else:
        tgt.statuses[code] = {"remaining": duration, "stacks": stacks}
    b.log.append(f"{tgt.name} gains {code} ({stacks} stacks, {duration}t).")


@register("apply_buff")
def eff_apply_buff(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique un buff générique. Params: buff_code (REQUIS), duration (REQUIS), stacks (REQUIS)"""
    if not _require_param(b, "apply_buff", p, "buff_code"): return
    if not _require_param(b, "apply_buff", p, "duration"): return
    if not _require_param(b, "apply_buff", p, "stacks"): return
    _apply_buff(b, tgt, p["buff_code"], int(p["duration"]), int(p["stacks"]))


@register("apply_puissance")
def eff_apply_puissance(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Puissance (+10% dégâts/stack). Params: duration (REQUIS), stacks (REQUIS)"""
    if not _require_param(b, "apply_puissance", p, "duration"): return
    if not _require_param(b, "apply_puissance", p, "stacks"): return
    _apply_buff(b, tgt, "puissance", int(p["duration"]), int(p["stacks"]))


@register("apply_haste")
def eff_apply_haste(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Hâte (+vitesse/stack). Params: duration (REQUIS), stacks (REQUIS)"""
    if not _require_param(b, "apply_haste", p, "duration"): return
    if not _require_param(b, "apply_haste", p, "stacks"): return
    _apply_buff(b, tgt, "haste", int(p["duration"]), int(p["stacks"]))


@register("apply_rythme")
def eff_apply_rythme(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Rythme (+4 vitesse/stack). Params: duration (REQUIS), stacks (REQUIS)"""
    if not _require_param(b, "apply_rythme", p, "duration"): return
    if not _require_param(b, "apply_rythme", p, "stacks"): return
    _apply_buff(b, tgt, "rythme", int(p["duration"]), int(p["stacks"]))


@register("apply_mur")
def eff_apply_mur(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Mur (+8% armor/MR/stack). Params: duration (REQUIS), stacks (REQUIS)"""
    if not _require_param(b, "apply_mur", p, "duration"): return
    if not _require_param(b, "apply_mur", p, "stacks"): return
    _apply_buff(b, tgt, "mur", int(p["duration"]), int(p["stacks"]))


@register("apply_impact")
def eff_apply_impact(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Impact (bonus AP prochain sort). Params: duration (REQUIS), stacks (REQUIS)"""
    if not _require_param(b, "apply_impact", p, "duration"): return
    if not _require_param(b, "apply_impact", p, "stacks"): return
    _apply_buff(b, tgt, "impact", int(p["duration"]), int(p["stacks"]))


@register("apply_focus")
def eff_apply_focus(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Focus (+15% crit/stack). Params: duration (REQUIS), stacks (REQUIS)"""
    if not _require_param(b, "apply_focus", p, "duration"): return
    if not _require_param(b, "apply_focus", p, "stacks"): return
    _apply_buff(b, tgt, "focus", int(p["duration"]), int(p["stacks"]))


@register("apply_concentration")
def eff_apply_concentration(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Concentration (ignore résistances partiel). Params: duration (REQUIS), stacks (REQUIS)"""
    if not _require_param(b, "apply_concentration", p, "duration"): return
    if not _require_param(b, "apply_concentration", p, "stacks"): return
    _apply_buff(b, tgt, "concentration", int(p["duration"]), int(p["stacks"]))


@register("apply_volonte")
def eff_apply_volonte(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Volonté (-20% dégâts reçus/stack). Params: duration (REQUIS), stacks (REQUIS)"""
    if not _require_param(b, "apply_volonte", p, "duration"): return
    if not _require_param(b, "apply_volonte", p, "stacks"): return
    _apply_buff(b, tgt, "volonte", int(p["duration"]), int(p["stacks"]))


@register("apply_voile")
def eff_apply_voile(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Voile (bloque prochain sort). Params: duration (REQUIS)"""
    if not _require_param(b, "apply_voile", p, "duration"): return
    _apply_buff(b, tgt, "voile", int(p["duration"]), 1)


@register("apply_regeneration")
def eff_apply_regeneration(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Régénération. Params: duration (REQUIS), stacks (REQUIS)"""
    if not _require_param(b, "apply_regeneration", p, "duration"): return
    if not _require_param(b, "apply_regeneration", p, "stacks"): return
    _apply_buff(b, tgt, "regeneration", int(p["duration"]), int(p["stacks"]))


@register("apply_meditation")
def eff_apply_meditation(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Méditation (soin/tour). Params: duration (REQUIS), stacks (REQUIS)"""
    if not _require_param(b, "apply_meditation", p, "duration"): return
    if not _require_param(b, "apply_meditation", p, "stacks"): return
    _apply_buff(b, tgt, "meditation", int(p["duration"]), int(p["stacks"]))
