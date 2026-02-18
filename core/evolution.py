
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json
import sqlite3
from core.storage import EngramStorage
from core.abstraction_manager import AbstractionManager
from utils import config

logger = logging.getLogger(__name__)

class EvolutionManager:
    """
    Manages the evolutionary growth of the Engram System.
    Unlocks features (Dream Mode, Implicit Priming, etc.) based on fitness metrics.
    """
    
    def __init__(self):
        self.storage = EngramStorage()
        self.am = AbstractionManager()
        self._ensure_evolution_state()
        
    def _ensure_evolution_state(self):
        """Ensure the evolution state table exists in SQLite"""
        self.storage.conn.execute("""
            CREATE TABLE IF NOT EXISTS system_evolution (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        self.storage.conn.commit()
        
    def get_state(self, key: str, default: Any = None) -> Any:
        cursor = self.storage.conn.execute("SELECT value FROM system_evolution WHERE key = ?", (key,))
        row = cursor.fetchone()
        if row:
            try:
                return json.loads(row[0])
            except:
                return row[0]
        return default

    def set_state(self, key: str, value: Any):
        self.storage.conn.execute("INSERT OR REPLACE INTO system_evolution VALUES (?, ?)", (key, json.dumps(value)))
        self.storage.conn.commit()

    def get_metrics(self) -> Dict[str, Any]:
        """Calculate implementation fitness metrics"""
        # Total Abstractions
        cursor = self.storage.conn.execute("SELECT COUNT(*), AVG(quality_score), AVG(compression_ratio) FROM abstractions")
        count, avg_quality, avg_compression = cursor.fetchone()
        
        # Successful Refinements (approximate for now, using successful_application_count sum)
        cursor = self.storage.conn.execute("SELECT SUM(successful_application_count) FROM abstractions")
        refinements = cursor.fetchone()[0] or 0
        
        # Reuse Contexts
        cursor = self.storage.conn.execute("SELECT SUM(reuse_contexts) FROM abstractions")
        total_reuse = cursor.fetchone()[0] or 0
        
        metrics = {
            "total_abstractions": count,
            "avg_quality": avg_quality or 0.0,
            "avg_compression": avg_compression or 0.0,
            "total_refinements": refinements,
            "total_reuse": total_reuse,
            "dream_insights": self.get_state("dream_insight_count", 0),
            "current_level": self.get_state("evolution_level", 0)
        }
        return metrics

    def check_for_evolution(self) -> str:
        """
        Check if any evolution triggers are met.
        Returns a message if an upgrade is available or applied.
        """
        metrics = self.get_metrics()
        current_level = metrics["current_level"]
        
        logger.info(f"🧬 Evolution Check. Level: {current_level}. Metrics: {metrics}")
        
        # Truth Guard: Don't evolve if memory confidence is too low
        from core.truth_guard import TruthGuard
        top_abs = self._get_top_abstractions()
        risk, is_safe = TruthGuard.calculate_risk(top_abs)
        if not is_safe:
            logger.warning(f"Evolution postponed — memory confidence too low (risk {risk:.2f}).")
            return f"Evolution postponed — memory confidence too low to evolve safely (risk {risk:.2f})."
        
        # Level 1 (Auto): 100+ abstractions, Quality > 0.6
        if current_level < 1:
            if metrics["total_abstractions"] >= 100 and metrics["avg_quality"] > 0.6:
                self.set_state("evolution_level", 1)
                self.set_state("dream_mode_enabled", True)
                self.set_state("implicit_priming_enabled", True)
                msg = "🧬 SYSTEM EVOLUTION: Level 1 Reached! Dream Mode & Implicit Priming ENABLED."
                logger.info(msg)
                return msg

        # Level 2 (Manual): 500+ abstractions OR 50+ dream insights
        if current_level < 2:
            if metrics["total_abstractions"] >= 500 or metrics["dream_insights"] >= 50:
                # Require user permission (simulated here by checking a pending flag)
                # In a real app, we'd notify user and wait. 
                # For this implementation, we'll mark as "PENDING_UPGRADE_2"
                if self.get_state("pending_upgrade") != 2:
                    self.set_state("pending_upgrade", 2)
                    return "🧬 EVOLUTION AVAILABLE: Level 2 (Hierarchical Clustering). Run `/evolve 2` to apply."
        
        # Level 3 (Manual): Avg Quality > 0.85 for 7 days (Simplified: just check avg quality now)
        if current_level < 3:
            if metrics["avg_quality"] > 0.85:
                 if self.get_state("pending_upgrade") != 3:
                    self.set_state("pending_upgrade", 3)
                    return "🧬 EVOLUTION AVAILABLE: Level 3 (Salience Weighting). Run `/evolve 3` to apply."

        return "No evolution changes."

    def apply_upgrade(self, level: int) -> str:
        """Apply a pending manual upgrade"""
        current = self.get_state("evolution_level", 0)
        
        if level <= current:
            return f"Already at or above Level {level}."
            
        if level == 2:
            self.set_state("evolution_level", 2)
            self.set_state("hierarchical_clustering_enabled", True)
            self.set_state("pending_upgrade", None)
            return "🧬 Level 2 Applied: Hierarchical Clustering enabled."
            
        if level == 3:
            self.set_state("evolution_level", 3)
            self.set_state("salience_factor_enabled", True)
            self.set_state("pending_upgrade", None)
            return "🧬 Level 3 Applied: Emotional Salience now impacts memory retention."

        return "Upgrade not implemented."

    def run_dream_mode(self):
        """
        Level 1 Feature: Nightly recombination.
        Picks random high-quality nodes and tries to link them.
        """
        if not self.get_state("dream_mode_enabled"):
            return "Dream Mode disabled."
            
        # 1. Pick 2 random high quality abstractions
        cursor = self.storage.conn.execute("""
            SELECT id, content FROM abstractions 
            WHERE quality_score > 0.7 
            ORDER BY RANDOM() LIMIT 2
        """)
        nodes = cursor.fetchall()
        
        if len(nodes) < 2:
            return "Not enough high-quality memories to dream."
            
        n1, n2 = nodes[0], nodes[1]
        
        logger.info(f"😴 Dreaming: Connecting '{n1[1][:30]}' <-> '{n2[1][:30]}'...")
        
        # In a real system, we'd ask LLM for insight.
        # Here we simulate an insight.
        insight = f"Dream connection between {n1[0][:4]} and {n2[0][:4]}"
        
        # Create meta-abstraction
        from core.graph_manager import GraphManager
        gm = GraphManager()
        
        # Link them
        gm.add_link(n1[0], n2[0], type="dream_association", weight=0.5)
        
        # Update stats
        count = self.get_state("dream_insight_count", 0) + 1
        self.set_state("dream_insight_count", count)
        
        return f"Dreamt of connection between {n1[0]} and {n2[0]}."
    
    def _get_top_abstractions(self) -> List:
        """Helper: Get top 10 abstractions for quality checks"""
        cursor = self.storage.conn.execute("""
            SELECT id FROM abstractions 
            ORDER BY quality_score DESC LIMIT 10
        """)
        rows = cursor.fetchall()
        return [self.storage.get_abstraction(row[0]) for row in rows if self.storage.get_abstraction(row[0])]

