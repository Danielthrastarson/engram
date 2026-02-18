# reasoning/rhythms.py
# Change 4: Polyrhythmic Processing
# The brain runs multiple concurrent oscillations at different frequencies
# Each subsystem has its own rhythm, coupled through the 1 Hz Heartbeat

import time
import threading
import logging
from typing import Dict, Callable, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class BrainRhythm:
    """A single oscillatory rhythm for one subsystem"""
    name: str
    base_hz: float           # Default frequency
    current_hz: float = 0.0  # Active frequency (can be modulated)
    min_hz: float = 0.1
    max_hz: float = 60.0
    active: bool = False
    cycle_count: int = 0
    last_tick: float = field(default_factory=time.time)
    damping: float = 0.1     # Max Hz change per tick (prevents oscillation)
    
    def __post_init__(self):
        self.current_hz = self.base_hz
    
    def modulate(self, target_hz: float):
        """Change Hz with damping (max ±10% per tick to prevent oscillation)"""
        target_hz = max(self.min_hz, min(self.max_hz, target_hz))
        delta = target_hz - self.current_hz
        max_delta = self.current_hz * self.damping
        
        if abs(delta) > max_delta:
            delta = max_delta if delta > 0 else -max_delta
        
        self.current_hz = max(self.min_hz, self.current_hz + delta)
    
    def get_interval(self) -> float:
        """Get sleep interval in seconds"""
        if self.current_hz <= 0:
            return float('inf')
        return 1.0 / self.current_hz


class BrainRhythms:
    """
    Polyrhythmic processing manager.
    
    Instead of one global Hz knob, each subsystem has its own rhythm:
    
    | Rhythm       | Default Hz | Brain Equivalent | Purpose                    |
    |------------- |----------- |----------------- |--------------------------- |
    | heartbeat    | 1.0        | Slow cortical    | Master clock, coordination |
    | gate         | 2.0        | Alpha (8-12 Hz)  | Input filtering            |
    | retrieval    | 10.0       | Beta (12-30 Hz)  | Fast pattern matching      |
    | reasoning    | 2.0        | Theta (4-8 Hz)   | Deliberate reasoning       |
    | consolidation| 0.2        | Delta (0.5-4 Hz) | Background cleanup         |
    | dreaming     | 0.01       | Sleep spindles   | Creative replay            |
    
    The Heartbeat (1 Hz) acts as the master clock that coordinates
    all faster rhythms through cross-frequency coupling.
    """
    
    # Default rhythms
    DEFAULTS = {
        "heartbeat":     BrainRhythm(name="heartbeat",     base_hz=1.0,  min_hz=0.5,  max_hz=2.0),
        "gate":          BrainRhythm(name="gate",           base_hz=2.0,  min_hz=0.5,  max_hz=10.0),
        "retrieval":     BrainRhythm(name="retrieval",      base_hz=10.0, min_hz=1.0,  max_hz=30.0),
        "reasoning":     BrainRhythm(name="reasoning",      base_hz=2.0,  min_hz=0.5,  max_hz=15.0),
        "consolidation": BrainRhythm(name="consolidation",  base_hz=0.2,  min_hz=0.05, max_hz=2.0),
        "dreaming":      BrainRhythm(name="dreaming",       base_hz=0.01, min_hz=0.001,max_hz=0.5),
    }
    
    def __init__(self):
        self.rhythms: Dict[str, BrainRhythm] = {}
        self._threads: Dict[str, threading.Thread] = {}
        self._callbacks: Dict[str, Callable] = {}
        self.running = False
        
        # Initialize with defaults
        for name, rhythm in self.DEFAULTS.items():
            self.rhythms[name] = BrainRhythm(
                name=rhythm.name,
                base_hz=rhythm.base_hz,
                min_hz=rhythm.min_hz,
                max_hz=rhythm.max_hz,
            )
    
    def register_callback(self, rhythm_name: str, callback: Callable):
        """Register a function to call on each tick of a rhythm"""
        if rhythm_name in self.rhythms:
            self._callbacks[rhythm_name] = callback
    
    def start(self):
        """Start all rhythms as separate threads"""
        self.running = True
        
        for name, rhythm in self.rhythms.items():
            if name in self._callbacks:
                rhythm.active = True
                thread = threading.Thread(
                    target=self._rhythm_loop,
                    args=(name,),
                    daemon=True,
                    name=f"Rhythm-{name}"
                )
                self._threads[name] = thread
                thread.start()
                logger.info(f"🎵 Rhythm started: {name} @ {rhythm.current_hz:.2f} Hz")
    
    def stop(self):
        """Stop all rhythms"""
        self.running = False
        for name, rhythm in self.rhythms.items():
            rhythm.active = False
        logger.info("🎵 All rhythms stopped")
    
    def modulate(self, rhythm_name: str, target_hz: float):
        """Modulate a specific rhythm's frequency (with damping)"""
        if rhythm_name in self.rhythms:
            self.rhythms[rhythm_name].modulate(target_hz)
    
    def get_status(self) -> Dict[str, dict]:
        """Get status of all rhythms"""
        return {
            name: {
                "hz": r.current_hz,
                "base_hz": r.base_hz,
                "active": r.active,
                "cycles": r.cycle_count,
            }
            for name, r in self.rhythms.items()
        }
    
    def _rhythm_loop(self, rhythm_name: str):
        """Main loop for a single rhythm"""
        rhythm = self.rhythms[rhythm_name]
        callback = self._callbacks[rhythm_name]
        
        while self.running and rhythm.active:
            try:
                start = time.time()
                callback()
                rhythm.cycle_count += 1
                rhythm.last_tick = time.time()
                
                # Sleep for the remainder of the interval
                elapsed = time.time() - start
                interval = rhythm.get_interval()
                sleep_time = max(0.01, interval - elapsed)
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Rhythm {rhythm_name} error: {e}")
                time.sleep(1)  # Backoff on error
