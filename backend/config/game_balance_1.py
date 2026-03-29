"""
Game Balance Configuration — Constantes centralisées pour l'équilibrage.

Utilise pydantic-settings pour charger depuis .env avec des valeurs par défaut.
Singleton thread-safe via lru_cache.

Usage :
    from app.config.game_balance import get_balance
    balance = get_balance()
    gold = balance.GOLD_BY_CATEGORY[mob_category]
"""

from functools import lru_cache
from typing import Dict

from pydantic import field_validator
from pydantic_settings import BaseSettings


class GameBalance(BaseSettings):
    """
    Toutes les variables d'équilibrage du jeu.

    Chaque variable est configurable via .env (préfixe GAME_).
    Les dicts ne peuvent pas être passés directement via .env,
    ils sont donc construits à partir de champs scalaires.
    """

    model_config = {"env_prefix": "GAME_"}

    # ─── XP ──────────────────────────────────────────

    BASE_XP: int = 100
    """XP de base accordée par un mob de même niveau que le joueur."""

    BASE_XP_LEVEL_100: int = 5000
    """XP de base pour les mobs de donjon (niveau 100+)."""

    XP_PENALTY_DIVISOR: float = 100.0
    """Diviseur pour le malus XP : penalty = (hero_lvl - mob_lvl) / divisor."""

    # ─── Gold par catégorie de monstre ───────────────

    GOLD_CAT_1: int = 50
    GOLD_CAT_2: int = 150
    GOLD_CAT_3: int = 350
    GOLD_CAT_4: int = 1000

    GOLD_SCALING_PER_LEVEL: float = 0.07
    """Multiplicateur linéaire : gold = base * (1 + scaling * mob_level)."""

    GOLD_BONUS_PER_RARITY: int = 100
    """Bonus gold quand un coffre tombe sur __GOLD_BONUS__ (par point de rareté)."""

    @property
    def GOLD_BY_CATEGORY(self) -> Dict[int, int]:
        """Mapping catégorie → gold de base."""
        return {
            1: self.GOLD_CAT_1,
            2: self.GOLD_CAT_2,
            3: self.GOLD_CAT_3,
            4: self.GOLD_CAT_4,
        }

    # ─── Rareté des coffres (Gacha step 1) ───────────

    CHEST_RARITY_W1: float = 50.0
    CHEST_RARITY_W2: float = 28.0
    CHEST_RARITY_W3: float = 15.4
    CHEST_RARITY_W4: float = 6.0
    CHEST_RARITY_W5: float = 0.6

    @property
    def CHEST_RARITY_WEIGHTS(self) -> Dict[int, float]:
        """Probabilités pondérées pour le roll de rareté du coffre."""
        return {
            1: self.CHEST_RARITY_W1,
            2: self.CHEST_RARITY_W2,
            3: self.CHEST_RARITY_W3,
            4: self.CHEST_RARITY_W4,
            5: self.CHEST_RARITY_W5,
        }

    # ─── Multiplicateurs de stats par rareté ─────────

    RARITY_MULT_1: float = 1.0     # Commun
    RARITY_MULT_2: float = 1.15    # Peu commun  (+15%)
    RARITY_MULT_3: float = 1.35    # Rare         (+35%)
    RARITY_MULT_4: float = 1.60    # Épique       (+60%)
    RARITY_MULT_5: float = 2.00    # Légendaire  (+100%)

    @property
    def RARITY_STAT_MULTIPLIERS(self) -> Dict[int, float]:
        """Multiplicateur appliqué aux stats de base d'un item selon sa rareté d'instance."""
        return {
            1: self.RARITY_MULT_1,
            2: self.RARITY_MULT_2,
            3: self.RARITY_MULT_3,
            4: self.RARITY_MULT_4,
            5: self.RARITY_MULT_5,
        }

    # ─── Multiplicateurs de difficulté des donjons ───

    DUNGEON_DIFF_1: float = 1.0
    DUNGEON_DIFF_2: float = 1.5     # +50% drop rate
    DUNGEON_DIFF_3: float = 2.0     # +100% drop rate
    DUNGEON_DIFF_4: float = 3.0     # +200% drop rate
    DUNGEON_DIFF_5: float = 5.0     # +400% drop rate

    @property
    def DUNGEON_DIFFICULTY_MULTIPLIERS(self) -> Dict[int, float]:
        """Multiplicateur sur le drop rate de base selon la difficulté du donjon."""
        return {
            1: self.DUNGEON_DIFF_1,
            2: self.DUNGEON_DIFF_2,
            3: self.DUNGEON_DIFF_3,
            4: self.DUNGEON_DIFF_4,
            5: self.DUNGEON_DIFF_5,
        }

    # ─── Coffres : quantité par victoire ─────────────

    CHESTS_PER_VICTORY: int = 1
    """Nombre de coffres standard par victoire."""

    BOSS_BONUS_CHESTS: int = 1
    """Coffres bonus supplémentaires pour un boss."""

    # ─── Echo Gauge (combat) ─────────────────────────

    ECHO_GAUGE_MAX: int = 100
    """Valeur maximum de la jauge Echo."""

    ECHO_BASE_GAIN: int = 10
    """Gain d'Echo de base par action offensive."""

    # ─── Combat tuning ───────────────────────────────

    CRIT_DAMAGE_MULTIPLIER: float = 1.5
    """Multiplicateur de dégâts critiques par défaut."""

    MIN_DAMAGE: int = 1
    """Dégâts minimum par coup (floor)."""

    MIN_XP_REWARD: int = 1
    """XP minimum accordée même avec un malus maximal."""

    # ─── Validators ──────────────────────────────────

    @field_validator(
        "CHEST_RARITY_W1", "CHEST_RARITY_W2", "CHEST_RARITY_W3",
        "CHEST_RARITY_W4", "CHEST_RARITY_W5",
    )
    @classmethod
    def weights_must_be_positive(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Les poids de rareté doivent être >= 0")
        return v

    @field_validator(
        "RARITY_MULT_1", "RARITY_MULT_2", "RARITY_MULT_3",
        "RARITY_MULT_4", "RARITY_MULT_5",
    )
    @classmethod
    def multipliers_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Les multiplicateurs de rareté doivent être > 0")
        return v


# ─── Singleton accessor ─────────────────────────────────

@lru_cache(maxsize=1)
def get_balance() -> GameBalance:
    """
    Retourne l'instance unique de GameBalance.

    Chargée une seule fois depuis .env, puis mise en cache.
    Pour les tests, utiliser get_balance.cache_clear() avant
    de patcher les variables d'environnement.
    """
    return GameBalance()
