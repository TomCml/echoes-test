"""
GameBalance — Configuration centralisée des paramètres d'équilibrage du jeu.

Toutes les valeurs sont overridables via variables d'environnement avec le préfixe GAME_.
Exemple : GAME_BASE_XP=250 dans .env

Usage :
    from app.config.game_balance import get_balance
    balance = get_balance()
    gold = balance.GOLD_BY_CATEGORY[monster_category]
"""
from functools import lru_cache
from typing import Dict

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GameBalance(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GAME_", env_file=".env", extra="ignore")

    # ─── Gold par catégorie de monstre ───────────────────
    GOLD_CAT_1: int = 50
    GOLD_CAT_2: int = 150
    GOLD_CAT_3: int = 350
    GOLD_CAT_4: int = 1000

    # ─── XP de base ──────────────────────────────────────
    BASE_XP: int = 100
    MIN_XP_REWARD: int = 1

    # ─── Poids des raretés de coffres (doivent sommer à 100) ─
    CHEST_RARITY_W1: float = 50.0   # Common
    CHEST_RARITY_W2: float = 30.0   # Uncommon
    CHEST_RARITY_W3: float = 14.0   # Rare
    CHEST_RARITY_W4: float = 5.0    # Epic
    CHEST_RARITY_W5: float = 1.0    # Legendary

    # ─── Multiplicateurs de stats par rareté d'instance ──
    RARITY_MULT_1: float = 1.0      # Common   (baseline)
    RARITY_MULT_2: float = 1.15     # Uncommon
    RARITY_MULT_3: float = 1.35     # Rare
    RARITY_MULT_4: float = 1.60     # Epic
    RARITY_MULT_5: float = 2.00     # Legendary

    # ─── Multiplicateurs de difficulté de donjon ─────────
    DUNGEON_DIFF_1: float = 1.0
    DUNGEON_DIFF_2: float = 1.25
    DUNGEON_DIFF_3: float = 1.60
    DUNGEON_DIFF_4: float = 2.00
    DUNGEON_DIFF_5: float = 2.50

    # ─── Jauge Echo ───────────────────────────────────────
    ECHO_GAUGE_MAX: int = 100
    ECHO_BASE_GAIN: int = 10

    # ─── Tuning combat ───────────────────────────────────
    CRIT_DAMAGE_MULTIPLIER: float = 1.5
    MIN_DAMAGE: int = 1

    # ─── Coffres ─────────────────────────────────────────
    CHESTS_PER_VICTORY: int = 1
    BOSS_BONUS_CHESTS: int = 1

    # ─── Validators ──────────────────────────────────────

    @field_validator("CHEST_RARITY_W1", "CHEST_RARITY_W2", "CHEST_RARITY_W3",
                     "CHEST_RARITY_W4", "CHEST_RARITY_W5", mode="before")
    @classmethod
    def validate_chest_weights(cls, v: float) -> float:
        if float(v) < 0:
            raise ValueError("Les poids de rareté ne peuvent pas être négatifs")
        return v

    @field_validator("RARITY_MULT_1", "RARITY_MULT_2", "RARITY_MULT_3",
                     "RARITY_MULT_4", "RARITY_MULT_5", mode="before")
    @classmethod
    def validate_rarity_multipliers(cls, v: float) -> float:
        if float(v) <= 0:
            raise ValueError("Les multiplicateurs de rareté doivent être > 0")
        return v

    # ─── Properties ──────────────────────────────────────

    @property
    def GOLD_BY_CATEGORY(self) -> Dict[int, int]:
        return {1: self.GOLD_CAT_1, 2: self.GOLD_CAT_2,
                3: self.GOLD_CAT_3, 4: self.GOLD_CAT_4}

    @property
    def CHEST_RARITY_WEIGHTS(self) -> Dict[int, float]:
        return {1: self.CHEST_RARITY_W1, 2: self.CHEST_RARITY_W2,
                3: self.CHEST_RARITY_W3, 4: self.CHEST_RARITY_W4,
                5: self.CHEST_RARITY_W5}

    @property
    def RARITY_STAT_MULTIPLIERS(self) -> Dict[int, float]:
        return {1: self.RARITY_MULT_1, 2: self.RARITY_MULT_2, 3: self.RARITY_MULT_3,
                4: self.RARITY_MULT_4, 5: self.RARITY_MULT_5}

    @property
    def DUNGEON_DIFFICULTY_MULTIPLIERS(self) -> Dict[int, float]:
        return {1: self.DUNGEON_DIFF_1, 2: self.DUNGEON_DIFF_2, 3: self.DUNGEON_DIFF_3,
                4: self.DUNGEON_DIFF_4, 5: self.DUNGEON_DIFF_5}


@lru_cache(maxsize=1)
def get_balance() -> GameBalance:
    """Singleton GameBalance — chargé une fois, réutilisé partout."""
    return GameBalance()
