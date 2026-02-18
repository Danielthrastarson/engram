import logging
from typing import List
from core.abstraction_manager import AbstractionManager
from integration.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

class SalienceDetector:
    """
    Automatic salience detection using LLM (Phase 14).
    Rates emotional importance during ingestion.
    """
    def __init__(self):
        self.llm = OllamaClient()
        
    def detect(self, content: str) -> float:
        """
        Rate content salience (0.5 to 2.0).
        Falls back to 1.0 if LLM unavailable.
        """
        try:
            salience = self.llm.rate_salience(content)
            logger.info(f"Salience detected: {salience:.2f} for '{content[:30]}...'")
            return salience
        except Exception as e:
            logger.warning(f"Salience detection failed: {e}")
            return 1.0

class QueryExpander:
    """
    Expands user queries with synonyms/rephrasings (Phase 14).
    Improves recall by searching multiple variants.
    """
    def __init__(self):
        self.llm = OllamaClient()
        
    def expand(self, query: str) -> List[str]:
        """Generate 3 alternative query phrasings"""
        try:
            variants = self.llm.expand_query(query)
            logger.info(f"Query expanded: {len(variants)} variants")
            return variants
        except Exception as e:
            logger.warning(f"Query expansion failed: {e}")
            return [query]
