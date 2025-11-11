import os
import logging

logger = logging.getLogger("interruption-handler")
logger.setLevel(logging.INFO)

FILTER_LIST = os.getenv("IGNORED_WORDS", "uh,umm,hmm,haan").split(",")

class SpeechHandler:

    def __init__(self):
        self.is_agent_speaking = False

    async def set_agent_speaking(self, speaking: bool):
        self.is_agent_speaking = speaking
        logger.debug(f"Agent speaking = {self.is_agent_speaking}")

    async def process_input(self, text: str, confidence: float = 1.0):
        if not text:
            return "ignore"

        clean_text = text.lower().strip()
        tokens = [w for w in clean_text.split() if w.isalpha()]

        if confidence < 0.6:
            logger.debug("Ignored low confidence")
            return "ignore"

        if self.is_agent_speaking and all(w in FILTER_LIST for w in tokens):
            logger.info(f"Ignored filler during agent speech: {text}")
            return "ignore"

        if self.is_agent_speaking and any(w not in FILTER_LIST for w in tokens):
            logger.info(f"Interrupt detected: {text}")
            return "interrupt"

        return "register"
