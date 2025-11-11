import os
import logging
import re
from enum import Enum, auto
from typing import Set, Optional

# --- Setup ---
logger = logging.getLogger("interruption-handler")
logger.setLevel(logging.INFO)

# Load default ignored words from environment
DEFAULT_IGNORED_WORDS = os.getenv("IGNORED_WORDS", "uh,umm,hmm,haan").split(",")


# --- Enum for clear return actions ---
class TranscriptionAction(Enum):
    """Defines the possible actions for a processed transcription."""
    IGNORE = auto()
    INTERRUPT = auto()
    REGISTER = auto()


# --- Rewritten Class ---
class InterruptionHandler:
    """
    Filters incoming user speech to decide whether it's a valid interruption
    or just filler/background noise.
    """

    def __init__(
        self,
        min_confidence: float = 0.6,
        ignored_words: Optional[Set[str]] = None,
    ):
        """
        Initializes the handler.

        Args:
            min_confidence: The confidence score below which transcriptions
                            will be ignored as mumbles.
            ignored_words: A set of filler words to ignore. If None,
                           defaults to words from the environment variable.
        """
        self.agent_speaking = False
        self.min_confidence = min_confidence

        # Use the provided set or default to the list from env var
        # Using a set provides much faster lookups (O(1) vs O(n))
        self.ignored_words = ignored_words if ignored_words is not None else set(DEFAULT_IGNORED_WORDS)
        
        logger.info(f"Handler initialized. Min confidence: {self.min_confidence}")
        logger.info(f"Ignored words: {self.ignored_words}")

    async def on_agent_speaking(self, speaking: bool):
        """Updates the handler's state when the agent starts or stops speaking."""
        self.agent_speaking = speaking
        logger.debug(f"Agent speaking state set to: {self.agent_speaking}")

    async def process_transcription(
        self, text: str, confidence: float = 1.0
    ) -> TranscriptionAction:
        """
        Decides whether to ignore, interrupt, or register a transcription.
        """
        # 1. Ignore empty transcriptions
        if not text:
            return TranscriptionAction.IGNORE

        # 2. Ignore low-confidence mumbles
        if confidence < self.min_confidence:
            logger.debug(f"Ignored low confidence ({confidence:.2f}): {text}")
            return TranscriptionAction.IGNORE

        # 3. Parse words robustly
        # Splits by any non-alphabetic character and filters out empty strings.
        # This handles "Wait!", "uh-huh", and "umm..." correctly.
        words = [
            w for w in re.split(r'[^a-zA-Z]+', text.lower()) if w
        ]

        # 4. Ignore if no words were found (e.g., text was just "...")
        if not words:
            logger.debug(f"Ignored empty/punctuation-only text: {text}")
            return TranscriptionAction.IGNORE

        # 5. Main Decision Logic
        if self.agent_speaking:
            # Agent is talking. Check if user speech is just filler.
            is_all_filler = all(w in self.ignored_words for w in words)
            
            if is_all_filler:
                # User said "uh-huh" while agent was talking. Ignore it.
                logger.info(f"Ignored filler during agent speech: {text}")
                return TranscriptionAction.IGNORE
            else:
                # User said "Wait, stop!" while agent was talking. Interrupt.
                logger.info(f"Interrupt detected: {text}")
                return TranscriptionAction.INTERRUPT
        
        # 6. Agent is quiet. Register any valid speech.
        return TranscriptionAction.REGISTER
