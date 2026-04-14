from app.engine.combat import register, apply_damage
from app.engine.effects.base import percent_bonus_from_ad
from app.engine.domain import Battle, Entity
from typing import Dict, Any

@register("bonus_damage_if_target_has_status")
def eff_bonus(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    code = p["status_code"]
    bonus_pct = float(p.get("bonus_pct", 0.0))
    if code in tgt.statuses:
        extra = percent_bonus_from_ad(b, src, bonus_pct)
        apply_damage(b, tgt, extra, f"bonus {int(bonus_pct*100)}% ({code})")
