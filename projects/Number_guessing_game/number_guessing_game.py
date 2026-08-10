"""
Number Guessing Game – refactored (modular + logging + error handling).

Improvements over the original ``main.py``
------------------------------------------
* Logic moved into a ``NumberGuessingGame`` controller class.
* Uses Python ``logging`` instead of bare ``print()`` for informational and
  diagnostic messages (user-facing prompts still use ``print()``).
* Input validation wrapped in a ``parse_guess`` helper that handles
  :exc:`ValueError` so invalid entries never crash the game.
* ``max_attempts`` guard prevents infinite loops.
* ``main()`` entry-point wires everything and calls ``game.run()``.
"""

import logging
import random
import sys
from typing import Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def parse_guess(raw: str) -> Optional[int]:
    """Parse a raw user-input string into an integer.

    Parameters
    ----------
    raw:
        The string entered by the user.

    Returns
    -------
    An ``int`` on success, or ``None`` if the input is not a valid integer.
    """
    try:
        return int(raw.strip())
    except ValueError:
        logger.warning("Non-integer input received: %r", raw)
        return None


def generate_secret(low: int = 1, high: int = 9) -> int:
    """Return a random integer in the closed interval [*low*, *high*].

    Parameters
    ----------
    low:
        Lower bound (inclusive).  Defaults to 1.
    high:
        Upper bound (inclusive).  Defaults to 9.

    Returns
    -------
    A random integer.
    """
    secret = random.randint(low, high)
    logger.debug("Secret number generated: %d (range %d–%d)", secret, low, high)
    return secret


# ---------------------------------------------------------------------------
# Controller class
# ---------------------------------------------------------------------------


class NumberGuessingGame:
    """Orchestrates a single round of the number guessing game.

    Parameters
    ----------
    low:
        Lower bound of the number range.  Defaults to 1.
    high:
        Upper bound of the number range.  Defaults to 9.
    max_attempts:
        Maximum number of guesses before the game ends.  Defaults to 5.
    """

    def __init__(self, low: int = 1, high: int = 9, max_attempts: int = 5) -> None:
        self.low = low
        self.high = high
        self.max_attempts = max_attempts
        self._secret: Optional[int] = None
        self._attempts: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Initialise a new round by generating the secret number."""
        self._secret = generate_secret(self.low, self.high)
        self._attempts = 0
        logger.info("Game started. Allowed attempts: %d", self.max_attempts)

    def handle_guess(self, guess: int) -> str:
        """Evaluate a single guess and return a feedback string.

        Parameters
        ----------
        guess:
            The integer guessed by the player.

        Returns
        -------
        One of ``"correct"``, ``"too_low"``, or ``"too_high"``.

        Raises
        ------
        RuntimeError
            If :meth:`start` has not been called before this method.
        """
        if self._secret is None:
            raise RuntimeError("Game not started – call start() first.")

        self._attempts += 1
        logger.debug(
            "Attempt %d/%d: guess=%d, secret=%d",
            self._attempts,
            self.max_attempts,
            guess,
            self._secret,
        )

        if guess == self._secret:
            logger.info("Correct guess in %d attempt(s).", self._attempts)
            return "correct"
        if guess < self._secret:
            return "too_low"
        return "too_high"

    @property
    def attempts_remaining(self) -> int:
        """Number of guesses still available."""
        return self.max_attempts - self._attempts

    @property
    def attempts_used(self) -> int:
        """Number of guesses made so far."""
        return self._attempts

    def run(self) -> None:
        """Run the interactive game loop until win or attempts exhausted."""
        self.start()
        print(f"Number Guessing Game")
        print(f"Guess a number between {self.low} and {self.high}.")
        print(f"You have {self.max_attempts} attempts.\n")

        while self.attempts_remaining > 0:
            raw = input("Your guess: ")
            guess = parse_guess(raw)

            if guess is None:
                print("  Please enter a valid integer.")
                continue

            result = self.handle_guess(guess)

            if result == "correct":
                print(
                    f"\nCONGRATULATIONS! You guessed {self._secret} "
                    f"in {self.attempts_used} attempt(s)!"
                )
                return

            if result == "too_low":
                print(
                    f"  Too low. "
                    f"({self.attempts_remaining} attempt(s) remaining)"
                )
            else:
                print(
                    f"  Too high. "
                    f"({self.attempts_remaining} attempt(s) remaining)"
                )

        print(
            f"\nGame over. The number was {self._secret}. Better luck next time!"
        )
        logger.info("Game ended without correct guess. Secret was %d.", self._secret)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Configure logging and start the game."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        stream=sys.stderr,
    )
    logger.info("Number Guessing Game initialising.")
    game = NumberGuessingGame(low=1, high=9, max_attempts=5)
    game.run()


if __name__ == "__main__":
    main()
