# reasoning/prediction.py
# Change 1: Prediction Error Signal
# The brain's core algorithm: predict → compare → learn from error
# Based on Karl Friston's Free Energy Principle

import logging
import time
import hashlib
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class Prediction:
    """A prediction about what the answer should be"""
    query: str
    predicted_content: str
    predicted_confidence: float
    source: str  # "pattern_cache", "recent_context", "axiom"
    timestamp: float = field(default_factory=time.time)


@dataclass
class PredictionError:
    """The difference between prediction and reality"""
    query: str
    prediction: Prediction
    actual_content: str
    actual_confidence: float
    error_magnitude: float  # 0.0 = perfect prediction, 1.0 = completely wrong
    surprise: float         # How unexpected this was (drives learning priority)
    domain: str = "general"
    
    def to_dict(self) -> dict:
        return {
            "query": self.query[:100],
            "error_magnitude": self.error_magnitude,
            "surprise": self.surprise,
            "predicted_confidence": self.prediction.predicted_confidence,
            "actual_confidence": self.actual_confidence,
            "source": self.prediction.source,
            "domain": self.domain,
        }


class PredictionEngine:
    """
    Generates predictions before processing and computes prediction error after.
    
    This is the brain's core algorithm:
    1. Before processing a query, predict the answer from cached patterns
    2. Process the query through the full pipeline
    3. Compare prediction vs. actual
    4. High error = surprising = LEARN from this
    5. Low error = expected = don't waste resources
    
    The prediction error signal drives:
    - Awake Engine prioritization (high-error queries get more cycles)
    - Memory consolidation priority (surprising events consolidate faster)
    - Seeking Drive activation (what domains have high prediction error?)
    """
    
    def __init__(self):
        # Recent query→response cache for rapid prediction
        self._pattern_cache: Dict[str, str] = {}
        self._cache_max = 500
        
        # Recent prediction errors (drives learning)
        self.error_history: deque = deque(maxlen=200)
        
        # Domain error tracking (which domains surprise us most?)
        self.domain_errors: Dict[str, List[float]] = {}
        
        # Stats
        self.total_predictions = 0
        self.total_surprises = 0  # error > 0.5
        self.avg_error = 0.0
    
    def predict(self, query: str, context_engrams: list = None) -> Prediction:
        """
        Generate a prediction BEFORE processing the query.
        Uses cached patterns and context similarity.
        """
        self.total_predictions += 1
        
        # Strategy 1: Exact/near match in pattern cache
        cache_key = self._cache_key(query)
        if cache_key in self._pattern_cache:
            return Prediction(
                query=query,
                predicted_content=self._pattern_cache[cache_key],
                predicted_confidence=0.8,
                source="pattern_cache",
            )
        
        # Strategy 2: Use context engrams if available
        if context_engrams:
            # Predict from highest-quality engram's content
            best = max(context_engrams, key=lambda e: e.quality_score)
            return Prediction(
                query=query,
                predicted_content=best.content,
                predicted_confidence=best.quality_score * 0.7,
                source="context_engram",
            )
        
        # Strategy 3: No prediction possible (novel input)
        return Prediction(
            query=query,
            predicted_content="",
            predicted_confidence=0.0,
            source="no_prediction",
        )
    
    def compute_error(self, prediction: Prediction, 
                      actual_content: str, 
                      actual_confidence: float,
                      domain: str = "general") -> PredictionError:
        """
        Compare prediction to actual result.
        Returns a PredictionError with surprise magnitude.
        """
        # Compute content similarity
        if not prediction.predicted_content or not actual_content:
            content_error = 1.0 if actual_content else 0.0
        else:
            similarity = self._text_similarity(
                prediction.predicted_content, actual_content
            )
            content_error = 1.0 - similarity
        
        # Compute confidence error
        confidence_error = abs(prediction.predicted_confidence - actual_confidence)
        
        # Combined error magnitude
        error_magnitude = content_error * 0.7 + confidence_error * 0.3
        
        # Surprise = error weighted by how confident the prediction was
        # High confidence + high error = VERY surprising
        # Low confidence + high error = expected (we knew we didn't know)
        surprise = error_magnitude * (0.3 + 0.7 * prediction.predicted_confidence)
        
        error = PredictionError(
            query=prediction.query,
            prediction=prediction,
            actual_content=actual_content,
            actual_confidence=actual_confidence,
            error_magnitude=error_magnitude,
            surprise=surprise,
            domain=domain,
        )
        
        # Track
        self.error_history.append(error)
        self._track_domain_error(domain, error_magnitude)
        
        # Update running average
        self.avg_error = self.avg_error * 0.95 + error_magnitude * 0.05
        
        if surprise > 0.5:
            self.total_surprises += 1
            logger.info(f"⚡ HIGH SURPRISE: error={error_magnitude:.2f}, "
                        f"surprise={surprise:.2f}, domain={domain}")
        
        # Cache this query→response for future predictions
        cache_key = self._cache_key(prediction.query)
        self._update_cache(cache_key, actual_content)
        
        return error
    
    def get_surprising_domains(self, top_k: int = 3) -> List[tuple]:
        """Get domains with highest average prediction error"""
        domain_avgs = []
        for domain, errors in self.domain_errors.items():
            if len(errors) >= 3:  # Need enough samples
                avg = sum(errors[-20:]) / len(errors[-20:])
                domain_avgs.append((domain, avg))
        
        domain_avgs.sort(key=lambda x: x[1], reverse=True)
        return domain_avgs[:top_k]
    
    def get_recent_surprises(self, min_surprise: float = 0.5) -> List[PredictionError]:
        """Get recent high-surprise events for directed dreaming"""
        return [e for e in self.error_history if e.surprise >= min_surprise]
    
    def get_stats(self) -> dict:
        return {
            "total_predictions": self.total_predictions,
            "total_surprises": self.total_surprises,
            "avg_error": self.avg_error,
            "cache_size": len(self._pattern_cache),
            "surprising_domains": self.get_surprising_domains(),
        }
    
    # === Internal ===
    
    def _cache_key(self, query: str) -> str:
        """Normalize query for cache lookup"""
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()[:16]
    
    def _update_cache(self, key: str, content: str):
        if len(self._pattern_cache) >= self._cache_max:
            # Evict oldest (FIFO)
            oldest = next(iter(self._pattern_cache))
            del self._pattern_cache[oldest]
        self._pattern_cache[key] = content
    
    def _track_domain_error(self, domain: str, error: float):
        if domain not in self.domain_errors:
            self.domain_errors[domain] = []
        self.domain_errors[domain].append(error)
        # Keep last 50 per domain
        if len(self.domain_errors[domain]) > 50:
            self.domain_errors[domain] = self.domain_errors[domain][-50:]
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Jaccard word-overlap similarity"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union)
