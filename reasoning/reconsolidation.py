# reasoning/reconsolidation.py
# Change 5: Reconsolidation on Retrieval
# Every recalled memory enters a fragile window where it can be modified
# Based on Nader et al. (2000) — memory reconsolidation theory

import logging
import time
from typing import Dict, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ReconsolidationWindow:
    """A memory in its fragile reconsolidation state"""
    engram_id: str
    query_context: str       # The query that triggered retrieval
    opened_at: float = field(default_factory=time.time)
    window_duration: float = 30.0  # Seconds the window stays open
    modifications: List[str] = field(default_factory=list)
    closed: bool = False
    strengthened: bool = False
    weakened: bool = False
    
    @property
    def is_open(self) -> bool:
        return not self.closed and (time.time() - self.opened_at) < self.window_duration
    
    @property
    def age(self) -> float:
        return time.time() - self.opened_at


class ReconsolidationEngine:
    """
    Memory Reconsolidation: Every recall is an opportunity to modify.
    
    In neuroscience (Nader et al., 2000), every time a memory is recalled,
    it temporarily becomes fragile — entering a 'reconsolidation window'
    lasting ~6 hours. During this window:
    
    - STRENGTHEN: If the recall context matches the original, strengthen it
    - UPDATE: If new information is present, integrate it into the memory
    - WEAKEN: If the recall context is dissonant, weaken the memory
    
    This replaces the old pattern of "find weak engrams in background loop"
    with "improve engrams naturally when they're recalled."
    
    The key insight: refinement should happen AT THE MOMENT OF USE,
    not in a disconnected background thread.
    """
    
    def __init__(self, window_duration: float = 30.0):
        # Active reconsolidation windows
        self.active_windows: Dict[str, ReconsolidationWindow] = {}
        
        # Configuration
        self.window_duration = window_duration
        
        # Stats
        self.total_opened = 0
        self.total_strengthened = 0
        self.total_updated = 0
        self.total_weakened = 0
    
    def open_window(self, engram_id: str, query_context: str) -> ReconsolidationWindow:
        """
        Open a reconsolidation window for a recalled engram.
        Called by the retrieval system every time an engram is returned.
        """
        # If already open, extend it
        if engram_id in self.active_windows:
            existing = self.active_windows[engram_id]
            if existing.is_open:
                return existing
        
        window = ReconsolidationWindow(
            engram_id=engram_id,
            query_context=query_context,
            window_duration=self.window_duration,
        )
        self.active_windows[engram_id] = window
        self.total_opened += 1
        
        logger.debug(f"🔓 Reconsolidation window opened: {engram_id[:8]} "
                      f"(context: {query_context[:40]})")
        
        return window
    
    def evaluate_and_modify(self, engram, query: str, 
                            response_quality: float,
                            prediction_error: float = 0.0) -> Optional[dict]:
        """
        Evaluate an engram during its reconsolidation window and decide
        how to modify it.
        
        Returns a dict of modifications to apply, or None if no changes.
        """
        window = self.active_windows.get(engram.id)
        if not window or not window.is_open:
            return None
        
        modifications = {}
        
        # === STRENGTHEN ===
        # If used successfully with high quality → boost
        if response_quality > 0.7 and prediction_error < 0.3:
            quality_boost = min(0.05, response_quality * 0.02)
            modifications["quality_score"] = min(1.0, engram.quality_score + quality_boost)
            modifications["consistency_score"] = min(1.0, engram.consistency_score + 0.01)
            window.strengthened = True
            self.total_strengthened += 1
            logger.debug(f"  💪 STRENGTHEN: {engram.id[:8]} quality +{quality_boost:.3f}")
        
        # === WEAKEN ===
        # High prediction error when this engram was retrieved → it was misleading
        elif prediction_error > 0.7:
            quality_penalty = min(0.1, prediction_error * 0.05)
            modifications["quality_score"] = max(0.1, engram.quality_score - quality_penalty)
            modifications["decay_score"] = min(1.0, engram.decay_score + 0.05)
            window.weakened = True
            self.total_weakened += 1
            logger.debug(f"  📉 WEAKEN: {engram.id[:8]} quality -{quality_penalty:.3f}")
        
        # === UPDATE ===
        # Moderate prediction error → integrate new context
        elif prediction_error > 0.3:
            # Mark for the Awake Engine to refine with new context
            modifications["_needs_refinement"] = True
            modifications["_refinement_context"] = query
            self.total_updated += 1
            logger.debug(f"  🔄 UPDATE queued: {engram.id[:8]}")
        
        if modifications:
            window.modifications.append(str(modifications))
        
        return modifications if modifications else None
    
    def close_expired_windows(self):
        """Close windows that have exceeded their duration"""
        expired = [
            eid for eid, w in self.active_windows.items()
            if not w.is_open
        ]
        for eid in expired:
            self.active_windows[eid].closed = True
            del self.active_windows[eid]
    
    def get_open_windows(self) -> List[ReconsolidationWindow]:
        """Get all currently open windows"""
        self.close_expired_windows()
        return [w for w in self.active_windows.values() if w.is_open]
    
    def get_stats(self) -> dict:
        self.close_expired_windows()
        return {
            "active_windows": len(self.active_windows),
            "total_opened": self.total_opened,
            "total_strengthened": self.total_strengthened,
            "total_updated": self.total_updated,
            "total_weakened": self.total_weakened,
        }
