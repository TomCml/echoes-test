from app.engine.combat import register
from app.engine.domain import Battle, Entity
from typing import Dict, Any


@register("modify_stat")
def eff_modify_stat(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    stat_name = p["stat"]  # ex: "AD", "ARMOR", "MR"
    amount = int(p["amount"])  # positif = buff, négatif = debuff
    current = getattr(tgt.stats, stat_name, None)
    if current is None:
        b.log.append(f"[WARN] unknown stat: {stat_name}")
        return
    setattr(tgt.stats, stat_name, current + amount)
    sign = "+" if amount >= 0 else ""
    b.log.append(f"{tgt.name} {stat_name} {sign}{amount} (now {current + amount})")
