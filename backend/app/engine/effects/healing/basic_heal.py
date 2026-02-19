"""Basic heal opcodes - Soins basiques.

IMPORTANT: Tous les paramètres doivent être fournis par les items JSON.
"""
from typing import Dict, Any
from app.engine.combat import register, eval_formula
from app.engine.domain import Battle, Entity


def _require_param(b: Battle, opcode: str, p: Dict, key: str) -> bool:
    if key not in p:
        b.log.append(f"[WARN] {opcode}: '{key}' param missing")
        return False
    return True


def _apply_antiheal_reduction(entity: Entity, amount: float) -> float:
    """Réduit le soin selon les stacks d'antiheal."""
    antiheal = entity.statuses.get("antiheal")
    if antiheal:
        stacks = antiheal.get("stacks", 1)
        reduction = min(0.8, stacks * 0.4)  # 40% par stack, max 80%
        return amount * (1 - reduction)
    return amount


@register("heal")
def eff_heal(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Soin avec formule. Params: formula (REQUIS), label (REQUIS)"""
    if not _require_param(b, "heal", p, "formula"): return
    if not _require_param(b, "heal", p, "label"): return
    
    amount = eval_formula(p["formula"], src, tgt)
    amount = _apply_antiheal_reduction(tgt, amount)
    
    old_hp = tgt.stats.HP
    tgt.stats.HP = min(tgt.stats.MAX_HP, tgt.stats.HP + int(amount))
    actual_heal = tgt.stats.HP - old_hp
    
    b.log.append(f"{tgt.name} healed {actual_heal} ({p['label']}).")


@register("heal_flat")
def eff_heal_flat(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Soin fixe. Params: amount (REQUIS), label (REQUIS)"""
    if not _require_param(b, "heal_flat", p, "amount"): return
    if not _require_param(b, "heal_flat", p, "label"): return
    
    amount = float(p["amount"])
    amount = _apply_antiheal_reduction(tgt, amount)
    
    old_hp = tgt.stats.HP
    tgt.stats.HP = min(tgt.stats.MAX_HP, tgt.stats.HP + int(amount))
    actual_heal = tgt.stats.HP - old_hp
    
    b.log.append(f"{tgt.name} healed {actual_heal} ({p['label']}).")


@register("heal_percent_max_hp")
def eff_heal_percent_max_hp(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Soin % PV max. Params: percent (REQUIS), label (REQUIS)"""
    if not _require_param(b, "heal_percent_max_hp", p, "percent"): return
    if not _require_param(b, "heal_percent_max_hp", p, "label"): return
    
    percent = float(p["percent"])
    label = p["label"]
    
    amount = tgt.stats.MAX_HP * percent
    amount = _apply_antiheal_reduction(tgt, amount)
    
    old_hp = tgt.stats.HP
    tgt.stats.HP = min(tgt.stats.MAX_HP, tgt.stats.HP + int(amount))
    actual_heal = tgt.stats.HP - old_hp
    
    b.log.append(f"{tgt.name} healed {actual_heal} ({int(percent*100)}% max HP, {label}).")


@register("heal_percent_missing_hp")
def eff_heal_percent_missing_hp(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Soin % PV manquants. Params: percent (REQUIS), label (REQUIS)"""
    if not _require_param(b, "heal_percent_missing_hp", p, "percent"): return
    if not _require_param(b, "heal_percent_missing_hp", p, "label"): return
    
    percent = float(p["percent"])
    label = p["label"]
    
    missing_hp = tgt.stats.MAX_HP - tgt.stats.HP
    amount = missing_hp * percent
    amount = _apply_antiheal_reduction(tgt, amount)
    
    old_hp = tgt.stats.HP
    tgt.stats.HP = min(tgt.stats.MAX_HP, tgt.stats.HP + int(amount))
    actual_heal = tgt.stats.HP - old_hp
    
    b.log.append(f"{tgt.name} healed {actual_heal} ({int(percent*100)}% missing HP, {label}).")


@register("self_heal")
def eff_self_heal(b: Battle, src: Entity, tgt: Entity, p: Dict[str, Any]):
    """Soin sur le lanceur. Params: formula (REQUIS), label (REQUIS)"""
    if not _require_param(b, "self_heal", p, "formula"): return
    if not _require_param(b, "self_heal", p, "label"): return
    
    amount = eval_formula(p["formula"], src, src)
    amount = _apply_antiheal_reduction(src, amount)
    
    old_hp = src.stats.HP
    src.stats.HP = min(src.stats.MAX_HP, src.stats.HP + int(amount))
    actual_heal = src.stats.HP - old_hp
    
    b.log.append(f"{src.name} self-healed {actual_heal} ({p['label']}).")
