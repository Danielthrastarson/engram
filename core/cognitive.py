import logging
import time
import random
from typing import List, Optional
from core.abstraction_manager import AbstractionManager
from integration.llm_interface import LLMInterface
from core.storage import EngramStorage
from utils import config
from utils.metrics import MetricsTracker

logger = logging.getLogger(__name__)

class CognitiveLoop:
    def __init__(self):
        self.manager = AbstractionManager()
        self.llm = LLMInterface()
        self.storage = EngramStorage()
        self.running = False
        self.metrics = MetricsTracker()

    def start(self):
        """Start the background cognitive loop"""
        if not config.ENABLE_COGNITIVE_LOOP:
            logger.info("Cognitive Loop disabled in config.")
            return

        self.running = True
        logger.info("🧠 Cognitive Loop Started")
        
        while self.running:
            try:
                self.step()
                time.sleep(config.COGNITIVE_LOOP_INTERVAL_SEC)
            except KeyboardInterrupt:
                self.stop()
            except Exception as e:
                logger.error(f"Cognitive Loop Error: {e}")
                time.sleep(60) # Backoff

    def stop(self):
        self.running = False
        logger.info("Cognitive Loop Stopped")

    def step(self):
        """Perform one refinement cycle"""
        logger.info("Cognitive Loop: Scanning for weak abstractions...")

        # 1. Select Weak Abstractions (Low Quality / High Uncertainty)
        candidates = self._find_weak_abstractions(limit=config.MAX_REFINEMENTS_PER_RUN)
        
        if not candidates:
            logger.info("Cognitive Loop: No weak abstractions found. System is stable.")
            return

        # 2. Refine Each
        for abs_obj in candidates:
            logger.info(f"Refining abstraction {abs_obj.id} (Quality: {abs_obj.quality_score:.2f})")
            
            # 3. Generate Improved Content
            improved_content = self.llm.refine_abstraction(abs_obj.content)
            
            if improved_content and improved_content != abs_obj.content:
                # Truth Guard self-check
                from core.truth_guard import TruthGuard
                risk, is_safe = TruthGuard.calculate_risk([abs_obj])  # self-check
                if not is_safe:
                    improved_content = f"[REFINED WITH LOW CONFIDENCE] {improved_content}"
                
                # 4. Update
                old_len = len(abs_obj.content)
                self.manager.update_abstraction(abs_obj.id, content=improved_content)
                new_len = len(improved_content)
                
                # Track Metric
                self.metrics.track_refinement(abs_obj.id, old_len, new_len)
                
                logger.info(f" -> Refined to: {improved_content[:50]}...")
            else:
                logger.info(" -> No improvement generated.")

    def _find_weak_abstractions(self, limit: int) -> List:
        """Find abstractions with low quality score"""
        candidates = []
        try:
            cursor = self.storage.conn.execute(
                "SELECT id FROM abstractions WHERE quality_score < ? ORDER BY quality_score ASC LIMIT ?",
                (config.UNCERTAINTY_THRESHOLD, limit)
            )
            rows = cursor.fetchall()
            for row in rows:
                candidates.append(self.storage.get_abstraction(row[0]))
        except Exception as e:
            logger.error(f"Failed to query weak abstractions: {e}")
            
        return candidates
