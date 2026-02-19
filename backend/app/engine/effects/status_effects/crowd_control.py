"""Crowd control opcodes - Effets de contrôle.

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


@register("apply_stun")
def eff_apply_stun(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Stun. Params: duration (REQUIS), chance (REQUIS - 0.0 à 1.0)"""
    if not _require_param(b, "apply_stun", p, "duration"): return
    if not _require_param(b, "apply_stun", p, "chance"): return
    
    duration = int(p["duration"])
    chance = float(p["chance"])
    
    if b.rng.random() > chance:
        b.log.append(f"{tgt.name} resisted stun ({int(chance*100)}% chance).")
        return
    
    tgt.statuses["stun"] = {"remaining": duration, "stacks": 1}
    b.log.append(f"{tgt.name} is stunned for {duration}t!")


@register("apply_silence")
def eff_apply_silence(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Silence. Params: duration (REQUIS), chance (REQUIS)"""
    if not _require_param(b, "apply_silence", p, "duration"): return
    if not _require_param(b, "apply_silence", p, "chance"): return
    
    duration = int(p["duration"])
    chance = float(p["chance"])
    
    if b.rng.random() > chance:
        b.log.append(f"{tgt.name} resisted silence ({int(chance*100)}% chance).")
        return
    
    tgt.statuses["silence"] = {"remaining": duration, "stacks": 1}
    b.log.append(f"{tgt.name} is silenced for {duration}t!")


@register("apply_root")
def eff_apply_root(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Root/Immobilisation. Params: duration (REQUIS), chance (REQUIS)"""
    if not _require_param(b, "apply_root", p, "duration"): return
    if not _require_param(b, "apply_root", p, "chance"): return
    
    duration = int(p["duration"])
    chance = float(p["chance"])
    
    if b.rng.random() > chance:
        b.log.append(f"{tgt.name} resisted root ({int(chance*100)}% chance).")
        return
    
    tgt.statuses["root"] = {"remaining": duration, "stacks": 1}
    b.log.append(f"{tgt.name} is rooted for {duration}t!")


@register("apply_fear")
def eff_apply_fear(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Fear. Params: duration (REQUIS), chance (REQUIS)"""
    if not _require_param(b, "apply_fear", p, "duration"): return
    if not _require_param(b, "apply_fear", p, "chance"): return
    
    duration = int(p["duration"])
    chance = float(p["chance"])
    
    if b.rng.random() > chance:
        b.log.append(f"{tgt.name} resisted fear ({int(chance*100)}% chance).")
        return
    
    tgt.statuses["fear"] = {"remaining": duration, "stacks": 1}
    b.log.append(f"{tgt.name} is feared for {duration}t!")


@register("apply_taunt")
def eff_apply_taunt(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Taunt (doit attaquer le lanceur). Params: duration (REQUIS)"""
    if not _require_param(b, "apply_taunt", p, "duration"): return
    
    duration = int(p["duration"])
    tgt.statuses["taunt"] = {"remaining": duration, "stacks": 1, "source": src.id}
    b.log.append(f"{tgt.name} is taunted by {src.name} for {duration}t!")


@register("apply_charm")
def eff_apply_charm(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Charm. Params: duration (REQUIS), chance (REQUIS)"""
    if not _require_param(b, "apply_charm", p, "duration"): return
    if not _require_param(b, "apply_charm", p, "chance"): return
    
    duration = int(p["duration"])
    chance = float(p["chance"])
    
    if b.rng.random() > chance:
        b.log.append(f"{tgt.name} resisted charm ({int(chance*100)}% chance).")
        return
    
    tgt.statuses["charm"] = {"remaining": duration, "stacks": 1, "source": src.id}
    b.log.append(f"{tgt.name} is charmed for {duration}t!")


@register("apply_sleep")
def eff_apply_sleep(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Sleep. Params: duration (REQUIS)"""
    if not _require_param(b, "apply_sleep", p, "duration"): return
    
    duration = int(p["duration"])
    tgt.statuses["sleep"] = {"remaining": duration, "stacks": 1}
    b.log.append(f"{tgt.name} falls asleep for {duration}t!")


@register("apply_airborne")
def eff_apply_airborne(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique Airborne/Knock-up. Params: duration (REQUIS)"""
    if not _require_param(b, "apply_airborne", p, "duration"): return
    
    duration = int(p["duration"])
    tgt.statuses["airborne"] = {"remaining": duration, "stacks": 1}
    b.log.append(f"{tgt.name} is knocked airborne for {duration}t!")
