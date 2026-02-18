# reasoning/working_memory.py
# Working Memory: A small, high-priority buffer (~7 items) that persists
# across queries. Based on Miller's Law (7±2 items).
#
# Brain analogy: Prefrontal cortex's active representation buffer.
# Items in working memory are ALWAYS included in reasoning context,
# giving the system persistent focus across conversations.

import time
import logging
from typing import List, Optional, Dict
from dataclasses import dataclass, field
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    """One item in working memory"""
    engram_id: str
    content: str
    relevance: float           # How relevant to current focus (0-1)
    quality: float             # Quality score from engram
    added_at: float = field(default_factory=time.time)
    access_count: int = 1      # How many times recalled
    source_query: str = ""     # What query brought this in
    
    @property
    def priority(self) -> float:
        """Combined priority score for eviction decisions"""
        recency = max(0, 1.0 - (time.time() - self.added_at) / 300)  # 5 min decay
        return (
            self.relevance * 0.4 +
            self.quality * 0.3 +
            recency * 0.2 +
            min(self.access_count / 10, 1.0) * 0.1
        )


class WorkingMemory:
    """
    Fixed-capacity focus buffer (Miller's 7±2).
    
    - Items enter when they score high on relevance + quality
    - Items are evicted FIFO with priority weighting
    - Working memory is ALWAYS prepended to reasoning context
    - Survives across queries (persistent focus)
    """
    
    def __init__(self, capacity: int = 7):
        self.capacity = capacity
        self.items: List[MemoryItem] = []
        
        # Stats
        self.total_insertions = 0
        self.total_evictions = 0
        self.total_accesses = 0
    
    def update(self, query: str, retrieved_engrams: list, 
               min_relevance: float = 0.3) -> List[MemoryItem]:
        """
        Update working memory with newly retrieved engrams.
        
        1. Score each retrieved engram for "focus worthiness"
        2. High quality + high relevance → enters working memory
        3. Low priority items get evicted when full
        
        Returns: list of newly added items
        """
        new_items = []
        
        for engram in retrieved_engrams:
            # Skip if already in working memory
            existing = self._find(engram.id)
            if existing:
                existing.access_count += 1
                existing.relevance = max(existing.relevance, 
                                         getattr(engram, '_rerank_score', 0.5))
                self.total_accesses += 1
                continue
            
            # Calculate relevance from rerank score if available
            rerank = getattr(engram, '_rerank_score', 0.0)
            # Normalize rerank score (cross-encoder logits typically -10 to 10)
            relevance = max(0, min(1.0, (rerank + 5) / 10))
            
            if relevance < min_relevance and engram.quality_score < 0.6:
                continue  # Not worthy of working memory
            
            item = MemoryItem(
                engram_id=engram.id,
                content=engram.content[:200],  # Truncate for memory efficiency
                relevance=relevance,
                quality=engram.quality_score,
                source_query=query,
            )
            
            self._insert(item)
            new_items.append(item)
        
        return new_items
    
    def get_context(self) -> List[str]:
        """
        Get current working memory contents as context strings.
        Always included in reasoning, regardless of retrieval results.
        """
        # Sort by priority (highest first)
        sorted_items = sorted(self.items, key=lambda x: x.priority, reverse=True)
        return [item.content for item in sorted_items]
    
    def get_engram_ids(self) -> List[str]:
        """Get IDs of engrams currently in working memory"""
        return [item.engram_id for item in self.items]
    
    def prime(self, engram_id: str):
        """
        Manually boost an item to high priority.
        Used by /helpful to keep good engrams in focus.
        """
        item = self._find(engram_id)
        if item:
            item.relevance = 1.0
            item.access_count += 3
            item.added_at = time.time()  # Reset recency
            logger.debug(f"Primed working memory item: {engram_id[:8]}")
    
    def clear(self):
        """Clear all working memory (fresh start)"""
        self.items.clear()
    
    def _insert(self, item: MemoryItem):
        """Insert item, evicting lowest priority if full"""
        if len(self.items) >= self.capacity:
            # Evict lowest priority
            lowest = min(self.items, key=lambda x: x.priority)
            self.items.remove(lowest)
            self.total_evictions += 1
            logger.debug(f"WM evicted: {lowest.engram_id[:8]} (priority={lowest.priority:.2f})")
        
        self.items.append(item)
        self.total_insertions += 1
        logger.debug(f"WM added: {item.engram_id[:8]} (relevance={item.relevance:.2f})")
    
    def _find(self, engram_id: str) -> Optional[MemoryItem]:
        """Find item by engram ID"""
        for item in self.items:
            if item.engram_id == engram_id:
                return item
        return None
    
    def get_status(self) -> dict:
        return {
            "capacity": self.capacity,
            "current_size": len(self.items),
            "items": [
                {
                    "id": item.engram_id[:8],
                    "relevance": round(item.relevance, 2),
                    "priority": round(item.priority, 2),
                    "accesses": item.access_count,
                }
                for item in sorted(self.items, key=lambda x: x.priority, reverse=True)
            ],
            "total_insertions": self.total_insertions,
            "total_evictions": self.total_evictions,
        }
