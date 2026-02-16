import logging
import math
from datetime import datetime
from typing import List, Dict
from core.storage import EngramStorage
from core.abstraction import Abstraction
from utils import config

logger = logging.getLogger(__name__)

class DecaySystem:
    def __init__(self):
        self.storage = EngramStorage()

    def calculate_decay(self, abstraction: Abstraction) -> float:
        """
        Calculate current decay score (0.0=fresh, 1.0=fully decayed).
        """
        time_since_use = datetime.now() - abstraction.last_used
        days_unused = time_since_use.total_seconds() / 86400.0 # days
        
        # Exponential decay: 1 - e^(-rate * days)
        decay_rate = config.DECAY_RATE_DAILY
        raw_decay = 1.0 - math.exp(-decay_rate * days_unused)
        
        # Modifiers (Protection)
        
        # 1. High Reuse Protection
        if abstraction.reuse_contexts > 5:
            raw_decay *= 0.5 # Halve decay speed
            
        # 2. High Accuracy Protection
        if abstraction.accuracy_preserved >= config.PROTECT_ACCURACY_THRESHOLD:
            raw_decay *= 0.7 # 30% slower
            
        return min(raw_decay, 1.0)

    def run_decay_cycle(self):
        """
        Update decay scores for ALL abstractions and prune if necessary.
        """
        # 1. Get all abstractions (iterative in prod, all-at-once for V1)
        cursor = self.storage.conn.execute("SELECT id FROM abstractions")
        all_ids = [row[0] for row in cursor.fetchall()]
        
        pruned_count = 0
        updated_count = 0
        
        # Cache cluster counts for Rule 0 (Orphan Protection)
        cluster_counts = self._get_cluster_counts()
        
        for abs_id in all_ids:
            abs_obj = self.storage.get_abstraction(abs_id)
            if not abs_obj:
                continue
                
            # Update Score
            new_decay = self.calculate_decay(abs_obj)
            abs_obj.decay_score = new_decay
            
            # Check Pruning
            if self._should_prune(abs_obj, cluster_counts):
                self._prune(abs_obj)
                pruned_count += 1
                # Update cluster count cache decrement
                if abs_obj.cluster_id:
                    cluster_counts[abs_obj.cluster_id] = cluster_counts.get(abs_obj.cluster_id, 1) - 1
            else:
                self.storage.update_metrics(abs_obj)
                updated_count += 1
                
        logger.info(f"Decay cycle complete. Updated {updated_count}, Pruned {pruned_count}.")

    def _get_cluster_counts(self) -> Dict[str, int]:
        """Get count of items in each cluster for Rule 0"""
        cursor = self.storage.conn.execute(
            "SELECT cluster_id, COUNT(*) FROM abstractions GROUP BY cluster_id"
        )
        return {row[0]: row[1] for row in cursor.fetchall() if row[0]}

    def _should_prune(self, abs_obj: Abstraction, cluster_counts: Dict[str, int]) -> bool:
        """Apply Pruning Rules"""
        
        # Rule 0: High Priority - Orphan Protection
        # If it's the last item in a cluster, KEEP IT.
        if abs_obj.cluster_id and cluster_counts.get(abs_obj.cluster_id, 0) <= 1:
            return False
            
        # Rule 1: Fast Decay for unused low-quality
        if abs_obj.decay_score > 0.8 and abs_obj.usage_count < 2:
            return True
            
        # Rule 2: Hard limit
        if abs_obj.decay_score > config.PRUNE_THRESHOLD + 0.5: # e.g., > 0.9
            return True
        
        # Rule 3: Quality Threshold
        # If quality drops below threshold due to decay
        # (calculated outside this func, but let's check decay part)
        # Note: Quality formula includes decay, but we can check raw decay too.
        
        return False

    def _prune(self, abs_obj: Abstraction):
        """Delete from DBs"""
        logger.info(f"Pruning abstraction {abs_obj.id} (Decay: {abs_obj.decay_score:.2f})")
        
        # 1. Delete from Chroma
        self.storage.collection.delete(ids=[abs_obj.id])
        
        # 2. Delete from SQLite
        self.storage.conn.execute("DELETE FROM abstractions WHERE id = ?", (abs_obj.id,))
        self.storage.conn.commit()
