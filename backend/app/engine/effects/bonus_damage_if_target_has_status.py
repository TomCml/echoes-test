"""Bonus damage if target has status opcode.

IMPORTANT: Tous les paramètres doivent être fournis par les items JSON.
"""
from app.engine.combat import register, apply_damage
from app.engine.effects.base import percent_bonus_from_ad
from app.engine.domain import Battle, Entity
from typing import Dict, Any


def _require_param(b: Battle, opcode: str, p: Dict, key: str) -> bool:
    if key not in p:
        b.log.append(f"[WARN] {opcode}: '{key}' param missing")
        return False
    return True


@register("bonus_damage_if_target_has_status")
def eff_bonus(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Dégâts bonus si la cible a un statut.
    
    Params: status_code (REQUIS), bonus_pct (REQUIS)
    """
    if not _require_param(b, "bonus_damage_if_target_has_status", p, "status_code"): return
    if not _require_param(b, "bonus_damage_if_target_has_status", p, "bonus_pct"): return
    
    code = p["status_code"]
    bonus_pct = float(p["bonus_pct"])
    
    if code in tgt.statuses:
        extra = percent_bonus_from_ad(b, src, bonus_pct)
        apply_damage(b, tgt, extra, f"bonus {int(bonus_pct*100)}% ({code})")
