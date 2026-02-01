from app.engine.domain import Battle, Entity
from app.engine.combat import eval_formula, apply_damage

def percent_bonus_from_ad(b: Battle, src: Entity, pct: float) -> float:
    return src.stats.AD * pct
