# reasoning/query_router.py
# Smart Query Routing: Leverages existing Engram Searcher for fast/slow path decision
# Part of the Hybrid AI: First-Principles Reasoning system

import logging
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class ReasoningMode(Enum):
    """Which engine should handle this query"""
    PATTERN = "pattern"        # Fast path: engram retrieval only
    SYMBOLIC = "symbolic"      # Slow path: first-principles reasoning
    HYBRID = "hybrid"          # Both in parallel, merge results
    CLARIFY = "clarify"        # Input too noisy, ask for clarification


@dataclass
class RoutingDecision:
    """Result of query routing"""
    engine: ReasoningMode = ReasoningMode.PATTERN
    confidence: float = 0.0
    pattern_results: List[Any] = field(default_factory=list)
    message: Optional[str] = None
    escalation_reason: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "engine": self.engine.value,
            "confidence": self.confidence,
            "num_pattern_results": len(self.pattern_results),
            "message": self.message,
            "escalation_reason": self.escalation_reason,
        }


class QueryRouter:
    """
    Smart query routing using the existing Engram Searcher.
    
    Strategy:
    1. Try pattern matching first (fast path via Searcher)
    2. If confidence is high, use pattern results directly
    3. If keywords demand first-principles, route to symbolic
    4. Otherwise, use hybrid (both in parallel)
    """
    
    # Keywords that demand first-principles reasoning
    SYMBOLIC_KEYWORDS = [
        'prove', 'proof', 'derive', 'derivation',
        'why fundamentally', 'from first principles',
        'axiom', 'theorem', 'logically follows',
        'contradict', 'contradiction', 'necessarily',
        'formally verify', 'demonstrate that',
    ]
    
    # Keywords suggesting pattern retrieval is sufficient
    PATTERN_KEYWORDS = [
        'what is', 'who is', 'when was', 'where is',
        'define', 'list', 'example', 'summary',
        'recall', 'remember', 'tell me about',
    ]
    
    def __init__(self, searcher=None, confidence_threshold: float = 0.8):
        self.searcher = searcher
        self.confidence_threshold = confidence_threshold
    
    def route(self, query: str, filtered_confidence: float = 1.0) -> RoutingDecision:
        """
        Route a query to the appropriate reasoning engine.
        
        Args:
            query: The user's query (ideally filtered through Layer 0)
            filtered_confidence: Confidence from Layer 0 translator gate (1.0 if bypassed)
        """
        # Step 1: Check if input needs clarification
        if filtered_confidence < 0.5:
            return RoutingDecision(
                engine=ReasoningMode.CLARIFY,
                confidence=filtered_confidence,
                message="Input too ambiguous - please rephrase your question."
            )
        
        # Step 2: Check for explicit symbolic keywords
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in self.SYMBOLIC_KEYWORDS):
            reason = next(kw for kw in self.SYMBOLIC_KEYWORDS if kw in query_lower)
            return RoutingDecision(
                engine=ReasoningMode.SYMBOLIC,
                confidence=0.9,
                escalation_reason=f"Keyword detected: '{reason}'"
            )
        
        # Step 3: Try pattern matching using existing Searcher
        pattern_results = []
        pattern_confidence = 0.0
        
        if self.searcher:
            try:
                results = self.searcher.search(query, top_k=5)
                if results:
                    pattern_results = results
                    # Use quality score as confidence proxy
                    if hasattr(results[0], 'quality_score'):
                        pattern_confidence = results[0].quality_score
                    elif hasattr(results[0], '_embedding_cache_sim'):
                        pattern_confidence = results[0]._embedding_cache_sim
                    else:
                        pattern_confidence = 0.7  # Default if no score available
            except Exception as e:
                logger.warning(f"Searcher failed during routing: {e}")
        
        # Adjust confidence by input quality
        adjusted_confidence = pattern_confidence * filtered_confidence
        
        # Step 4: Route based on confidence
        if adjusted_confidence >= self.confidence_threshold and pattern_results:
            # High confidence pattern match
            return RoutingDecision(
                engine=ReasoningMode.PATTERN,
                confidence=adjusted_confidence,
                pattern_results=pattern_results,
            )
        
        # Step 5: Check for simple pattern keywords
        if any(kw in query_lower for kw in self.PATTERN_KEYWORDS):
            return RoutingDecision(
                engine=ReasoningMode.PATTERN,
                confidence=max(adjusted_confidence, 0.6),
                pattern_results=pattern_results,
            )
        
        # Step 6: Hybrid for everything else
        return RoutingDecision(
            engine=ReasoningMode.HYBRID,
            confidence=adjusted_confidence,
            pattern_results=pattern_results,
            escalation_reason="Low pattern confidence, using hybrid approach"
        )
    
    def should_think(self, decision: RoutingDecision) -> bool:
        """Should we show a 'thinking...' pause for this query?"""
        return (
            decision.engine in (ReasoningMode.SYMBOLIC, ReasoningMode.HYBRID)
            or decision.confidence < 0.75
        )
