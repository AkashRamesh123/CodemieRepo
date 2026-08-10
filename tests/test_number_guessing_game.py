"""Unit tests for the refactored Number Guessing Game module."""

import sys
import os

# Allow importing from the projects directory
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "projects", "Number_guessing_game"),
)

import pytest
from number_guessing_game import (
    NumberGuessingGame,
    parse_guess,
    generate_secret,
)


# ---------------------------------------------------------------------------
# parse_guess
# ---------------------------------------------------------------------------

class TestParseGuess:
    def test_valid_integer_string(self):
        assert parse_guess("5") == 5

    def test_valid_integer_with_whitespace(self):
        assert parse_guess("  3  ") == 3

    def test_non_integer_returns_none(self):
        assert parse_guess("abc") is None

    def test_float_string_returns_none(self):
        assert parse_guess("3.5") is None

    def test_empty_string_returns_none(self):
        assert parse_guess("") is None


# ---------------------------------------------------------------------------
# generate_secret
# ---------------------------------------------------------------------------

class TestGenerateSecret:
    def test_value_within_range(self):
        for _ in range(50):
            value = generate_secret(1, 9)
            assert 1 <= value <= 9

    def test_custom_range(self):
        for _ in range(50):
            value = generate_secret(10, 20)
            assert 10 <= value <= 20


# ---------------------------------------------------------------------------
# NumberGuessingGame
# ---------------------------------------------------------------------------

class TestNumberGuessingGame:
    def _game_with_secret(self, secret: int) -> NumberGuessingGame:
        game = NumberGuessingGame(low=1, high=9, max_attempts=5)
        game.start()
        game._secret = secret  # Override for deterministic testing
        game._attempts = 0
        return game

    def test_correct_guess_returns_correct(self):
        game = self._game_with_secret(5)
        assert game.handle_guess(5) == "correct"

    def test_low_guess_returns_too_low(self):
        game = self._game_with_secret(5)
        assert game.handle_guess(3) == "too_low"

    def test_high_guess_returns_too_high(self):
        game = self._game_with_secret(5)
        assert game.handle_guess(8) == "too_high"

    def test_attempts_increment(self):
        game = self._game_with_secret(5)
        assert game.attempts_used == 0
        game.handle_guess(3)
        assert game.attempts_used == 1
        game.handle_guess(4)
        assert game.attempts_used == 2

    def test_attempts_remaining_decrements(self):
        game = self._game_with_secret(5)
        initial = game.attempts_remaining
        game.handle_guess(1)
        assert game.attempts_remaining == initial - 1

    def test_start_before_guess_required(self):
        game = NumberGuessingGame()
        with pytest.raises(RuntimeError):
            game.handle_guess(5)
