"""Debuff opcodes - Effets négatifs.

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


def _apply_debuff(b: Battle, tgt: Entity, code: str, duration: int, stacks: int):
    """Helper pour appliquer un debuff."""
    current = tgt.statuses.get(code)
    if current:
        current["stacks"] = current.get("stacks", 0) + stacks
        current["remaining"] = max(current["remaining"], duration)
    else:
        tgt.statuses[code] = {"remaining": duration, "stacks": stacks}
    b.log.append(f"{tgt.name} suffers {code} ({stacks} stacks, {duration}t).")


@register("apply_debuff")
def eff_apply_debuff(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique un debuff générique. Params: debuff_code (REQUIS), duration (REQUIS), stacks (REQUIS)"""
    if not _require_param(b, "apply_debuff", p, "debuff_code"): return
    if not _require_param(b, "apply_debuff", p, "duration"): return
    if not _require_param(b, "apply_debuff", p, "stacks"): return
    _apply_debuff(b, tgt, p["debuff_code"], int(p["duration"]), int(p["stacks"]))


@register("apply_burn")
def eff_apply_burn_status(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Brûlure (DoT). Params: duration (REQUIS), stacks (REQUIS)"""
    if not _require_param(b, "apply_burn", p, "duration"): return
    if not _require_param(b, "apply_burn", p, "stacks"): return
    _apply_debuff(b, tgt, "burn", int(p["duration"]), int(p["stacks"]))


@register("apply_laceration")
def eff_apply_laceration(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Lacération (DoT physique). Params: duration (REQUIS), stacks (REQUIS)"""
    if not _require_param(b, "apply_laceration", p, "duration"): return
    if not _require_param(b, "apply_laceration", p, "stacks"): return
    _apply_debuff(b, tgt, "laceration", int(p["duration"]), int(p["stacks"]))


@register("apply_fatigue")
def eff_apply_fatigue(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Fatigue (-vitesse). Params: duration (REQUIS), stacks (REQUIS)"""
    if not _require_param(b, "apply_fatigue", p, "duration"): return
    if not _require_param(b, "apply_fatigue", p, "stacks"): return
    _apply_debuff(b, tgt, "fatigue", int(p["duration"]), int(p["stacks"]))


@register("apply_slow")
def eff_apply_slow(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Slow/Ralentissement. Params: duration (REQUIS), stacks (REQUIS)"""
    if not _require_param(b, "apply_slow", p, "duration"): return
    if not _require_param(b, "apply_slow", p, "stacks"): return
    _apply_debuff(b, tgt, "slow", int(p["duration"]), int(p["stacks"]))


@register("apply_vulnerability")
def eff_apply_vulnerability(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Vulnérabilité (+dégâts reçus). Params: duration (REQUIS), stacks (REQUIS)"""
    if not _require_param(b, "apply_vulnerability", p, "duration"): return
    if not _require_param(b, "apply_vulnerability", p, "stacks"): return
    _apply_debuff(b, tgt, "vulnerability", int(p["duration"]), int(p["stacks"]))


@register("apply_antiheal")
def eff_apply_antiheal(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Anti-heal (réduit les soins). Params: duration (REQUIS), stacks (REQUIS)"""
    if not _require_param(b, "apply_antiheal", p, "duration"): return
    if not _require_param(b, "apply_antiheal", p, "stacks"): return
    _apply_debuff(b, tgt, "antiheal", int(p["duration"]), int(p["stacks"]))


@register("apply_armor_reduction")
def eff_apply_armor_reduction(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Réduction d'armure. Params: duration (REQUIS), stacks (REQUIS)"""
    if not _require_param(b, "apply_armor_reduction", p, "duration"): return
    if not _require_param(b, "apply_armor_reduction", p, "stacks"): return
    _apply_debuff(b, tgt, "armor_reduction", int(p["duration"]), int(p["stacks"]))


@register("apply_mr_reduction")
def eff_apply_mr_reduction(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Réduction de MR. Params: duration (REQUIS), stacks (REQUIS)"""
    if not _require_param(b, "apply_mr_reduction", p, "duration"): return
    if not _require_param(b, "apply_mr_reduction", p, "stacks"): return
    _apply_debuff(b, tgt, "mr_reduction", int(p["duration"]), int(p["stacks"]))


@register("apply_glancing_glow")
def eff_apply_glancing_glow(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Lueur oblique (-25% dégâts AA). Params: duration (REQUIS), stacks (REQUIS)"""
    if not _require_param(b, "apply_glancing_glow", p, "duration"): return
    if not _require_param(b, "apply_glancing_glow", p, "stacks"): return
    _apply_debuff(b, tgt, "glancing_glow", int(p["duration"]), int(p["stacks"]))


@register("apply_critiquable")
def eff_apply_critiquable(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Critiquable (+20% dégâts crit reçus). Params: duration (REQUIS), stacks (REQUIS)"""
    if not _require_param(b, "apply_critiquable", p, "duration"): return
    if not _require_param(b, "apply_critiquable", p, "stacks"): return
    _apply_debuff(b, tgt, "critiquable", int(p["duration"]), int(p["stacks"]))


@register("apply_exposed")
def eff_apply_exposed(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Exposé (dégâts bonus prochaine attaque). Params: duration (REQUIS), stacks (REQUIS)"""
    if not _require_param(b, "apply_exposed", p, "duration"): return
    if not _require_param(b, "apply_exposed", p, "stacks"): return
    _apply_debuff(b, tgt, "exposed", int(p["duration"]), int(p["stacks"]))
