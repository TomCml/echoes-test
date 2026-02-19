"""Stat scaling opcodes - Stats qui scale avec d'autres stats.

IMPORTANT: Tous les ratios et valeurs doivent être fournis par les items JSON.
Ces opcodes ne doivent PAS avoir de valeurs hardcodées par défaut.
"""
from typing import Dict, Any
from app.engine.combat import register
from app.engine.domain import Battle, Entity


@register("adaptive_force")
def eff_adaptive_force(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Ajoute de la force adaptative (AD si AD > AP, sinon AP).
    
    Params (depuis item JSON):
        amount: int - Montant de force adaptative à ajouter (REQUIS)
    """
    if "amount" not in p:
        b.log.append("[WARN] adaptive_force: 'amount' param missing")
        return
    
    amount = int(p["amount"])
    
    if tgt.stats.AD >= tgt.stats.AP:
        tgt.stats.AD += amount
        b.log.append(f"{tgt.name} gains +{amount} AD (adaptive).")
    else:
        tgt.stats.AP += amount
        b.log.append(f"{tgt.name} gains +{amount} AP (adaptive).")


@register("hp_to_ad")
def eff_hp_to_ad(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Converti des PV bonus en AD (Titanic Hydra, Sterak's).
    
    Params (depuis item JSON):
        ratio: float - Ratio de conversion (ex: 0.02 = 2% des PV bonus) (REQUIS)
        base_hp: int - PV de base du héro (à soustraire pour calculer PV bonus) (REQUIS)
    """
    if "ratio" not in p:
        b.log.append("[WARN] hp_to_ad: 'ratio' param missing")
        return
    if "base_hp" not in p:
        b.log.append("[WARN] hp_to_ad: 'base_hp' param missing")
        return
    
    ratio = float(p["ratio"])
    base_hp = int(p["base_hp"])
    
    bonus_hp = max(0, tgt.stats.MAX_HP - base_hp)
    bonus_ad = int(bonus_hp * ratio)
    
    tgt.stats.AD += bonus_ad
    b.log.append(f"{tgt.name} gains +{bonus_ad} AD from bonus HP ({int(ratio*100)}% of {bonus_hp}).")


@register("armor_to_ad")
def eff_armor_to_ad(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Converti l'armor en AD.
    
    Params (depuis item JSON):
        ratio: float - Ratio de conversion (ex: 0.1 = 10% d'armor) (REQUIS)
    """
    if "ratio" not in p:
        b.log.append("[WARN] armor_to_ad: 'ratio' param missing")
        return
    
    ratio = float(p["ratio"])
    bonus_ad = int(tgt.stats.ARMOR * ratio)
    tgt.stats.AD += bonus_ad
    b.log.append(f"{tgt.name} gains +{bonus_ad} AD from armor ({int(ratio*100)}% of {tgt.stats.ARMOR}).")


@register("mr_to_ap")
def eff_mr_to_ap(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Converti la MR en AP.
    
    Params (depuis item JSON):
        ratio: float - Ratio de conversion (ex: 0.1 = 10% de MR) (REQUIS)
    """
    if "ratio" not in p:
        b.log.append("[WARN] mr_to_ap: 'ratio' param missing")
        return
    
    ratio = float(p["ratio"])
    bonus_ap = int(tgt.stats.MR * ratio)
    tgt.stats.AP += bonus_ap
    b.log.append(f"{tgt.name} gains +{bonus_ap} AP from MR ({int(ratio*100)}% of {tgt.stats.MR}).")


@register("ap_to_hp")
def eff_ap_to_hp(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Converti l'AP en PV (Rod of Ages, etc.).
    
    Params (depuis item JSON):
        ratio: float - Ratio de conversion (ex: 0.5 = 50% de l'AP en HP) (REQUIS)
    """
    if "ratio" not in p:
        b.log.append("[WARN] ap_to_hp: 'ratio' param missing")
        return
    
    ratio = float(p["ratio"])
    bonus_hp = int(tgt.stats.AP * ratio)
    tgt.stats.MAX_HP += bonus_hp
    tgt.stats.HP += bonus_hp
    b.log.append(f"{tgt.name} gains +{bonus_hp} HP from AP ({int(ratio*100)}% of {tgt.stats.AP}).")


@register("copy_stats")
def eff_copy_stats(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Copie un pourcentage des stats d'une cible.
    
    Params (depuis item JSON):
        stat: str - Nom de la stat à copier (ex: "AD", "AP") (REQUIS)
        percent: float - Pourcentage à copier (REQUIS)
    """
    if "stat" not in p:
        b.log.append("[WARN] copy_stats: 'stat' param missing")
        return
    if "percent" not in p:
        b.log.append("[WARN] copy_stats: 'percent' param missing")
        return
    
    stat = p["stat"]
    percent = float(p["percent"])
    
    target_stat = getattr(tgt.stats, stat, 0)
    copied = int(target_stat * percent)
    
    current = getattr(src.stats, stat, 0)
    setattr(src.stats, stat, current + copied)
    
    b.log.append(f"{src.name} copies {int(percent*100)}% of {tgt.name}'s {stat} (+{copied}).")


@register("stack_scaling_stat")
def eff_stack_scaling_stat(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """
    Augmente une stat par stack d'un buff.
    
    Params (depuis item JSON):
        stat: str - Nom de la stat à augmenter (REQUIS)
        buff_code: str - Code du buff à vérifier (REQUIS)
        per_stack: float - Bonus par stack (REQUIS)
    """
    if "stat" not in p:
        b.log.append("[WARN] stack_scaling_stat: 'stat' param missing")
        return
    if "buff_code" not in p:
        b.log.append("[WARN] stack_scaling_stat: 'buff_code' param missing")
        return
    if "per_stack" not in p:
        b.log.append("[WARN] stack_scaling_stat: 'per_stack' param missing")
        return
    
    stat = p["stat"]
    buff_code = p["buff_code"]
    per_stack = float(p["per_stack"])
    
    status = tgt.statuses.get(buff_code)
    if not status:
        return
    
    stacks = status.get("stacks", 0)
    bonus = int(per_stack * stacks)
    
    current = getattr(tgt.stats, stat, 0)
    setattr(tgt.stats, stat, current + bonus)
    
    b.log.append(f"{tgt.name} gains +{bonus} {stat} from {stacks} {buff_code} stacks.")
