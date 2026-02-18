
import logging
import random
from typing import List
from core.storage import EngramStorage
from core.graph_manager import GraphManager
from core.abstraction import Abstraction
from core.evolution import EvolutionManager

logger = logging.getLogger(__name__)

class Subconscious:
    """
    Handles background cognitive processes like dreaming and implicit priming.
    """
    def __init__(self):
        self.storage = EngramStorage()
        self.gm = GraphManager()
        self.evolution = EvolutionManager()
        
    def dream(self):
        """
        Active Nightly Consolidation WITH LLM INSIGHTS (Phase 14).
        - Identifies disconnected high-quality nodes.
        - Uses Ollama to generate bridging concept.
        - Creates 'Dream' associations to spark innovation.
        """
        if not self.evolution.get_state("dream_mode_enabled"):
            logger.info("😴 Dream Mode: Disabled (Evolution Level too low).")
            return

        logger.info("😴 Dream Mode: Active. Scanning for creative associations...")
        
        # Import LLM client
        try:
            from integration.ollama_client import OllamaClient
            llm = OllamaClient()
        except:
            logger.warning("Ollama not available. Using simple dream mode.")
            llm = None
        
        # Get high salience nodes
        cursor = self.storage.conn.execute("""
            SELECT id, content FROM abstractions 
            WHERE quality_score > 0.6 
            ORDER BY RANDOM() LIMIT 5
        """)
        candidates = cursor.fetchall()
        
        if len(candidates) < 2:
            return
            
        # Pick two
        a = candidates[0]
        b = candidates[1]
        
        # LLM-powered insight
        if llm:
            insight = llm.connect_concepts(a[1], b[1])
            if insight:
                logger.info(f"✨ Dream Insight: {insight}")
                
                # Enforce truth even in subconscious creation
                from core.truth_guard import TruthGuard
                abs1 = self.storage.get_abstraction(a[0])
                abs2 = self.storage.get_abstraction(b[0])
                risk, is_safe = TruthGuard.calculate_risk([abs1, abs2])
                if not is_safe:
                    insight = f"[DREAM INSIGHT — LOW CONFIDENCE] {insight}"
                
                # Create meta-abstraction from insight
                from core.abstraction_manager import AbstractionManager
                am = AbstractionManager()
                meta_abs, created = am.create_abstraction(
                    content=f"DREAM INSIGHT: {insight}",
                    metadata={"source": "dream", "type": "creative_connection"}
                )
                
                if created:
                    # Link A → Meta ← B
                    self.gm.add_link(a[0], meta_abs.id, type="implies_dream", weight=0.6)
                    self.gm.add_link(b[0], meta_abs.id, type="implies_dream", weight=0.6)
                    logger.info(f"💡 Created meta-abstraction: {meta_abs.id[:8]}")
            else:
                # Fallback: simple link
                logger.info(f"✨ Simple Dream: Connecting '{a[1][:20]}...' <-> '{b[1][:20]}...'")
                self.gm.add_link(a[0], b[0], type="dreamt_association", weight=0.3)
        else:
            # No LLM: simple link
            logger.info(f"✨ Simple Dream: Connecting '{a[1][:20]}...' <-> '{b[1][:20]}...'")
            self.gm.add_link(a[0], b[0], type="dreamt_association", weight=0.3)
        
        # Increment dream stats
        count = self.evolution.get_state("dream_insight_count", 0) + 1
        self.evolution.set_state("dream_insight_count", count)

    def implicit_priming(self, active_cluster_id: str):
        """
        Boosts activation of all nodes in the active cluster.
        This simulates 'spreading activation'.
        """
        if not self.evolution.get_state("implicit_priming_enabled"):
            return

        # Boost metrics for everything in this cluster slightly
        # This increases their retention chance
        logger.info(f"🌊 Implicit Priming: Boosting Cluster {active_cluster_id}")
        
        self.storage.conn.execute("""
            UPDATE abstractions 
            SET successful_application_count = successful_application_count + 1 
            WHERE cluster_id = ?
        """, (active_cluster_id,))
        self.storage.conn.commit()
