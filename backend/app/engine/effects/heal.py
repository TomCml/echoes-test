from app.engine.combat import register, eval_formula
from app.engine.domain import Battle, Entity
from typing import Dict, Any


@register("heal")
def eff_heal(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    base = eval_formula(p["formula"], src, tgt)
    amount = max(1, int(round(base)))
    tgt.stats.HP = min(tgt.stats.MAX_HP, tgt.stats.HP + amount)
    b.log.append(f"{tgt.name} heals {amount}. HP {tgt.stats.HP}/{tgt.stats.MAX_HP}")
