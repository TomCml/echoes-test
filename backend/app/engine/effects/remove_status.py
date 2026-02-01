from app.engine.combat import register
from app.engine.domain import Battle, Entity
from typing import Dict, Any


@register("remove_status")
def eff_remove_status(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    code = p["status_code"]
    if code in tgt.statuses:
        del tgt.statuses[code]
        b.log.append(f"{tgt.name} loses {code}.")
    else:
        b.log.append(f"{tgt.name} didn't have {code}.")
