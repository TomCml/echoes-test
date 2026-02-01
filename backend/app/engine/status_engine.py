from app.engine.domain import Battle, Entity
from app.engine.combat import run_effects

def end_turn(b: Battle, who: Entity):
    for code, inst in list(who.statuses.items()):
        defn = b.status_defs.get(code)
        if defn and defn.get("tick", {}).get("trigger") == "on_turn_end":
            run_effects(b, who, who, [defn["tick"]["effect"]])
        inst["remaining"] -= 1
        if inst["remaining"] <= 0:
            del who.statuses[code]

    for k in list(who.cds.keys()):
        if who.cds[k] > 0:
            who.cds[k] -= 1
