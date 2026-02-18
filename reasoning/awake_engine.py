# reasoning/awake_engine.py  
# Awake Engine: Dynamic 1-60 Hz cognitive loop
# Replaces static refinement cycle with a living, breathing cognitive engine

import asyncio
import logging
import time
import random
import threading
from typing import List, Optional
from typing import List, Optional
from enum import Enum
from core.abstraction_manager import AbstractionManager
from core.abstraction import Abstraction
from integration.llm_interface import LLMInterface
from core.storage import EngramStorage
from core.truth_guard import TruthGuard
from reasoning.bridge import SemanticBridge
from reasoning.axiom_store import AxiomStore
from reasoning.symbolic_reasoning import ReasoningEngine
from utils import config
from utils.metrics import MetricsTracker

logger = logging.getLogger(__name__)


class EngineMode(Enum):
    """Awake Engine operating modes"""
    IDLE = "idle"           # 1 Hz - background consistency checks
    THINKING = "thinking"   # 10-30 Hz - active refinement
    FOCUSED = "focused"     # 60 Hz - deep first-principles reasoning
    DREAMING = "dreaming"   # 5-10 Hz - internal organization (Low Battery)
    SLEEPING = "sleeping"   # 0 Hz - paused


class AwakeEngine:
    """
    Dynamic 1-60 Hz cognitive loop that feels alive.
    
    Modes:
    - IDLE (1 Hz): Background scanning
    - THINKING (10-30 Hz): Active refinement
    - FOCUSED (60 Hz): Deep reasoning
    - DREAMING (10 Hz): Internal graph optimization (No LLM)
    - SLEEPING (0 Hz): Paused
    """
    


    def _step(self):
        """Execute one cognitive cycle based on current mode"""
        self.cycle_count += 1
        
        # Check Energy Level for Dreaming Trigger
        # Market updates allocation, but does it pass energy level? 
        # No, we need to read it.
        # self.market is avail.
        if self.market and self.market.energy_level < 20.0:
             if self.mode != EngineMode.DREAMING:
                 logger.info(f"🌙 Energy Low ({self.market.energy_level:.1f}%). Entering DREAM STATE.")
                 self.mode = EngineMode.DREAMING
        elif self.mode == EngineMode.DREAMING and self.market and self.market.energy_level > 80.0:
             logger.info(f"☀ Energy Restored ({self.market.energy_level:.1f}%). Waking up.")
             self.mode = EngineMode.IDLE

        if self.mode == EngineMode.IDLE:
            self._idle_scan()
        elif self.mode == EngineMode.THINKING:
            self._think()
        elif self.mode == EngineMode.FOCUSED:
            self._focused_reasoning()
        elif self.mode == EngineMode.DREAMING:
            self._dream()
        
        # Adjust Hz after each step
        self._adjust_hz()
    
    def __init__(self):
        self.manager = AbstractionManager()
        self.llm = LLMInterface()
        self.storage = EngramStorage()
        self.bridge = SemanticBridge(llm=self.llm)
        self.axiom_store = AxiomStore()
        self.reasoning = ReasoningEngine(llm=self.llm, axiom_store=self.axiom_store)
        self.metrics = MetricsTracker()
        
        # Economy
        self.market = None
        self.allocation = {"amount": 0.0} # Current resources
        
        # Engine state
        self.mode = EngineMode.SLEEPING
        self.running = False
        
        # RPM control (Allocated by market)
        self.current_hz = 0.5 
        self.min_hz = 0.5
        self.max_hz = 60.0
        
        # Work queue
        self.workload_queue: List[Abstraction] = []
        
        # Stats
        self.cycle_count = 0
        self.proofs_generated = 0
        self.refinements_made = 0
        self.consistency_checks = 0
        self.mode_switches = 0
        self.last_mode_change = time.time()
        
        # Thresholds
        self.consistency_threshold = 0.8
        self.escalation_threshold = 0.6
        self.escalation_cooldown = 30.0
    
        # Thread safety
        self._lock = threading.Lock()
    
    def set_market(self, market):
        """Connect to the Internal Economy"""
        self.market = market
        self.market.register_agent("awake_engine", initial_credits=100.0)
        
    def construct_bid(self) -> dict:
        """Called by Heartbeat to get this agent's bid"""
        with self._lock:
            # Calculate Urgency
            queue_size = len(self.workload_queue)
            # Avoid division by zero
            avg_quality = sum(a.quality_score for a in self.workload_queue) / max(1, queue_size)
        
        # Base bid (Background maintenance)
        value = 1.0
        amount = 10.0 
        exclusive = False
        
        # --- Deadlock Prevention: Bailout Grant ---
        # If queue is massive, we can't afford to bid high enough with just UBI.
        # We need a Bailout Grant.
        if queue_size > 50:
            # Cost estimate: 10cr per item?
            needed = queue_size * 5.0
            utility = needed * 2.0 # High utility to clear backlog
            self.market.submit_proposal("awake_engine", needed, utility, "Workload Bailout")
            # We still bid, but we might lose this tick until grant arrives
            # But grant arrives at START of tick?
            # If we submit now (during collect_bids), it gets processed in run_auction (processed grants).
            # So we get money THIS tick.
            value = needed / 60.0 # Per RPM price
            amount = 60.0
            exclusive = True
            
        elif queue_size > 0:
            value += queue_size * 0.5
            amount = 30.0
            
        if avg_quality < 0.5 and queue_size > 0: # Urgent fix needed
            value += 10.0
            amount = 60.0
            exclusive = True # Request Power Lease
        
        # Cap bid at conservative estimate if no grant requested?
        # No, if we requested grant, we expect money.
        
        return {
            "agent_id": "awake_engine",
            "resource": "POWER_LEASE" if exclusive else "COMPUTE_RPM",
            "amount": amount,
            "value": value,
            "exclusive": exclusive
        }
        
    def receive_allocation(self, allocation: dict):
        """Called by Heartbeat when auction is won (or lost)"""
        self.allocation = allocation
        if allocation and allocation.get("amount", 0) > 0:
            self.current_hz = allocation["amount"]
            if allocation.get("resource") == "POWER_LEASE":
                self.mode = EngineMode.FOCUSED
            elif self.current_hz >= 10:
                self.mode = EngineMode.THINKING
            else:
                self.mode = EngineMode.IDLE
        else:
            self.current_hz = 0.5 # Minimum heartbeat
            self.mode = EngineMode.IDLE
    
    def start(self):
        """Start the Awake Engine (synchronous wrapper)"""
        if not config.ENABLE_COGNITIVE_LOOP:
            logger.info("Awake Engine disabled in config.")
            return
        
        self.running = True
        logger.info("🧠 Awake Engine: Online (Market-Driven)")
        
        while self.running:
            try:
                # Do work based on current allocation
                if self.allocation.get("amount", 0) > 0:
                    self._step()
                
                # Sleep based on allocated Hz (or default slow loop if no allocation)
                sleep_time = 1.0 / max(self.current_hz, 0.1)
                time.sleep(sleep_time)
                
            except KeyboardInterrupt:
                self.stop()
            except Exception as e:
                logger.error(f"Awake loop error: {e}")
                time.sleep(1)
    
    def stop(self):
        """Stop the Awake Engine"""
        self.mode = EngineMode.SLEEPING
        self.running = False
        logger.info(f"🧠 Awake Engine: Shutting down. Stats: "
                     f"{self.cycle_count} cycles, {self.proofs_generated} proofs, "
                     f"{self.refinements_made} refinements")
    

    
    # === Mode Implementations ===
    
    def _idle_scan(self):
        """IDLE: Background scan for weak/inconsistent engrams"""
        candidates = self._find_weak_abstractions(limit=3)
        
        if candidates:
            logger.info(f"💭 Awake [IDLE]: Found {len(candidates)} weak engrams")
            with self._lock:
                self.workload_queue.extend(candidates)
            self._switch_mode(EngineMode.THINKING)
        
        # --- The Reaper: Cleanup old junk ---
        # Every 10th check
        if self.consistency_checks % 10 == 0:
            with self._lock:
                # Remove items older than 1 hour (3600s) if quality < 0.5
                now = time.time()
                initial_len = len(self.workload_queue)
                # Filter in place
                self.workload_queue = [
                    a for a in self.workload_queue 
                    if (now - a.created_at.timestamp()) < 3600 or a.quality_score > 0.5
                ]
                removed = initial_len - len(self.workload_queue)
                if removed > 0:
                    logger.info(f"💀 The Reaper removed {removed} stale items from queue")

        self.consistency_checks += 1
    
    def _think(self):
        """THINKING: Active refinement of queued items"""
        abs_obj = None
        with self._lock:
            if not self.workload_queue:
                self._switch_mode(EngineMode.IDLE)
                return
            
            # --- Starvation Avoidance: Sort by Urgency ---
            # Urgency = Quality (0-1) + AgeFactor (0.1 per minute)
            # This ensures old items eventually float to top
            now = time.time()
            self.workload_queue.sort(
                key=lambda x: x.quality_score + ((now - x.created_at.timestamp()) / 600.0),
                reverse=True
            )
            
            # Get next item
            abs_obj = self.workload_queue.pop(0)
        
        # Check if this needs escalation to focused mode
        if abs_obj.consistency_score < self.escalation_threshold:
            # High-priority item → escalate
            with self._lock:
                self.workload_queue.insert(0, abs_obj)
            self._switch_mode(EngineMode.FOCUSED)
            return
        
        # Standard LLM refinement (same as original cognitive loop)
        logger.info(f"🤔 Awake [THINKING]: Refining {abs_obj.id[:8]}... "
                     f"(quality={abs_obj.quality_score:.2f}, "
                     f"consistency={abs_obj.consistency_score:.2f})")
        
        improved_content = self.llm.refine_abstraction(abs_obj.content)
        
        if improved_content and improved_content != abs_obj.content:
            # Truth Guard check
            risk, is_safe = TruthGuard.calculate_risk([abs_obj])
            
            if not is_safe:
                improved_content = f"[REFINED WITH LOW CONFIDENCE] {improved_content}"
            
            # Update
            old_len = len(abs_obj.content)
            self.manager.update_abstraction(abs_obj.id, content=improved_content)
            new_len = len(improved_content)
            self.metrics.track_refinement(abs_obj.id, old_len, new_len)
            self.refinements_made += 1
            
            logger.info(f"  → Refined successfully ({old_len} → {new_len} chars)")
        else:
            logger.info(f"  → No improvement needed")
    
    def _focused_reasoning(self):
        """FOCUSED: Deep first-principles reasoning"""
        abs_obj = None
        with self._lock:
            if not self.workload_queue:
                self._switch_mode(EngineMode.THINKING)
                return
            
            # --- Starvation Avoidance ---
            # Sort by Urgency (Quality + Age)
            now = time.time()
            self.workload_queue.sort(
                key=lambda x: x.quality_score + ((now - x.created_at.timestamp()) / 600.0),
                reverse=True
            )
            
            abs_obj = self.workload_queue.pop(0)

            # --- Ruthless Pruning (Hard Cap) ---
            # If queue is too big, drop the bottom 10% immediately
            if len(self.workload_queue) > 500:
                cut_point = int(len(self.workload_queue) * 0.9)
                self.workload_queue = self.workload_queue[:cut_point]
                logger.info("💀 Ruthless Pruning: Dropped bottom 10% of queue overflow")
        
        logger.info(f"🔥 Awake [FOCUSED]: First-principles on {abs_obj.id[:8]}... "
                     f"(consistency={abs_obj.consistency_score:.2f})")
        
        # Step 1: Extract logical proposition via bridge
        proposition = self.bridge.engram_to_axiom_sync(abs_obj)
        
        if not proposition:
            logger.info(f"  → Could not extract proposition, falling back to LLM")
            abs_obj.consistency_score = 0.7  # Mild penalty
            self._switch_mode(EngineMode.THINKING)
            return
        
        # Step 2: Attempt proof
        domain = abs_obj.metadata.get("domain", proposition.domain)
        
        proof = self.reasoning.prove(
            query=f"Verify: {proposition.formula}",
            domain=domain,
        )
        
        if proof.proven:
            # SUCCESS: Store proof as high-salience engram
            proof_data = proof.to_dict()
            proof_data["formula"] = proposition.formula
            proof_data["domain"] = domain
            
            proof_engram = self.bridge.axiom_to_engram(proof_data)
            
            # Generate embedding and store
            try:
                from core.embedding import EmbeddingHandler
                embedder = EmbeddingHandler()
                embedding = embedder.generate_embedding(proof_engram.content)
                self.storage.add_abstraction(proof_engram, embedding)
                
                logger.info(f"  → ✅ Proof stored as engram {proof_engram.id[:8]}...")
            except Exception as e:
                logger.warning(f"  → Failed to embed proof engram: {e}")
            
            # Update original engram
            abs_obj.consistency_score = 1.0
            abs_obj.is_axiom_derived = True
            abs_obj.proof_id = proof_engram.id
            abs_obj.axioms_used = proof.axioms_used
            self.manager.update_abstraction(abs_obj.id, content=abs_obj.content)
            
            self.proofs_generated += 1
            
        else:
            # Proof failed - lower consistency
            old_score = abs_obj.consistency_score
            abs_obj.consistency_score = max(0.3, old_score - 0.2)
            self.manager.update_abstraction(abs_obj.id, content=abs_obj.content)
            
            logger.info(f"  → ❌ Proof failed: {proof.error or 'unknown'}. "
                         f"Consistency: {old_score:.2f} → {abs_obj.consistency_score:.2f}")
        
        # Check if more work in queue
        if not self.workload_queue:
            self._switch_mode(EngineMode.THINKING)

    def _dream(self):
        """DREAMING: Internal graph optimization (Low Cost)"""
        logger.info("💭 Awake [DREAMING]: Optimizing semantic graph...")
        
        with self._lock:
            # 1. Prune orphans
            count = self.storage.prune_orphans(min_quality=0.4)
            if count > 0:
                logger.info(f"  → Pruned {count} orphan nodes")
                
        # 2. Run Clustering Algorithm (if affordable)
        # TODO: Implement ClusterManager integration
        
        logger.info("  → Graph optimized (Dream Cycle complete)")
        time.sleep(1.0) # Slow metabolism

    
    # === Engine Control ===
    
    def _switch_mode(self, new_mode: EngineMode):
        """Switch engine mode with logging"""
        if new_mode == self.mode:
            return
        
        old_mode = self.mode
        self.mode = new_mode
        self.mode_switches += 1
        self.last_mode_change = time.time()
        
        mode_emoji = {
            EngineMode.IDLE: "💤",
            EngineMode.THINKING: "🤔", 
            EngineMode.FOCUSED: "🔥",
            EngineMode.SLEEPING: "😴",
        }
        
        logger.info(f"{mode_emoji.get(new_mode, '?')} Awake Engine: "
                     f"{old_mode.value} → {new_mode.value} "
                     f"(queue: {len(self.workload_queue)})")
    
    def _adjust_hz(self):
        """Dynamically adjust processing rate based on mode and workload"""
        if self.mode == EngineMode.IDLE:
            self.current_hz = self.min_hz  # 0.5 Hz
            
        elif self.mode == EngineMode.THINKING:
            # Scale with queue size: 2-15 Hz
            queue_pressure = min(len(self.workload_queue), 10) / 10
            self.current_hz = 2 + queue_pressure * 13
            
        elif self.mode == EngineMode.FOCUSED:
            # High rate during focused reasoning: 15-60 Hz
            self.current_hz = min(self.max_hz, 15 + len(self.workload_queue) * 5)
            
        elif self.mode == EngineMode.SLEEPING:
            self.current_hz = 0.0
    
    def _find_weak_abstractions(self, limit: int = 3) -> List[Abstraction]:
        """Find abstractions with low quality or low consistency"""
        candidates = []
        try:
            # Query for low quality OR low consistency
            cursor = self.storage.conn.execute("""
                SELECT id FROM abstractions 
                WHERE quality_score < ? OR consistency_score < ?
                ORDER BY consistency_score ASC, quality_score ASC 
                LIMIT ?
            """, (config.UNCERTAINTY_THRESHOLD, self.consistency_threshold, limit))
            
            for row in cursor.fetchall():
                abs_obj = self.storage.get_abstraction(row[0])
                if abs_obj:
                    candidates.append(abs_obj)
                    
        except Exception as e:
            logger.error(f"Failed to find weak abstractions: {e}")
        
        return candidates
    
    # === External Triggers ===
    
    def trigger_focused_burst(self, engrams: List[Abstraction]):
        """External trigger for focused reasoning on specific engrams"""
        logger.info(f"⚡ Awake Engine: Focused burst triggered on {len(engrams)} items")
        self.workload_queue.extend(engrams)
        self._switch_mode(EngineMode.FOCUSED)
    
    def get_status(self) -> dict:
        """Get current engine status"""
        return {
            "mode": self.mode.value,
            "hz": self.current_hz,
            "queue_size": len(self.workload_queue),
            "cycle_count": self.cycle_count,
            "proofs_generated": self.proofs_generated,
            "refinements_made": self.refinements_made,
            "consistency_checks": self.consistency_checks,
            "mode_switches": self.mode_switches,
            "running": self.running,
        }
    
    # === Human-Like Thinking Pauses ===
    
    @staticmethod
    def thinking_response(confidence: float) -> Optional[str]:
        """Generate a human-like thinking pause message if confidence is low"""
        if confidence >= 0.75:
            return None
        
        pauses = [
            "Hmm, let me think about that...",
            "Interesting question. Working through the logic...",
            "That requires some deeper reasoning...",
            "Let me verify this against what I know...",
            "Thinking carefully about this one...",
        ]
        return random.choice(pauses)
