"""
Status Engine — Gestion des statuts pendant le combat.

Hooks :
  start_turn(b, who)  → tick statuts ON_TURN_START
  end_turn(b, who)    → tick statuts ON_TURN_END, décrement durées, rm expirés, tick CDs
"""
from app.engine.domain import Battle, Entity
from app.engine.combat import run_effects
from app.schemas.combat_events import StatusTickEvent, StatusExpiredEvent


def start_turn(b: Battle, who: Entity):
    """
    Début de tour pour une entité :
    1. Tick tous les statuts qui ont trigger=on_turn_start
    """
    for code, inst in list(who.statuses.items()):
        defn = b.status_defs.get(code)
        if defn and defn.get("tick", {}).get("trigger") == "on_turn_start":
            b.add_log(f"🔄 {who.name}: status {code} ticks (start)")
            b.emit(StatusTickEvent(
                turn=0, sequence=0,
                target=who.id,
                status_code=code,
                effect_type=defn["tick"]["effect"].get("opcode", "unknown"),
            ))
            run_effects(b, who, b.other(who), [defn["tick"]["effect"]])


def end_turn(b: Battle, who: Entity):
    """
    Fin de tour pour une entité :
    1. Tick tous les statuts qui ont trigger=on_turn_end
    2. Décrémenter la durée de tous les statuts
    3. Supprimer les statuts expirés
    4. Décrémenter tous les cooldowns
    """
    # Tick on_turn_end statuses
    for code, inst in list(who.statuses.items()):
        defn = b.status_defs.get(code)
        if defn and defn.get("tick", {}).get("trigger") == "on_turn_end":
            b.add_log(f"🔄 {who.name}: status {code} ticks (end)")
            b.emit(StatusTickEvent(
                turn=0, sequence=0,
                target=who.id,
                status_code=code,
                effect_type=defn["tick"]["effect"].get("opcode", "unknown"),
            ))
            run_effects(b, who, b.other(who), [defn["tick"]["effect"]])

    # Decrement durations + remove expired
    for code in list(who.statuses.keys()):
        who.statuses[code]["remaining"] -= 1
        if who.statuses[code]["remaining"] <= 0:
            del who.statuses[code]
            b.add_log(f"{who.name} loses status {code}.")
            b.emit(StatusExpiredEvent(
                turn=0, sequence=0,
                target=who.id,
                status_code=code,
            ))

    # Tick cooldowns
    for k in list(who.cds.keys()):
        if who.cds[k] > 0:
            who.cds[k] -= 1
            if who.cds[k] == 0:
                del who.cds[k]
