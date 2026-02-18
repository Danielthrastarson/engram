# reasoning/heartbeat.py
# 1 Hz Master Clock + Brain-Wide Metrics Collector
# The central nervous system monitor — collects, timestamps, and serves all brain metrics

import time
import threading
import logging
from collections import deque
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from core.internal_economy import Bid

logger = logging.getLogger(__name__)

# Maximum time-series history (keeps last 300 data points = 5 min at 1 Hz)
MAX_HISTORY = 300


@dataclass
class BrainSnapshot:
    """A single timestamped snapshot of the entire brain's state"""
    tick: int = 0
    timestamp: float = 0.0
    
    # Awake Engine
    awake_mode: str = "sleeping"
    awake_hz: float = 0.0
    awake_queue: int = 0
    
    # Reasoning
    proofs_total: int = 0
    proofs_this_tick: int = 0
    proof_cache_size: int = 0
    
    # Memory
    total_engrams: int = 0
    avg_quality: float = 0.0
    avg_consistency: float = 0.0
    axiom_derived_count: int = 0
    low_consistency_count: int = 0
    
    # Activity
    refinements_total: int = 0
    queries_total: int = 0
    errors_total: int = 0
    
    # Translator Gate
    gate_confidence: float = 1.0
    gate_cache_size: int = 0
    
    # System
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "tick": self.tick,
            "timestamp": self.timestamp,
            "awake_mode": self.awake_mode,
            "awake_hz": self.awake_hz,
            "awake_queue": self.awake_queue,
            "proofs_total": self.proofs_total,
            "proofs_this_tick": self.proofs_this_tick,
            "proof_cache_size": self.proof_cache_size,
            "total_engrams": self.total_engrams,
            "avg_quality": round(self.avg_quality, 3),
            "avg_consistency": round(self.avg_consistency, 3),
            "axiom_derived_count": self.axiom_derived_count,
            "low_consistency_count": self.low_consistency_count,
            "refinements_total": self.refinements_total,
            "queries_total": self.queries_total,
            "errors_total": self.errors_total,
            "gate_confidence": round(self.gate_confidence, 3),
            "gate_cache_size": self.gate_cache_size,
            "cpu_percent": round(self.cpu_percent, 1),
            "memory_mb": round(self.memory_mb, 1),
        }


class Heartbeat:
    """
    1 Hz master clock for the entire brain.
    
    Every tick:
    1. Collects metrics from all components
    2. Stores timestamped snapshot in ring buffer
    3. Feeds metrics back to Awake Engine for metacognitive adjustment
    4. Broadcasts to connected WebSocket clients
    
    The ring buffer provides 300 data points (5 minutes of history)
    for real-time charting.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.tick_count = 0
        self.start_time = time.time()
        self.running = False
        self._thread: Optional[threading.Thread] = None
        
        # Time-series ring buffer for charting
        self.history: deque = deque(maxlen=MAX_HISTORY)
        
        # Current snapshot
        self.current = BrainSnapshot()
        
        # Component references (set by register())
        self._components: Dict[str, Any] = {}
        
        # Listeners for real-time broadcast
        self._listeners: List[callable] = []
        
        # Internal Market
        self.market = None
        
        # Error tracking for circuit breaker
        self._error_window: deque = deque(maxlen=60)  # Last 60 ticks
        self.error_rate = 0.0
        self.halted = False
        self.halt_reason = ""
        
        self._initialized = True
        logger.info("💓 Heartbeat initialized")
    
    def register(self, name: str, component: Any):
        """Register a component for metric collection"""
        self._components[name] = component
        logger.info(f"💓 Registered component: {name}")

    def set_market(self, market):
        """Set the internal market instance"""
        self.market = market
    
    def on_tick(self, callback: callable):
        """Register a callback to run on every heartbeat tick"""
        self._listeners.append(callback)
    
    def start(self):
        """Start the heartbeat in a background thread"""
        if self.running:
            return
        
        self.running = True
        self._thread = threading.Thread(target=self._beat_loop, daemon=True)
        self._thread.start()
        logger.info("💓 Heartbeat started (1 Hz)")
    
    def stop(self):
        """Stop the heartbeat"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=3)
        logger.info(f"💓 Heartbeat stopped after {self.tick_count} ticks")
    
    def _beat_loop(self):
        """Main heartbeat loop — runs at ~1 Hz"""
        while self.running:
            tick_start = time.time()
            
            try:
                self._tick()
            except Exception as e:
                logger.error(f"💓 Heartbeat tick error: {e}")
                self._record_error(str(e))
            
            # Maintain 1 Hz
            elapsed = time.time() - tick_start
            sleep_time = max(0, 1.0 - elapsed)
            time.sleep(sleep_time)
    
    def _tick(self):
        """Execute one heartbeat tick"""
        self.tick_count += 1
        
        # Collect snapshot
        snapshot = self._collect_snapshot()
        
        # Store in history
        self.history.append(snapshot)
        self.current = snapshot
        
        # Check circuit breaker
        self._check_circuit_breaker(snapshot)
        
        # Metacognitive feedback
        self._metacognitive_adjust(snapshot)
        
        # Notify listeners
        for callback in self._listeners:
            try:
                callback(snapshot)
            except Exception as e:
                logger.warning(f"Heartbeat listener error: {e}")
        
        # Run Internal Economy Auction (1 Hz)
        if self.market:
            try:
                bids = self._collect_bids()
                allocations = self.market.run_auction(bids)
                self._distribute_allocations(allocations)
            except Exception as e:
                logger.error(f"Market Auction error: {e}")

    def _collect_bids(self) -> List[Bid]:
        """Collect bids from all agents"""
        bids = []
        awake = self._components.get("awake_engine")
        if awake and hasattr(awake, "construct_bid"):
            bid_data = awake.construct_bid()
            bids.append(Bid(**bid_data))
        return bids

    def _distribute_allocations(self, allocations: dict):
        """Distribute resources to winners"""
        awake = self._components.get("awake_engine")
        if awake and hasattr(awake, "receive_allocation"):
            # Check if awake won
            my_alloc = {}
            for res, winners in allocations.items():
                for win in winners:
                    if win["winner"] == "awake_engine":
                        my_alloc = {"resource": res, "amount": win["amount"]}
                        break
            awake.receive_allocation(my_alloc)
    
    def _collect_snapshot(self) -> BrainSnapshot:
        """Collect metrics from all registered components"""
        snap = BrainSnapshot(
            tick=self.tick_count,
            timestamp=time.time(),
        )
        
        # Awake Engine metrics
        awake = self._components.get("awake_engine")
        if awake:
            status = awake.get_status()
            snap.awake_mode = status.get("mode", "unknown")
            snap.awake_hz = status.get("hz", 0)
            snap.awake_queue = status.get("queue_size", 0)
            snap.proofs_total = status.get("proofs_generated", 0)
            snap.refinements_total = status.get("refinements_made", 0)
        
        # Reasoning Engine metrics
        reasoning = self._components.get("reasoning_engine")
        if reasoning:
            snap.proof_cache_size = len(reasoning._proof_cache)
        
        # Storage metrics
        storage = self._components.get("storage")
        if storage:
            try:
                row = storage.conn.execute("""
                    SELECT 
                        COUNT(*) as total,
                        AVG(quality_score) as avg_q,
                        AVG(consistency_score) as avg_c,
                        SUM(CASE WHEN is_axiom_derived = 1 THEN 1 ELSE 0 END) as axiom_ct,
                        SUM(CASE WHEN consistency_score < 0.5 THEN 1 ELSE 0 END) as low_ct
                    FROM abstractions
                """).fetchone()
                if row:
                    snap.total_engrams = row[0] or 0
                    snap.avg_quality = row[1] or 0.0
                    snap.avg_consistency = row[2] or 1.0
                    snap.axiom_derived_count = row[3] or 0
                    snap.low_consistency_count = row[4] or 0
            except Exception:
                pass
        
        # Translator Gate metrics
        gate = self._components.get("translator_gate")
        if gate:
            snap.gate_cache_size = len(gate._cache)
        
        # Metrics tracker
        metrics = self._components.get("metrics")
        if metrics:
            snap.queries_total = metrics.data.get("queries_total", 0)
            snap.errors_total = metrics.data.get("errors_total", 0)
        
        # System metrics
        try:
            import psutil
            snap.cpu_percent = psutil.cpu_percent(interval=0)
            snap.memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
        except ImportError:
            pass
        
        return snap
    
    def _check_circuit_breaker(self, snap: BrainSnapshot):
        """Monitor error rate and halt if too high"""
        errors_this_tick = snap.errors_total - (
            self.history[-2].errors_total if len(self.history) >= 2 else 0
        )
        self._error_window.append(errors_this_tick)
        
        # Error rate = errors per tick over last 60 ticks
        self.error_rate = sum(self._error_window) / max(len(self._error_window), 1)
        
        if self.error_rate > 5.0 and not self.halted:
            self.halted = True
            self.halt_reason = f"Circuit breaker tripped: error rate {self.error_rate:.1f}/tick"
            logger.critical(f"🚨 {self.halt_reason}")
            
            # Halt the awake engine
            awake = self._components.get("awake_engine")
            if awake:
                awake.stop()
    
    def _metacognitive_adjust(self, snap: BrainSnapshot):
        """
        METACOGNITIVE FEEDBACK: The brain watching itself and adjusting.
        
        Uses real metrics to modify the Awake Engine's behavior:
        - Low consistency → speed up reasoning
        - High error rate → slow down
        - All healthy → maintain idle
        """
        awake = self._components.get("awake_engine")
        if not awake or not awake.running:
            return
        
        # Rule 1: Many low-consistency engrams → escalate
        if snap.low_consistency_count > 5 and awake.mode.value == "idle":
            logger.info(f"🧠 Metacognition: {snap.low_consistency_count} low-consistency "
                        f"engrams detected, escalating Awake Engine")
            weak = awake._find_weak_abstractions(limit=3)
            if weak:
                awake.trigger_focused_burst(weak)
        
        # Rule 2: High error rate → slow down
        if self.error_rate > 2.0:
            awake.current_hz = max(awake.min_hz, awake.current_hz * 0.5)
            logger.info(f"🧠 Metacognition: High error rate ({self.error_rate:.1f}), "
                        f"slowing to {awake.current_hz:.1f} Hz")
        
        # Rule 3: Large queue → speed up
        if snap.awake_queue > 10:
            awake.current_hz = min(awake.max_hz, awake.current_hz * 1.5)
        
        # Rule 4: Everything healthy → gradually return to idle
        if (snap.avg_consistency > 0.9 and snap.low_consistency_count == 0 
                and awake.mode.value == "thinking" and snap.awake_queue == 0):
            # System is healthy, no need to keep thinking
            pass  # Mode switching handled by awake engine itself
    
    def _record_error(self, error_msg: str):
        """Record an error for circuit breaker tracking"""
        self._error_window.append(1)
    
    # === Public API ===
    
    def get_current(self) -> dict:
        """Get current brain snapshot as dict"""
        return self.current.to_dict()
    
    def get_history(self, last_n: int = 60) -> List[dict]:
        """Get time-series history for charting"""
        recent = list(self.history)[-last_n:]
        return [s.to_dict() for s in recent]
    
    def get_time_series(self, metric: str, last_n: int = 60) -> List[dict]:
        """Get a single metric as time-series [{tick, value}]"""
        recent = list(self.history)[-last_n:]
        return [{"tick": s.tick, "value": getattr(s, metric, 0)} for s in recent]
    
    def get_health(self) -> dict:
        """Overall brain health summary"""
        return {
            "uptime_seconds": time.time() - self.start_time,
            "total_ticks": self.tick_count,
            "error_rate": round(self.error_rate, 2),
            "halted": self.halted,
            "halt_reason": self.halt_reason,
            "registered_components": list(self._components.keys()),
        }
