from typing import Dict, Any, Callable, List
from models.domain import Battle, Entity

EffectFn = Callable[[Battle, Entity, Entity, Dict[str, Any]], None]
REGISTRY: Dict[str, EffectFn] = {} 

def register(opcode: str):
    def deco(fn: EffectFn):
        REGISTRY[opcode] = fn
        return fn
    return deco

def run_effects(b: Battle, src: Entity, tgt: Entity, effects: List[Dict[str, Any]]):
    for e in sorted(effects, key=lambda x: x.get("order", 0)):
        fn = REGISTRY.get(e["opcode"])
        if not fn:
            b.log.append(f"[WARN] unknown opcode: {e['opcode']}")
            continue
        fn(b, src, tgt, e.get("params", {}))

def eval_formula(expr: str, src: Entity, tgt: Entity) -> float:
    scope = {
        **src.stats.__dict__,
        **{f"S_{k}": v for k, v in src.stats.__dict__.items()},
        **{f"T_{k}": v for k, v in tgt.stats.__dict__.items()},
    }

    return float(eval(expr, {"__builtins__": {}}, scope))

def apply_damage(b: Battle, target: Entity, amount: float, label: str = "damage"):
    val = max(1, int(round(amount)))
    target.stats.HP = max(0, target.stats.HP - val)
    b.log.append(f"{target.name} takes {val} ({label}). HP {target.stats.HP}/{target.stats.MAX_HP}")

def apply_status(b: Battle, target: Entity, code: str, duration: int, stacks_inc: int = 1):
    inst = target.statuses.get(code)
    if inst:
        inst["stacks"] = inst.get("stacks", 1) + stacks_inc
        inst["remaining"] = max(inst["remaining"], duration)
    else:
        target.statuses[code] = {"remaining": duration, "stacks": stacks_inc}
    b.log.append(f"{target.name} gains {code} ({duration}t).")
