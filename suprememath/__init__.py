"""suprememath — Supreme Mathematics date-reading engine."""

from pathlib import Path

DEFAULT_LEXICON_PATH = Path(__file__).parent.parent / "data" / "sm_lexicon.json"

from .lexicon import Lexicon
from .daily import compute_daily

__all__ = ["Lexicon", "compute_daily", "DEFAULT_LEXICON_PATH"]
