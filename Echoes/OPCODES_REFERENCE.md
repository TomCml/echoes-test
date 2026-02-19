# Echoes Opcodes Reference

> **IMPORTANT**: Ce document liste tous les opcodes disponibles dans le système d'effets.  
> **Tous les paramètres marqués REQUIS doivent être fournis dans les items JSON.**  
> Les paramètres optionnels ont des valeurs par défaut raisonnables (généralement 0 ou false).

## Summary Statistics

- **Total Opcodes**: ~100+
- **Categories**: 10 (damage, healing, shields, status_effects, stat_modifiers, gauge, triggers, cooldown, summons, misc)
- **Architecture**: Tous les opcodes utilisent `_require_param()` pour valider les paramètres obligatoires

---

## 1. Damage Opcodes

### Generic Damage (`damage.py`)

| Opcode | Description | Params (REQUIS) | Params (optionnel) |
|--------|-------------|-----------------|-------------------|
| `damage` | Dégâts génériques avec formule | `formula`, `damage_type`, `can_crit`, `label` | `variance` |

### Physical Damage (`damage/physical_damage.py`)

| Opcode | Description | Params (REQUIS) | Params (optionnel) |
|--------|-------------|-----------------|-------------------|
| `physical_damage` | Dégâts physiques standard | `formula`, `can_crit`, `label` | `variance`, `armor_pen_pct`, `lethality` |
| `physical_damage_ad_ratio` | Dégâts physiques ratio AD | `base`, `ad_ratio`, `can_crit`, `label` | - |
| `basic_attack` | Attaque de base | `ad_ratio`, `can_crit` | - |

### Magical Damage (`damage/magical_damage.py`)

| Opcode | Description | Params (REQUIS) | Params (optionnel) |
|--------|-------------|-----------------|-------------------|
| `magical_damage` | Dégâts magiques standard | `formula`, `can_crit`, `label` | `variance`, `magic_pen_pct`, `flat_magic_pen` |
| `magical_damage_ap_ratio` | Dégâts magiques ratio AP | `base`, `ap_ratio`, `can_crit`, `label` | - |
| `magical_damage_speed_ratio` | Dégâts ratio vitesse + AP | `base`, `speed_ratio`, `ap_ratio`, `can_crit`, `label` | - |

### True Damage (`damage/true_damage.py`)

| Opcode | Description | Params (REQUIS) |
|--------|-------------|-----------------|
| `true_damage` | Dégâts bruts (ignore résistances) | `formula`, `can_crit`, `label` |
| `true_damage_flat` | Dégâts bruts fixes | `amount`, `label` |
| `self_true_damage` | Auto-dégâts | `formula`, `label` |
| `destroy_shield_then_damage` | Détruit bouclier + % PV | `hp_percent`, `label` |

### Percent HP Damage (`damage/percent_hp_damage.py`)

| Opcode | Description | Params (REQUIS) |
|--------|-------------|-----------------|
| `percent_max_hp_damage` | % PV max cible | `percent`, `damage_type`, `can_crit`, `label` |
| `percent_current_hp_damage` | % PV actuels cible | `percent`, `damage_type`, `can_crit`, `label` |
| `percent_missing_hp_damage` | Dégâts + bonus PV manquants | `base`, `ratio`, `ratio_stat`, `missing_hp_ratio`, `damage_type`, `label` |
| `damage_per_burn_stack` | Dégâts par stack brûlure | `percent_per_stack`, `consume_stacks`, `damage_type`, `label` |

### On-Hit Damage (`damage/on_hit_damage.py`)

| Opcode | Description | Params (REQUIS) | Params (optionnel) |
|--------|-------------|-----------------|-------------------|
| `on_hit_damage` | Dégâts on-hit basiques | `base`, `ap_ratio`, `ad_ratio`, `damage_type`, `label` | - |
| `on_hit_crit_conversion` | Conversion crit → on-hit | `conversion_rate`, `label` | - |
| `on_hit_percent_hp` | On-hit % PV max | `percent`, `damage_type`, `label` | `bonus_if_debuff` |
| `on_hit_mr_scaling` | On-hit ratio MR | `mr_ratio`, `label` | - |
| `spellblade_damage` | Effet Spellblade | `type`, `base_ad`, `ratio` | `ap_ratio` (lich_bane), `hp_percent` (divine) |

### Burn Damage (`damage/burn_damage.py`)

| Opcode | Description | Params (REQUIS) |
|--------|-------------|-----------------|
| `apply_burn` | Applique stacks brûlure | `stacks`, `duration` |
| `tick_burn_damage` | Tick des dégâts brûlure | `hp_percent_per_stack`, `ad_ratio_per_stack`, `ap_ratio_per_stack`, `max_hp_ratio_per_stack` |
| `double_burn_stacks` | Double les stacks | `duration` |
| `damage_with_burn` | Dégâts + application brûlure | `base`, `ap_ratio`, `ad_ratio`, `burn_stacks`, `burn_duration`, `label` |

### Execute Damage (`damage/execute_damage.py`)

| Opcode | Description | Params (REQUIS) |
|--------|-------------|-----------------|
| `execute_damage` | Dégâts augmentés vs low HP | `base`, `ratio`, `ratio_stat`, `max_bonus`, `damage_type`, `label` |
| `kill_threshold` | Exécution si sous seuil | `threshold` |

### Multi-Hit Damage (`damage/multi_hit.py`)

| Opcode | Description | Params (REQUIS) |
|--------|-------------|-----------------|
| `multi_basic_attack` | Plusieurs attaques | `hits`, `ad_ratio`, `can_crit` |
| `multi_hit_spell` | Sort multi-projectiles | `hits`, `base_per_hit`, `ratio_per_hit`, `ratio_stat`, `damage_type`, `label` |

### Indirect Damage (`damage/indirect_damage.py`)

| Opcode | Description | Params (REQUIS) |
|--------|-------------|-----------------|
| `reflect_damage` | Renvoie % dégâts | `percent`, `damage_received` |
| `explosion_damage` | Explosion (Sunfire) | `base`, `armor_ratio`, `bonus_hp_ratio`, `damage_type`, `base_hp` |
| `drain_damage` | Dégâts + soin | `base`, `ap_ratio`, `label` |

### Adaptive Damage (`damage/adaptive_damage.py`)

| Opcode | Description | Params (REQUIS) |
|--------|-------------|-----------------|
| `adaptive_damage` | Dégâts adaptatifs AD/AP | `base`, `adaptive_ratio`, `can_crit`, `label` |
| `adaptive_damage_scaling` | Adaptatifs avec scaling | `base`, `adaptive_ratio`, `scale_per_debuff`, `scale_per_buff`, `label` |

---

## 2. Healing Opcodes

### Basic Heal (`healing/basic_heal.py`)

| Opcode | Description | Params (REQUIS) |
|--------|-------------|-----------------|
| `heal` | Soin avec formule | `formula`, `label` |
| `heal_flat` | Soin fixe | `amount`, `label` |
| `heal_percent_max_hp` | Soin % PV max | `percent`, `label` |
| `heal_percent_missing_hp` | Soin % PV manquants | `percent`, `label` |
| `self_heal` | Auto-soin | `formula`, `label` |

### Lifesteal (`healing/lifesteal.py`)

| Opcode | Description | Params (REQUIS) |
|--------|-------------|-----------------|
| `lifesteal` | Vol de vie (physique) | `damage_dealt`, `lifesteal_percent` |
| `omnivamp` | Vol de vie (tous types) | `damage_dealt`, `omnivamp_percent`, `is_aoe` |
| `spellvamp` | Vol de vie (sorts) | `damage_dealt`, `spellvamp_percent` |

### Regen (`healing/regen.py`)

| Opcode | Description | Params (REQUIS) |
|--------|-------------|-----------------|
| `apply_regen` | Applique régénération | `duration`, `stacks` |
| `tick_regen` | Tick de régénération | `hp_percent_per_stack`, `ap_ratio_per_stack` |
| `hp_per_turn` | Soin fixe/tour | `amount` |

### Special Heals (`healing/special_heals.py`)

| Opcode | Description | Params (REQUIS) |
|--------|-------------|-----------------|
| `revive` | Ressuscite cible | `hp_percent` |
| `heal_on_kill` | Soin au kill | `percent` |
| `meditation_heal` | Soin Méditation | `hp_percent_per_stack`, `ap_ratio_per_stack` |

---

## 3. Shield Opcodes

### Basic Shields (`shields/basic_shield.py`)

| Opcode | Description | Params (REQUIS) | Params (optionnel) |
|--------|-------------|-----------------|-------------------|
| `shield` | Bouclier formule | `formula` | - |
| `shield_flat` | Bouclier fixe | `amount` | - |
| `shield_percent_hp` | Bouclier % PV max | `percent` | `use_target_hp` |
| `self_shield` | Bouclier sur soi | `formula` | - |
| `shield_ap_scaling` | Bouclier ratio AP | `base`, `ap_ratio` | - |
| `shield_ad_scaling` | Bouclier ratio AD | `base`, `ad_ratio` | - |

### Special Shields (`shields/special_shields.py`)

| Opcode | Description | Params (REQUIS) |
|--------|-------------|-----------------|
| `maw_shield` | Maw of Malmortius (anti-magie) | `base`, `ad_ratio`, `base_ad` |
| `sterak_shield` | Sterak's Gage | `percent`, `base_hp` |
| `gargoyle_shield` | Gargoyle Stoneplate | `base`, `hp_ratio`, `base_hp` |
| `destroy_shield` | Détruit boucliers | - |
| `shield_decay` | Diminue boucliers | `decay_percent` |

---

## 4. Status Effects Opcodes

### Buffs (`status_effects/buffs.py`)

| Opcode | Description | Params (REQUIS) |
|--------|-------------|-----------------|
| `apply_buff` | Buff générique | `buff_code`, `duration`, `stacks` |
| `apply_puissance` | +10% dégâts/stack | `duration`, `stacks` |
| `apply_haste` | +vitesse | `duration`, `stacks` |
| `apply_rythme` | +4 vitesse/stack | `duration`, `stacks` |
| `apply_mur` | +8% armor/MR | `duration`, `stacks` |
| `apply_impact` | Bonus AP prochain sort | `duration`, `stacks` |
| `apply_focus` | +15% crit | `duration`, `stacks` |
| `apply_concentration` | Ignore résistances partiel | `duration`, `stacks` |
| `apply_volonte` | -20% dégâts reçus | `duration`, `stacks` |
| `apply_voile` | Bloque prochain sort | `duration` |
| `apply_regeneration` | Régénération | `duration`, `stacks` |
| `apply_meditation` | Méditation (soin/tour) | `duration`, `stacks` |

### Debuffs (`status_effects/debuffs.py`)

| Opcode | Description | Params (REQUIS) |
|--------|-------------|-----------------|
| `apply_debuff` | Debuff générique | `debuff_code`, `duration`, `stacks` |
| `apply_burn` | Brûlure (DoT) | `duration`, `stacks` |
| `apply_laceration` | Lacération (DoT physique) | `duration`, `stacks` |
| `apply_fatigue` | -vitesse | `duration`, `stacks` |
| `apply_slow` | Ralentissement | `duration`, `stacks` |
| `apply_vulnerability` | +dégâts reçus | `duration`, `stacks` |
| `apply_antiheal` | Réduit soins | `duration`, `stacks` |
| `apply_armor_reduction` | Réduction armure | `duration`, `stacks` |
| `apply_mr_reduction` | Réduction MR | `duration`, `stacks` |
| `apply_glancing_glow` | -25% dégâts AA | `duration`, `stacks` |
| `apply_critiquable` | +20% dégâts crit reçus | `duration`, `stacks` |
| `apply_exposed` | Dégâts bonus prochaine attaque | `duration`, `stacks` |

### Crowd Control (`status_effects/crowd_control.py`)

| Opcode | Description | Params (REQUIS) |
|--------|-------------|-----------------|
| `apply_stun` | Étourdissement | `duration`, `chance` |
| `apply_silence` | Silence | `duration`, `chance` |
| `apply_root` | Immobilisation | `duration`, `chance` |
| `apply_fear` | Peur | `duration`, `chance` |
| `apply_taunt` | Provocation | `duration` |
| `apply_charm` | Charme | `duration`, `chance` |
| `apply_sleep` | Sommeil | `duration` |
| `apply_airborne` | Projection en air | `duration` |

### Status Management (`status_effects/status_management.py`)

| Opcode | Description | Params (REQUIS) |
|--------|-------------|-----------------|
| `remove_status` | Retire un statut | `status_code` |
| `cleanse_debuffs` | Retire tous debuffs | - |
| `cleanse_buffs` | Retire tous buffs (dispel) | - |
| `extend_status_duration` | Prolonge durée | `status_code`, `extra_turns` |
| `add_status_stacks` | Ajoute stacks | `status_code`, `stacks` |
| `reduce_status_stacks` | Réduit stacks | `status_code`, `stacks` |
| `transfer_status` | Transfère statut | `status_code` |

---

## 5. Stat Modifiers Opcodes

### Flat Modifiers (`stat_modifiers/flat_modifiers.py`)

| Opcode | Description | Params (REQUIS) |
|--------|-------------|-----------------|
| `modify_stat` | Modifie stat flat | `stat`, `amount` |
| `modify_ad` | Modifie AD | `amount` |
| `modify_ap` | Modifie AP | `amount` |
| `modify_armor` | Modifie Armor | `amount` |
| `modify_mr` | Modifie MR | `amount` |
| `modify_speed` | Modifie vitesse | `amount` |
| `modify_max_hp` | Modifie PV max | `amount` |
| `modify_crit_chance` | Modifie crit chance | `amount` |
| `modify_crit_damage` | Modifie crit damage | `amount` |

### Percent Modifiers (`stat_modifiers/percent_modifiers.py`)

| Opcode | Description | Params (REQUIS) |
|--------|-------------|-----------------|
| `modify_stat_percent` | Modifie stat en % | `stat`, `percent` |
| `modify_ad_percent` | Modifie AD % | `percent` |
| `modify_ap_percent` | Modifie AP % | `percent` |
| `modify_armor_percent` | Modifie Armor % | `percent` |
| `modify_mr_percent` | Modifie MR % | `percent` |
| `modify_resistances_percent` | Modifie Armor+MR % | `percent` |
| `reduce_armor_percent` | Réduit Armor % | `percent` |
| `reduce_mr_percent` | Réduit MR % | `percent` |

### Stat Scaling (`stat_modifiers/stat_scaling.py`)

| Opcode | Description | Params (REQUIS) |
|--------|-------------|-----------------|
| `damage_bonus_from_max_hp` | Bonus dégâts % PV max | `ratio` |
| `damage_bonus_from_missing_hp` | Bonus dégâts % PV manquants | `ratio` |
| `damage_bonus_from_armor` | Bonus dégâts % Armor | `ratio` |
| `damage_bonus_from_bonus_hp` | Bonus dégâts HP bonus | `ratio`, `base_hp` |
| `scale_with_stacks` | Scaling par stack | `status_code`, `amount_per_stack` |

---

## 6. Gauge Opcodes

### Echo Gauge (`gauge/echo_gauge.py`)

| Opcode | Description | Params (REQUIS) |
|--------|-------------|-----------------|
| `build_echo` | Génère Echo | `amount`, `max` |
| `consume_echo` | Consomme Echo | `cost` |
| `echo_scaling_damage` | Dégâts scaling Echo | `base`, `ratio`, `ratio_stat`, `echo_scaling`, `damage_type` |
| `reset_echo` | Reset Echo à 0 | - |
| `echo_bonus_effect` | Effet bonus si Echo | `threshold`, `bonus_opcode`, `bonus_params` |

### Charge Gauge (`gauge/charge_gauge.py`)

| Opcode | Description | Params (REQUIS) | Params (optionnel) |
|--------|-------------|-----------------|-------------------|
| `build_charge` | Génère charges | `amount`, `max`, `gauge` | - |
| `consume_charges` | Consomme charges | `gauge` | `amount` ou `all` |
| `check_charges` | Vérifie charges | `required`, `gauge` | - |
| `charge_scaling_effect` | Scaling par charge | `gauge`, `per_charge`, `effect_type` | - |
| `threshold_effect` | Effet seuil atteint | `gauge`, `threshold`, `effect_opcode`, `effect_params` | `consume` |

### Resource Management (`gauge/resource_management.py`)

| Opcode | Description | Params (REQUIS) | Params (optionnel) |
|--------|-------------|-----------------|-------------------|
| `build_gauge` | Build jauge générique | `gauge`, `amount`, `max` | `only_if_target_has_status` |
| `drain_gauge` | Draine jauge | `gauge`, `amount` | - |
| `set_gauge` | Set valeur | `gauge`, `value` | - |
| `transfer_gauge` | Transfère jauge | `gauge` | `amount` ou `all` |
| `gauge_decay` | Décroissance | `gauge`, `decay` | - |

---

## 7. Trigger Opcodes

### On-Hit Triggers (`triggers/on_hit_triggers.py`)

| Opcode | Description | Params (REQUIS) |
|--------|-------------|-----------------|
| `on_basic_attack` | Effets attaque de base | `effects` |
| `on_crit` | Effets critique | `effects` |
| `on_hit_proc` | Proc on-hit % chance | `chance`, `effect_opcode`, `effect_params` |
| `multi_on_hit` | Multi effets on-hit | `on_hit_effects` |
| `bonus_damage_if_target_has_status` | Bonus si statut | `status_code`, `bonus_pct` |

### On-Damage Triggers (`triggers/on_damage_triggers.py`)

| Opcode | Description | Params (REQUIS) | Params (optionnel) |
|--------|-------------|-----------------|-------------------|
| `on_damage_dealt` | Effets dégâts infligés | `damage_dealt`, `effects` | - |
| `on_damage_taken` | Effets dégâts reçus | `damage_taken`, `effects` | - |
| `damage_reflection` | Renvoie dégâts | `damage_taken`, `percent` | - |
| `on_kill` | Effets on-kill | `effects` | - |
| `on_low_hp` | Effets si HP bas | `threshold`, `effects` | `target_self` |

### Conditional Triggers (`triggers/conditional_triggers.py`)

| Opcode | Description | Params (REQUIS) | Params (optionnel) |
|--------|-------------|-----------------|-------------------|
| `conditional_effect` | Effet si condition | `condition`, `effect` | `else_effect` |
| `if_has_status` | Effet si statut | `status_code`, `effect` | `check_self` |
| `if_hp_threshold` | Effet seuil HP | `threshold`, `effect` | `below`, `check_self` |
| `chain_effects` | Chaîne d'effets | `effects` | - |

---

## 8. Cooldown Opcodes

### Cooldown Management (`cooldown/cooldown_management.py`)

| Opcode | Description | Params (REQUIS) | Params (optionnel) |
|--------|-------------|-----------------|-------------------|
| `set_cooldown` | Set cooldown | `ability`, `turns` | - |
| `reduce_cooldown` | Réduit cooldown | `reduction` | `ability` ou `all` |
| `reset_cooldown` | Reset cooldown | - | `ability` ou `all` |
| `check_cooldown` | Vérifie cooldown | `ability` | - |
| `tick_cooldowns` | Tick tous CDs | - | - |
| `cooldown_reduction_percent` | Réduction % | `ability`, `percent` | - |
| `extend_cooldown` | Prolonge CD | `ability`, `turns` | - |

---

## 9. Summon Opcodes

### Summon Management (`summons/summon_management.py`)

| Opcode | Description | Params (REQUIS) | Params (optionnel) |
|--------|-------------|-----------------|-------------------|
| `summon_entity` | Invoque créature | `summon_id`, `name`, `base_hp`, `base_ad`, `base_ap`, `duration` | `hp_ratio`, `ad_ratio`, `ap_ratio` |
| `dismiss_summon` | Renvoie invocation | `summon_id` | - |
| `summon_attack` | Invocation attaque | `summon_id` | - |
| `summon_ability` | Invocation utilise sort | `summon_id`, `damage`, `damage_type`, `ap_ratio` | - |
| `heal_summon` | Soigne invocation | `summon_id`, `amount` | - |

---

## 10. Misc Opcodes

### Utility (`misc/utility.py`)

| Opcode | Description | Params (REQUIS) | Params (optionnel) |
|--------|-------------|-----------------|-------------------|
| `log_message` | Message log | `message` | - |
| `debug_entity` | Debug stats | - | `self` |
| `random_choice` | Effet aléatoire | `choices` | `weights` |
| `repeat_effect` | Répète effet | `times`, `effect` | - |
| `swap_target` | Inverse src/tgt | `effect` | - |
| `no_op` | Rien | - | - |

### Special (`misc/special.py`)

| Opcode | Description | Params (REQUIS) |
|--------|-------------|-----------------|
| `stasis` | Stase (invulnérable) | `duration` |
| `replay_turn` | Rejoue tour | - |
| `resurrect` | Ressuscite | `hp_percent` |
| `copy_last_spell` | Copie dernier sort | - |
| `steal_buff` | Vole un buff | - |
| `swap_hp` | Échange PV | - |
| `execute_if_low` | Execute si hp bas | `threshold` |
| `damage_cap` | Cap dégâts max | `cap_percent`, `duration` |
| `revive_on_death` | Résurrection préparée | `hp_percent`, `duration` |

---

## Usage Example (Item JSON)

```json
{
  "name": "Lame d'Infini",
  "effects": [
    {
      "opcode": "physical_damage_ad_ratio",
      "params": {
        "base": 100,
        "ad_ratio": 0.9,
        "can_crit": true,
        "label": "Lame d'Infini"
      }
    },
    {
      "opcode": "modify_crit_damage",
      "params": {
        "amount": 0.35
      }
    }
  ]
}
```

---

*Generated: 2026-02-01*
