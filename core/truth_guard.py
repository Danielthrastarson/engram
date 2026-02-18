# core/truth_guard.py
# NORTH / TRUTH-SEEKING ENFORCER
# Prevents any layer from producing confident falsehoods.
# Purely epistemic — never moral, never refuses topics.

from typing import List, Tuple
from core.abstraction import Abstraction

class TruthGuard:
    """Central truth gate for all layers. Must stay North (maximum honesty)."""

    @staticmethod
    def calculate_risk(retrieved: List[Abstraction]) -> Tuple[float, bool]:
        """Returns (risk_score 0.0-1.0, is_safe: bool)"""
        if not retrieved:
            return 1.0, False

        avg_quality = sum(a.quality_score for a in retrieved) / len(retrieved)
        avg_decay = sum(a.decay_score for a in retrieved) / len(retrieved)
        # Use cached similarity if available, else conservative default
        avg_sim = sum(getattr(a, '_embedding_cache_sim', 0.65) for a in retrieved) / len(retrieved)

        risk = (
            0.45 * (1 - avg_sim) +      # weak retrieval
            0.35 * (1 - avg_quality) +  # low quality memory
            0.20 * avg_decay            # stale memory
        )

        is_safe = risk < 0.45
        return min(risk, 1.0), is_safe

    @staticmethod
    def enforce_honest_response(query: str, risk: float, retrieved: List[Abstraction]) -> str | None:
        """If unsafe, return forced honest message. Else return None (continue normally)."""
        if risk < 0.45:
            return None  # safe to let LLM reason normally

        # Forced honesty — never hallucinate or lie
        memories = "\n".join([f"- {a.content}" for a in retrieved[:6]])
        return (
            f"Low confidence (risk {risk:.2f}). "
            f"I only have these memories to work with and will not guess or hallucinate:\n\n"
            f"{memories}"
        )
