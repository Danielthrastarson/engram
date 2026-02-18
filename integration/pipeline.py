# integration/pipeline.py
# Engram Awake Cortex v5.0 — Neuroscience-Grounded Pipeline
#
# Key changes from v4.6:
# 1. Prediction Error: predict before processing, compute surprise after
# 2. Impasse Detection: failures spawn sub-goals for directed learning
# 3. Parallel Competition: fast + slow paths compete, winner takes all
# 4. Reconsolidation: retrieved engrams are modified at moment of use
# 5. Winner-Take-All Gate: 3 translators compete (not 7 voting)
# 6. No more sequential Router → Pipeline; competition is the routing

import logging
import threading
import time
import concurrent.futures
from typing import Optional, Tuple
from core.abstraction_manager import AbstractionManager
from retrieval.search import Searcher
from retrieval.context import ContextBuilder
from integration.llm_interface import LLMInterface
from utils import config

logger = logging.getLogger(__name__)

from core.router import SemanticRouter


class CompetitionResult:
    """Result from one processing path"""
    def __init__(self, content: str, confidence: float, 
                 path: str, proof_data: dict = None):
        self.content = content
        self.confidence = confidence
        self.path = path  # "fast" or "symbolic"
        self.proof_data = proof_data


class EngramPipeline:
    """
    Neuroscience-grounded query pipeline.
    
    Architecture:
    1. Winner-Take-All Gate (3 translators, lateral inhibition)
    2. Prediction (what do we expect the answer to be?)
    3. Parallel Competition (fast + symbolic paths race)
    4. Winner Takes All (highest confidence wins)
    5. Prediction Error Signal (drives learning priority)
    6. Reconsolidation (modify retrieved engrams at point of use)
    7. Impasse Detection (failures → sub-goals → directed learning)
    """
    
    def __init__(self):
        self.manager = AbstractionManager()
        self.searcher = Searcher()
        self.context_builder = ContextBuilder()
        self.llm = LLMInterface()
        self.router = SemanticRouter()
        
        # === Neuroscience Components ===
        self._reasoning_ready = False
        self._init_reasoning()
    
    def _init_reasoning(self):
        """Initialize all neuroscience-grounded components"""
        try:
            from reasoning.translator_gate import SecureTranslatorGate
            from reasoning.query_router import QueryRouter
            from reasoning.symbolic_reasoning import ReasoningEngine
            from reasoning.bridge import SemanticBridge
            from reasoning.axiom_store import AxiomStore
            from reasoning.heartbeat import Heartbeat
            from reasoning.awake_engine import AwakeEngine
            from reasoning.prediction import PredictionEngine
            from reasoning.impasse import ImpasseDetector
            from reasoning.reconsolidation import ReconsolidationEngine
            from reasoning.rhythms import BrainRhythms
            from reasoning.working_memory import WorkingMemory
            from core.seeking_drive import SeekingDrive
            from core.internal_economy import InternalMarket
            
            # === Layer 0: Winner-Take-All Gate (3 translators) ===
            self.gate = SecureTranslatorGate(
                llm=self.llm,
                num_translators=3,
                min_agreement=config.TRANSLATOR_MIN_AGREEMENT,
            )
            
            # === Working Memory (Miller's 7±2) ===
            self.working_memory = WorkingMemory(capacity=7)
            
            # === Internal Economy (Phase 7) ===
            self.seeking_drive = SeekingDrive()
            self.market = InternalMarket(self.seeking_drive)
            
            # === Prediction Engine (Friston Free Energy) ===
            self.prediction_engine = PredictionEngine()
            
            # === Impasse Detector (SOAR-style) ===
            self.impasse_detector = ImpasseDetector()
            
            # === Reconsolidation Engine (Nader 2000) ===
            self.reconsolidation = ReconsolidationEngine(window_duration=30.0)
            
            # === Polyrhythmic Processing ===
            self.rhythms = BrainRhythms()
            
            # === Layer 2: Reasoning Engine ===
            self.axiom_store = AxiomStore()
            self.axiom_store.seed_foundational()
            self.bridge = SemanticBridge(llm=self.llm)
            self.reasoning_engine = ReasoningEngine(
                llm=self.llm,
                axiom_store=self.axiom_store,
            )
            
            # === Query Router (still used for keyword hints) ===
            self.query_router = QueryRouter(
                searcher=self.searcher,
            )
            
            # === Awake Engine (background thread) ===
            self.awake_engine = AwakeEngine()
            self.awake_engine.set_market(self.market)
            
            # === Heartbeat (1 Hz master clock) ===
            self.heartbeat = Heartbeat()
            self.heartbeat.set_market(self.market)
            self.heartbeat.register("storage", self.manager.storage)
            self.heartbeat.register("awake_engine", self.awake_engine)
            self.heartbeat.register("reasoning_engine", self.reasoning_engine)
            self.heartbeat.register("translator_gate", self.gate)
            self.heartbeat.register("prediction", self.prediction_engine)
            self.heartbeat.register("impasse", self.impasse_detector)
            self.heartbeat.register("reconsolidation", self.reconsolidation)
            from utils.metrics import MetricsTracker
            self.heartbeat.register("metrics", MetricsTracker())
            
            self._reasoning_ready = True
            self._deliberation_count = 0  # Track deliberation cycles
            logger.info("🧠 Neuroscience pipeline v6.1 initialized (working memory + deliberation)")
            
        except Exception as e:
            logger.error(f"Failed to initialize reasoning pipeline: {e}")
            import traceback
            traceback.print_exc()
            self._reasoning_ready = False
    
    def start_engines(self):
        """Start background engines"""
        if not self._reasoning_ready:
            logger.warning("Reasoning not initialized, skipping engine start")
            return
        
        # Start heartbeat (1 Hz master clock)
        self.heartbeat.start()
        
        # Start Awake Engine in background thread
        self._awake_thread = threading.Thread(
            target=self.awake_engine.start,
            daemon=True,
            name="AwakeEngine"
        )
        self._awake_thread.start()
        
        logger.info("🚀 All engines started (Heartbeat + Awake Engine + Rhythms)")
    
    def stop_engines(self):
        """Stop all background engines"""
        if self._reasoning_ready:
            try: self.awake_engine.stop()
            except Exception: pass
            try: self.heartbeat.stop()
            except Exception: pass
            try: self.rhythms.stop()
            except Exception: pass
            logger.info("⏹ All engines stopped")

    # ==========================================================
    # QUERY PIPELINE — Neuroscience-Grounded + Deliberation Loop
    # ==========================================================
    
    MAX_DELIBERATIONS = 3
    CONFIDENCE_THRESHOLD = 0.3  # Below this, re-deliberate
    
    def process_query(self, query: str) -> str:
        """
        Neuroscience-grounded query pipeline with DELIBERATION LOOP.
        
        Instead of single-pass reasoning, the system thinks iteratively:
        
        for attempt in range(3):
            1. Gate filter
            2. Retrieve (semantic + graph neighbors + working memory)
            3. Predict outcome
            4. Parallel competition (fast vs symbolic)
            5. Compute prediction error
            6. If confident → return
            7. If not → refine query, re-retrieve, re-reason
        
        After loop:
            8. Reconsolidate retrieved engrams
            9. Update working memory
            10. Detect impasses from failures
        """
        # === Step 1: Winner-Take-All Gate ===
        gate_confidence = 1.0
        if self._reasoning_ready:
            filtered = self.gate.filter_input(query)
            gate_confidence = filtered.confidence
            
            if filtered.needs_clarification and gate_confidence < 0.4:
                if self._reasoning_ready:
                    self.impasse_detector.detect(query, {
                        "gate_confidence": gate_confidence,
                        "confidence": gate_confidence,
                    })
                return ("I'm not quite sure I understand. Could you rephrase that? "
                        f"(confidence: {gate_confidence:.0%})")
            
            clean_query = filtered.content
        else:
            clean_query = query
        
        # Non-reasoning fast path
        if not self._reasoning_ready:
            relevant_abs = self.searcher.search(
                clean_query, top_k=config.DEFAULT_TOP_K
            )
            return self._fast_path(clean_query, relevant_abs)
        
        # ==========================================================
        # DELIBERATION LOOP (Prefrontal Cortex Executive Control)
        # ==========================================================
        
        best_winner = None
        best_confidence = 0.0
        all_relevant_abs = []
        current_query = clean_query
        prediction = None
        prediction_error = None
        
        for attempt in range(self.MAX_DELIBERATIONS):
            self._deliberation_count += 1
            
            # === Retrieve (semantic + graph walk + working memory) ===
            target_cluster = None
            if config.ENABLE_HYPERFOCUS:
                routes = self.router.route_query(current_query, top_k=1)
                if routes:
                    target_cluster = routes[0]
            
            # Hierarchical retrieval: graph_depth=1 expands to neighbors
            graph_depth = 1 if attempt == 0 else 0  # Only graph-walk on first attempt
            relevant_abs = self.searcher.search(
                current_query,
                top_k=config.DEFAULT_TOP_K,
                cluster_id=target_cluster,
                graph_depth=graph_depth,
            )
            
            # Inject working memory items (always in context)
            wm_context = self.working_memory.get_context()
            
            # Predict before reasoning
            prediction = self.prediction_engine.predict(current_query, relevant_abs)
            
            # Open reconsolidation windows
            for engram in relevant_abs:
                self.reconsolidation.open_window(engram.id, current_query)
            
            # === Parallel Competition ===
            winner = self._parallel_competition(current_query, relevant_abs,
                                                wm_context=wm_context)
            
            # === Prediction Error ===
            domain = self.impasse_detector._infer_domain(current_query)
            prediction_error = self.prediction_engine.compute_error(
                prediction=prediction,
                actual_content=winner.content,
                actual_confidence=winner.confidence,
                domain=domain,
            )
            
            # Track best result
            if winner.confidence > best_confidence:
                best_winner = winner
                best_confidence = winner.confidence
                all_relevant_abs = relevant_abs
            
            # === Confidence check: should we deliberate again? ===
            error_mag = prediction_error.error_magnitude if prediction_error else 0
            
            if winner.confidence >= 0.5 and error_mag < self.CONFIDENCE_THRESHOLD:
                # Confident + low error → done
                if attempt > 0:
                    logger.info(f"💭 Deliberation resolved in {attempt+1} cycles")
                break
            
            if attempt < self.MAX_DELIBERATIONS - 1:
                # Re-deliberate: refine the query
                current_query = self._refine_query_for_deliberation(
                    original_query=clean_query,
                    current_query=current_query,
                    winner=winner,
                    error_mag=error_mag,
                    attempt=attempt,
                    relevant_count=len(relevant_abs),
                )
                logger.info(f"💭 Deliberation cycle {attempt+1}: error={error_mag:.2f}, "
                            f"confidence={winner.confidence:.2f} → re-reasoning")
        
        # Use best result from all attempts
        winner = best_winner
        relevant_abs = all_relevant_abs
        
        # === Post-deliberation: Reconsolidate ===
        if prediction_error:
            for engram in relevant_abs:
                mods = self.reconsolidation.evaluate_and_modify(
                    engram=engram,
                    query=clean_query,
                    response_quality=winner.confidence,
                    prediction_error=prediction_error.error_magnitude,
                )
                if mods and "_needs_refinement" not in mods:
                    try:
                        if "quality_score" in mods:
                            engram.quality_score = mods["quality_score"]
                        if "consistency_score" in mods:
                            engram.consistency_score = mods["consistency_score"]
                        if "decay_score" in mods:
                            engram.decay_score = mods["decay_score"]
                        self.manager.update_abstraction(engram.id, content=engram.content)
                    except Exception as e:
                        logger.warning(f"Reconsolidation apply failed: {e}")
        
        # === Post-deliberation: Update Working Memory ===
        self.working_memory.update(clean_query, relevant_abs)
        
        # === Post-deliberation: Detect Impasses ===
        if winner.confidence < 0.5:
            self.impasse_detector.detect(clean_query, {
                "confidence": winner.confidence,
                "engrams_found": len(relevant_abs),
                "gate_confidence": gate_confidence,
                "proof_result": winner.proof_data or {},
                "deliberation_cycles": min(self.MAX_DELIBERATIONS, 
                                           self._deliberation_count),
            })
        
        # Record usage
        for abs_obj in relevant_abs:
            self.manager.record_usage(abs_obj.id, successful=(winner.confidence > 0.5))
        
        # Track for user feedback
        self._last_query_engrams = relevant_abs
        self._last_query_text = clean_query
        
        return winner.content
    
    def _refine_query_for_deliberation(self, original_query: str, current_query: str,
                                        winner, error_mag: float, attempt: int,
                                        relevant_count: int) -> str:
        """
        Refine the query for the next deliberation cycle.
        
        Strategy depends on what went wrong:
        - Low retrieval → broaden query
        - High prediction error → add specificity
        - Low confidence → rephrase
        """
        if relevant_count < 2:
            # Too few results → broaden
            return original_query  # Go back to original (remove any narrowing)
        
        if error_mag > 0.7:
            # Very surprising result → add context from winner to narrow
            key_terms = winner.content.split()[:5]
            return f"{original_query} specifically regarding {' '.join(key_terms)}"
        
        if attempt == 1:
            # Second attempt → try rephrasing
            return f"Explain: {original_query}"
        
        # Default: return original
        return original_query
    
    def _parallel_competition(self, query: str, relevant_abs: list,
                               wm_context: list = None) -> CompetitionResult:
        """
        Run fast and symbolic paths in PARALLEL.
        Winner-take-all: highest confidence wins.
        
        wm_context: Working memory strings to prepend to reasoning context.
        """
        # Check if symbolic is worth trying (has symbolic keywords)
        from reasoning.query_router import ReasoningMode
        routing = self.query_router.route(query)
        
        # Always run fast path
        fast_result = self._fast_path_scored(query, relevant_abs, wm_context=wm_context)
        
        # Only run symbolic if keywords suggest it or confidence is low
        if routing.engine in (ReasoningMode.SYMBOLIC, ReasoningMode.HYBRID):
            try:
                symbolic_result = self._symbolic_path_scored(query, relevant_abs)
            except Exception as e:
                logger.warning(f"Symbolic path error: {e}")
                symbolic_result = None
        else:
            symbolic_result = None
        
        # === Winner Takes All ===
        candidates = [fast_result]
        if symbolic_result and symbolic_result.confidence > 0:
            candidates.append(symbolic_result)
        
        winner = max(candidates, key=lambda r: r.confidence)
        
        # Log competition
        if len(candidates) > 1:
            loser = min(candidates, key=lambda r: r.confidence)
            logger.info(f"⚔️ Competition: {winner.path}({winner.confidence:.2f}) "
                        f"beat {loser.path}({loser.confidence:.2f})")
        
        return winner
    
    def _fast_path_scored(self, query: str, relevant_abs: list,
                          wm_context: list = None) -> CompetitionResult:
        """Fast path returning a scored CompetitionResult.
        Prepends working memory items to context for persistent focus."""
        context_str = self.context_builder.format_context(relevant_abs)
        
        # Prepend working memory (persistent focus items)
        if wm_context:
            wm_str = "\n".join(f"[Working Memory] {item}" for item in wm_context)
            context_str = f"{wm_str}\n\n{context_str}"
        
        # Truth Guard
        from core.truth_guard import TruthGuard
        risk, is_safe = TruthGuard.calculate_risk(relevant_abs)
        honest_forced = TruthGuard.enforce_honest_response(query, risk, relevant_abs)

        if honest_forced:
            return CompetitionResult(
                content=honest_forced,
                confidence=0.2,
                path="fast_honest",
            )
        
        response = self.llm.reason(query, context_str)
        
        # Confidence = inverse risk * context quality
        avg_quality = sum(a.quality_score for a in relevant_abs) / max(len(relevant_abs), 1)
        confidence = (1.0 - risk) * avg_quality if relevant_abs else 0.3
        
        return CompetitionResult(
            content=response,
            confidence=confidence,
            path="fast",
        )
    
    def _symbolic_path_scored(self, query: str, relevant_abs: list) -> CompetitionResult:
        """Symbolic path returning a scored CompetitionResult"""
        # Infer domain
        domain = self.impasse_detector._infer_domain(query)
        
        # Attempt formal proof
        proof = self.reasoning_engine.prove(query=query, domain=domain)
        
        if proof.proven:
            # Store proof as engram
            proof_data = proof.to_dict()
            proof_engram = self.bridge.axiom_to_engram(proof_data)
            
            try:
                from core.embedding import EmbeddingHandler
                embedder = EmbeddingHandler()
                embedding = embedder.generate_embedding(proof_engram.content)
                self.manager.storage.add_abstraction(proof_engram, embedding)
            except Exception as e:
                logger.warning(f"Failed to store proof engram: {e}")
            
            self.awake_engine.proofs_generated += 1
            
            # Build response
            context_str = self.context_builder.format_context(relevant_abs)
            response = self.llm.reason(query, context_str)
            
            return CompetitionResult(
                content=f"{response}\n\n[Verified via first-principles reasoning "
                        f"({proof.verifier}, confidence: {proof.confidence:.0%})]",
                confidence=proof.confidence,
                path="symbolic",
                proof_data=proof_data,
            )
        else:
            # Proof failed — return with low confidence for competition
            return CompetitionResult(
                content="",
                confidence=0.0,
                path="symbolic_failed",
                proof_data=proof.to_dict() if hasattr(proof, 'to_dict') else {"proven": False},
            )
    
    # Keep original _fast_path for backward compatibility
    def _fast_path(self, query: str, relevant_abs: list) -> str:
        """Legacy fast path (returns string only)"""
        result = self._fast_path_scored(query, relevant_abs)
        return result.content

    # ==========================================================
    # INGEST PIPELINE
    # ==========================================================
    
    def ingest(self, text: str, source: str = "user"):
        """
        Ingest new knowledge through the full pipeline.
        1. Filter through Gate
        2. Retrieve context
        3. Compress into abstraction
        4. Store with consistency check
        """
        # Filter through gate
        if self._reasoning_ready:
            filtered = self.gate.filter_input(text)
            clean_text = filtered.content
        else:
            clean_text = text
        
        # Context
        related = self.searcher.search(clean_text, top_k=3)
        context_str = self.context_builder.format_context(related)
        
        # Compress
        compressed_content = self.llm.generate_abstraction(clean_text, context_str)
        
        # Store
        abs_obj, created = self.manager.create_abstraction(
            compressed_content,
            metadata={"source": source, "original_length": len(text)}
        )
        
        # Check consistency if reasoning is ready
        if created and self._reasoning_ready:
            try:
                prop = self.bridge.engram_to_axiom_sync(abs_obj)
                if prop:
                    proof = self.reasoning_engine.prove(
                        query=f"Verify: {prop.formula}",
                        domain=prop.domain,
                    )
                    abs_obj.consistency_score = proof.confidence
                    if proof.proven:
                        abs_obj.is_axiom_derived = True
                        abs_obj.axioms_used = proof.axioms_used
                    self.manager.update_abstraction(abs_obj.id, content=abs_obj.content)
            except Exception as e:
                logger.warning(f"Consistency check failed: {e}")
    
    # ==========================================================
    # STATUS & DIAGNOSTICS
    # ==========================================================
    
    # Track last query's engrams for user feedback
    _last_query_engrams: list = []
    _last_query_text: str = ""
    
    def get_brain_status(self) -> dict:
        """Full brain status including all neuroscience components"""
        status = {
            "version": "v6.0-embodied",
            "reasoning_ready": self._reasoning_ready,
            "llm_provider": self.llm.provider,
        }
        
        if self._reasoning_ready:
            status["prediction"] = self.prediction_engine.get_stats()
            status["impasses"] = self.impasse_detector.get_stats()
            status["reconsolidation"] = self.reconsolidation.get_stats()
            status["rhythms"] = self.rhythms.get_status()
            status["awake_engine"] = self.awake_engine.get_status()
            status["heartbeat"] = self.heartbeat.get_health()
        
        return status
    
    def user_feedback_helpful(self) -> str:
        """User reports last answer was helpful → strengthen engrams"""
        if not self._last_query_engrams:
            return "No recent query to rate."
        
        count = 0
        for engram in self._last_query_engrams:
            window = self.reconsolidation.open_window(engram.id, self._last_query_text)
            mods = self.reconsolidation.evaluate_and_modify(
                engram=engram,
                query=self._last_query_text,
                response_quality=0.95,   # User says it was good
                prediction_error=0.05,   # Low error
            )
            if mods:
                try:
                    if "quality_score" in mods:
                        engram.quality_score = mods["quality_score"]
                    
                    # === Integrity Boost ===
                    engram.integrity_score = min(1.0, engram.integrity_score + 0.05)
                    engram.verification_history.append({
                        "action": "verified",
                        "source": "user_feedback",
                        "timestamp": time.time()
                    })
                    
                    self.manager.update_abstraction(engram.id, content=engram.content)
                    count += 1
                except Exception:
                    pass
        
        return f"Strengthened {count} engram(s) via reconsolidation."
    
    def user_feedback_wrong(self) -> str:
        """User reports last answer was wrong → weaken engrams + create impasse"""
        if not self._last_query_engrams:
            return "No recent query to rate."
        
        count = 0
        for engram in self._last_query_engrams:
            window = self.reconsolidation.open_window(engram.id, self._last_query_text)
            mods = self.reconsolidation.evaluate_and_modify(
                engram=engram,
                query=self._last_query_text,
                response_quality=0.1,    # User says it was bad
                prediction_error=0.9,    # High error
            )
            if mods:
                try:
                    if "quality_score" in mods:
                        engram.quality_score = mods["quality_score"]
                    if "decay_score" in mods:
                        engram.decay_score = mods["decay_score"]
                        
                    # === Integrity Slash ===
                    # Punishment is 5x stronger than reward (Loss Aversion)
                    engram.integrity_score = max(0.0, engram.integrity_score - 0.25)
                    engram.verification_history.append({
                        "action": "falsified",
                        "source": "user_feedback",
                        "timestamp": time.time()
                    })
                        
                    self.manager.update_abstraction(engram.id, content=engram.content)
                    count += 1
                except Exception:
                    pass
        
        # Create impasse for directed learning
        if self._reasoning_ready:
            self.impasse_detector.detect(self._last_query_text, {
                "confidence": 0.1,
                "engrams_found": len(self._last_query_engrams),
                "gate_confidence": 0.9,
            })
        
        return f"Weakened {count} engram(s) + created impasse for re-learning."
