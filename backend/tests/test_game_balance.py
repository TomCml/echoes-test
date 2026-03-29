"""
Tests for GameBalance configuration.

Vérifie :
  - Les valeurs par défaut sont cohérentes avec le GDD
  - Les properties retournent les bons dicts
  - Les validators rejettent les valeurs invalides
  - Le cache singleton fonctionne
  - Les overrides .env sont pris en compte
"""

import os
import pytest
from app.config.game_balance import GameBalance, get_balance


class TestGameBalanceDefaults:
    """Vérifie que les défauts matchent le Game Design Document."""

    def setup_method(self):
        self.balance = GameBalance()

    def test_gold_by_category(self):
        assert self.balance.GOLD_BY_CATEGORY == {
            1: 50, 2: 150, 3: 350, 4: 1000,
        }

    def test_chest_rarity_weights_sum(self):
        total = sum(self.balance.CHEST_RARITY_WEIGHTS.values())
        assert total == 100.0, f"Chest weights should sum to 100%, got {total}%"

    def test_rarity_multipliers_ascending(self):
        mults = self.balance.RARITY_STAT_MULTIPLIERS
        for i in range(1, 5):
            assert mults[i] < mults[i + 1], (
                f"Rarity {i} mult ({mults[i]}) should be < rarity {i+1} ({mults[i+1]})"
            )

    def test_rarity_common_is_baseline(self):
        assert self.balance.RARITY_STAT_MULTIPLIERS[1] == 1.0

    def test_dungeon_difficulty_ascending(self):
        diffs = self.balance.DUNGEON_DIFFICULTY_MULTIPLIERS
        for i in range(1, 5):
            assert diffs[i] < diffs[i + 1]

    def test_base_xp_positive(self):
        assert self.balance.BASE_XP > 0

    def test_echo_gauge_defaults(self):
        assert self.balance.ECHO_GAUGE_MAX == 100
        assert self.balance.ECHO_BASE_GAIN == 10

    def test_combat_tuning_defaults(self):
        assert self.balance.CRIT_DAMAGE_MULTIPLIER == 1.5
        assert self.balance.MIN_DAMAGE == 1
        assert self.balance.MIN_XP_REWARD == 1

    def test_chest_config(self):
        assert self.balance.CHESTS_PER_VICTORY == 1
        assert self.balance.BOSS_BONUS_CHESTS == 1


class TestGameBalanceValidators:
    """Vérifie que les validators rejettent les valeurs invalides."""

    def test_negative_chest_weight_rejected(self):
        with pytest.raises(ValueError, match="rareté"):
            GameBalance(CHEST_RARITY_W1=-1.0)

    def test_zero_rarity_multiplier_rejected(self):
        with pytest.raises(ValueError, match="multiplicateurs"):
            GameBalance(RARITY_MULT_3=0.0)

    def test_negative_rarity_multiplier_rejected(self):
        with pytest.raises(ValueError, match="multiplicateurs"):
            GameBalance(RARITY_MULT_2=-0.5)


class TestGameBalanceSingleton:
    """Vérifie le comportement du singleton."""

    def test_get_balance_returns_same_instance(self):
        get_balance.cache_clear()
        a = get_balance()
        b = get_balance()
        assert a is b

    def test_cache_clear_allows_new_instance(self):
        get_balance.cache_clear()
        a = get_balance()
        get_balance.cache_clear()
        b = get_balance()
        # Même valeurs mais instances différentes
        assert a is not b
        assert a.BASE_XP == b.BASE_XP


class TestGameBalanceEnvOverride:
    """Vérifie que les variables .env sont prises en compte."""

    def test_env_override_base_xp(self, monkeypatch):
        monkeypatch.setenv("GAME_BASE_XP", "250")
        balance = GameBalance()
        assert balance.BASE_XP == 250

    def test_env_override_gold_cat(self, monkeypatch):
        monkeypatch.setenv("GAME_GOLD_CAT_3", "500")
        balance = GameBalance()
        assert balance.GOLD_BY_CATEGORY[3] == 500
        # Les autres catégories gardent leurs défauts
        assert balance.GOLD_BY_CATEGORY[1] == 50

    def test_env_override_rarity_mult(self, monkeypatch):
        monkeypatch.setenv("GAME_RARITY_MULT_5", "3.0")
        balance = GameBalance()
        assert balance.RARITY_STAT_MULTIPLIERS[5] == 3.0

    def test_env_override_chest_weight(self, monkeypatch):
        monkeypatch.setenv("GAME_CHEST_RARITY_W5", "2.0")
        balance = GameBalance()
        assert balance.CHEST_RARITY_WEIGHTS[5] == 2.0
