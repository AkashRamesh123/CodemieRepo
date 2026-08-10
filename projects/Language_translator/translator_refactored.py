"""
Language Translator – refactored (modular + logging + error handling).

Improvements over the original ``translator.py``
-------------------------------------------------
* Logic split into small, named functions (``list_languages``,
  ``select_language``, ``translate_text``).
* ``TranslatorController`` class orchestrates the session loop.
* Uses Python ``logging`` instead of bare ``print()`` for diagnostics.
* Translation wrapped in structured ``try/except`` so network failures or
  API errors do not crash the application.
* ``main()`` entry-point sets up logging and runs the controller.
"""

import logging
import sys
from typing import Optional

from googletrans import Translator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Supported languages
# ---------------------------------------------------------------------------

LANGUAGES: dict[str, str] = {
    "bn": "Bangla",
    "en": "English",
    "ko": "Korean",
    "fr": "French",
    "de": "German",
    "he": "Hebrew",
    "hi": "Hindi",
    "it": "Italian",
    "ja": "Japanese",
    "la": "Latin",
    "ms": "Malay",
    "ne": "Nepali",
    "ru": "Russian",
    "ar": "Arabic",
    "zh": "Chinese",
    "es": "Spanish",
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def list_languages(languages: dict[str, str]) -> None:
    """Print a formatted table of available language codes and names.

    Parameters
    ----------
    languages:
        Mapping of ISO 639-1 code to language name.
    """
    print("\nCode  : Language")
    print("-" * 20)
    for code, name in languages.items():
        print(f"  {code}   : {name}")
    print()


def select_language(languages: dict[str, str]) -> Optional[str]:
    """Prompt the user to choose a target language and return its code.

    The user is given unlimited attempts.  Entering ``"options"`` displays
    the full language list.  An empty input exits the selection.

    Parameters
    ----------
    languages:
        Mapping of ISO 639-1 code to language name.

    Returns
    -------
    A valid language code string, or ``None`` if the user exits without
    selecting.
    """
    while True:
        raw = input(
            "Enter a language code (or 'options' to list, blank to exit): "
        ).strip().lower()

        if not raw:
            logger.info("User exited language selection.")
            return None

        if raw == "options":
            list_languages(languages)
            continue

        if raw in languages:
            logger.info("Language selected: %s (%s)", raw, languages[raw])
            print(f"Selected: {languages[raw]}\n")
            return raw

        logger.warning("Invalid language code entered: %r", raw)
        print(f"  '{raw}' is not a recognised language code.")


def translate_text(
    translator: Translator,
    text: str,
    dest_code: str,
    languages: dict[str, str],
) -> None:
    """Translate *text* to *dest_code* and print the result.

    Parameters
    ----------
    translator:
        An initialised :class:`googletrans.Translator` instance.
    text:
        The string to translate.
    dest_code:
        ISO 639-1 code of the target language.
    languages:
        Mapping of ISO 639-1 code to language name (for display).
    """
    try:
        result = translator.translate(text, dest=dest_code)
        dest_name = languages.get(dest_code, dest_code)
        src_name = languages.get(result.src, result.src)

        print(f"\n{dest_name} translation: {result.text}")
        if result.pronunciation:
            print(f"Pronunciation       : {result.pronunciation}")
        print(f"Translated from     : {src_name}\n")
        logger.debug(
            "Translated %r to %s (%r)", text[:40], dest_code, result.text[:40]
        )
    except AttributeError as exc:
        logger.error("Translation result missing expected attribute: %s", exc)
        print("  Translation failed – unexpected API response.")
    except Exception:
        logger.exception("Unexpected error during translation.")
        print("  Translation failed – please try again.")


# ---------------------------------------------------------------------------
# Controller class
# ---------------------------------------------------------------------------


class TranslatorController:
    """Orchestrate the translation session.

    Parameters
    ----------
    languages:
        Mapping of ISO 639-1 code to language name.  Defaults to
        :data:`LANGUAGES`.
    """

    def __init__(self, languages: dict[str, str] = LANGUAGES) -> None:
        self._languages = languages
        self._translator = Translator()

    def start(self) -> None:
        """Initialise the translator instance."""
        logger.info("TranslatorController started.")

    def run(self) -> None:
        """Run the interactive translation session."""
        self.start()
        dest_code = select_language(self._languages)
        if dest_code is None:
            logger.info("No language selected – exiting.")
            return

        print("Type the text to translate, or 'close' to exit.\n")
        while True:
            raw = input("Text: ").strip()
            if raw.lower() == "close":
                print("Have a nice day!")
                logger.info("User closed the translation session.")
                break
            if not raw:
                print("  Please enter some text.")
                continue

            translate_text(self._translator, raw, dest_code, self._languages)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Configure logging and run the translator controller."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        stream=sys.stderr,
    )
    logger.info("Language Translator application starting.")
    controller = TranslatorController()
    controller.run()


if __name__ == "__main__":
    main()
