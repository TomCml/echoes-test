"""Special opcodes - Effets spéciaux uniques.

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


@register("stasis")
def eff_stasis(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Met la cible en stase (invulnérable mais ne peut pas agir). Params: duration (REQUIS)"""
    if not _require_param(b, "stasis", p, "duration"): return
    
    duration = int(p["duration"])
    tgt.statuses["stasis"] = {"remaining": duration, "stacks": 1}
    b.log.append(f"{tgt.name} enters stasis for {duration}t (invulnerable, cannot act).")


@register("replay_turn")
def eff_replay_turn(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Permet de rejouer le tour (bonus action). Params: aucun requis"""
    src.gauges["bonus_action"] = src.gauges.get("bonus_action", 0) + 1
    b.log.append(f"{src.name} gains a bonus action!")


@register("resurrect")
def eff_resurrect(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Ressuscite le héro (Guardian Angel, Fruit revigorant). Params: hp_percent (REQUIS)"""
    if not _require_param(b, "resurrect", p, "hp_percent"): return
    
    hp_percent = float(p["hp_percent"])
    
    if tgt.stats.HP > 0:
        b.log.append(f"{tgt.name} is not dead.")
        return
    
    tgt.stats.HP = int(tgt.stats.MAX_HP * hp_percent)
    b.log.append(f"{tgt.name} resurrected with {tgt.stats.HP} HP ({int(hp_percent*100)}% max HP)!")


@register("copy_last_spell")
def eff_copy_last_spell(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Copie le dernier sort utilisé. Params: aucun requis"""
    last_spell = src.gauges.get("last_spell")
    
    if not last_spell:
        b.log.append(f"No spell to copy.")
        return
    
    b.log.append(f"{src.name} copies last spell!")
    
    from app.engine.combat import REGISTRY
    opcode = last_spell.get("opcode")
    params = last_spell.get("params", {})
    
    if opcode in REGISTRY:
        REGISTRY[opcode](b, src, tgt, params)


@register("steal_buff")
def eff_steal_buff(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Vole un buff de la cible. Params: aucun requis"""
    buff_codes = [
        "regeneration", "meditation", "puissance", "haste", "rythme",
        "mur", "impact", "focus", "concentration", "volonte"
    ]
    
    stolen = None
    for code in buff_codes:
        if code in tgt.statuses:
            stolen = code
            src.statuses[code] = tgt.statuses.pop(code)
            break
    
    if stolen:
        b.log.append(f"{src.name} steals {stolen} from {tgt.name}!")
    else:
        b.log.append(f"{tgt.name} has no buffs to steal.")


@register("swap_hp")
def eff_swap_hp(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Échange les PV actuels avec la cible. Params: aucun requis"""
    src_hp = src.stats.HP
    tgt_hp = tgt.stats.HP
    
    src.stats.HP = min(src.stats.MAX_HP, tgt_hp)
    tgt.stats.HP = min(tgt.stats.MAX_HP, src_hp)
    
    b.log.append(f"{src.name} and {tgt.name} swap HP! ({src.stats.HP}, {tgt.stats.HP})")


@register("execute_if_low")
def eff_execute_if_low(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Exécute instantanément si la cible est sous un seuil. Params: threshold (REQUIS)"""
    if not _require_param(b, "execute_if_low", p, "threshold"): return
    
    threshold = float(p["threshold"])
    hp_percent = tgt.stats.HP / tgt.stats.MAX_HP
    
    if hp_percent <= threshold:
        tgt.stats.HP = 0
        b.log.append(f"{tgt.name} executed! (was at {int(hp_percent*100)}% HP)")
    else:
        b.log.append(f"{tgt.name} not low enough for execution ({int(hp_percent*100)}% > {int(threshold*100)}%)")


@register("damage_cap")
def eff_damage_cap(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Applique un cap de dégâts max par attaque. Params: cap_percent (REQUIS), duration (REQUIS)"""
    if not _require_param(b, "damage_cap", p, "cap_percent"): return
    if not _require_param(b, "damage_cap", p, "duration"): return
    
    cap_percent = float(p["cap_percent"])
    duration = int(p["duration"])
    
    src.statuses["damage_cap"] = {
        "remaining": duration,
        "stacks": 1,
        "cap_percent": cap_percent
    }
    b.log.append(f"{src.name} gains damage cap ({int(cap_percent*100)}% max HP per hit).")


@register("revive_on_death")
def eff_revive_on_death(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Prépare une résurrection à la mort. Params: hp_percent (REQUIS), duration (REQUIS)"""
    if not _require_param(b, "revive_on_death", p, "hp_percent"): return
    if not _require_param(b, "revive_on_death", p, "duration"): return
    
    hp_percent = float(p["hp_percent"])
    duration = int(p["duration"])
    
    tgt.statuses["revive_pending"] = {
        "remaining": duration,
        "stacks": 1,
        "hp_percent": hp_percent
    }
    b.log.append(f"{tgt.name} will revive at {int(hp_percent*100)}% HP on death.")
