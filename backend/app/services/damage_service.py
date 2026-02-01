"""
Damage Service - Fonctions de calcul des dégâts.
Migré depuis services/damage_service.py (classe -> fonctions)
"""
import math
import logging
from typing import Dict, Any
from app.models.player import Player

logger = logging.getLogger(__name__)


def calculate_damage(
    player: Player,
    target: Player,
    item: Dict[str, Any],
    spell: Dict[str, Any],
    crit: bool
) -> Dict[str, Any]:
    """
    Calcule les dégâts d'un sort.
    
    Args:
        player: Le joueur attaquant (modèle SQLAlchemy)
        target: La cible (modèle SQLAlchemy)
        item: Dict provenant des fichiers JSON
        spell: Dict provenant de item["spells"]
        crit: Si True, applique le multiplicateur critique
    
    Returns:
        Dict avec les détails du calcul de dégâts
    """
    def val(x): return 0.0 if x is None else float(x)

    # Stats du joueur depuis le modèle Player
    ad_stat = val(player.attack_damage)
    ap_stat = val(player.ability_power)
    hp_stat = val(player.health_points)
    armor_stat = val(player.armor)
    mr_stat = val(player.magic_resistance)
    speed_stat = val(player.speed)

    # Extraire les ratios depuis les effects du spell
    # Structure attendue: spell["effects"] = [{"opcode": "damage", "params": {...}}]
    effects = spell.get("effects", [])
    damage_effect = next((e for e in effects if e.get("opcode") == "damage"), {})
    params = damage_effect.get("params", {})

    # Base Damage & Ratios from spell
    ad_base = val(params.get("ad_base_dmg", 0))
    ap_base = val(params.get("ap_base_dmg", 0))
    ad_ratio = val(params.get("ad_ratio", 0))
    ap_ratio = val(params.get("ap_ratio", 0))
    hp_ratio = val(params.get("hp_ratio", 0))
    armor_ratio = val(params.get("armor_ratio", 0))
    mr_ratio = val(params.get("mr_ratio", 0))
    speed_ratio = val(params.get("speed_ratio", 0))

    ad_ratio_dmg = (
        ad_stat * ad_ratio +
        hp_stat * hp_ratio +
        armor_stat * armor_ratio +
        speed_stat * speed_ratio
    )

    ap_ratio_dmg = (
        ap_stat * ap_ratio +
        mr_stat * mr_ratio
    )

    raw_ad = ad_base + ad_ratio_dmg
    raw_ap = ap_base + ap_ratio_dmg

    # Critical Hit
    crit_mult = 1.5 if crit else 1.0
    crit_ad = raw_ad * crit_mult
    crit_ap = raw_ap * crit_mult

    # Target Mitigations
    # TODO: Ajouter penetration au modèle Player si nécessaire
    pen_pct = 0.0
    pen_flat = 0.0

    target_armor = val(target.armor)
    target_mr = val(target.magic_resistance)

    armor_reducted = max(0.0, target_armor * (1 - pen_pct) - pen_flat)
    mr_reducted = max(0.0, target_mr * (1 - pen_pct) - pen_flat)

    # Reduction formula (exponential)
    armor_mult = math.exp(-armor_reducted / 448.6)
    mr_mult = math.exp(-mr_reducted / 448.6)

    post_ad = crit_ad * armor_mult
    post_ap = crit_ap * mr_mult
    
    pre_mod_total = post_ad + post_ap

    # Final modifiers
    dealt_pct = 0.0
    reduc_pct = 0.0
    reduc_flat = 0.0

    final_dmg = pre_mod_total * (1 + dealt_pct) - (pre_mod_total * reduc_pct + reduc_flat)
    final_dmg = max(0.0, final_dmg)

    logger.debug(f"Damage calculated: {final_dmg} (crit={crit})")

    return {
        "total_dmg": crit_ad + crit_ap,
        "new_total_dmg": pre_mod_total,
        "final_dmg": final_dmg,
        "armor_reduction": 1 - armor_mult,
        "mr_reduction": 1 - mr_mult,
        "spell_used": spell.get("code", "unknown"),
        "breakdown": {
            "raw_ad": raw_ad, 
            "raw_ap": raw_ap,
            "crit_ad": crit_ad, 
            "crit_ap": crit_ap,
            "armor_reducted": armor_reducted, 
            "mr_reducted": mr_reducted
        }
    }
