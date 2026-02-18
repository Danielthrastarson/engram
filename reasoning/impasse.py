# reasoning/impasse.py
# Change 2: Impasse Detection + Sub-Goal Generation
# Based on SOAR's impasse mechanism: when stuck, figure out WHY and learn

import logging
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from collections import deque
from enum import Enum

logger = logging.getLogger(__name__)


class ImpasseType(Enum):
    """Types of impasses the system can encounter"""
    NO_AXIOMS = "no_axioms"           # Domain lacks axioms for proof
    LOW_CONFIDENCE = "low_confidence" # All answers have low confidence
    CONTRADICTION = "contradiction"   # Evidence contradicts itself
    NO_ENGRAMS = "no_engrams"         # No relevant memories found
    PROOF_FAILED = "proof_failed"     # Formal proof could not be completed
    GATE_REJECTED = "gate_rejected"   # Translator Gate couldn't clean input


@dataclass
class Impasse:
    """
    A formal 'I'm stuck' state that spawns a sub-goal.
    
    In SOAR, an impasse occurs when no production rule fires.
    Here, it occurs when confidence is too low or processing fails.
    The impasse automatically generates a sub-goal describing
    WHAT needs to be learned to resolve it.
    """
    id: str = ""
    original_query: str = ""
    impasse_type: ImpasseType = ImpasseType.LOW_CONFIDENCE
    failure_reason: str = ""
    sub_goal: str = ""              # What needs to happen
    domain: str = "general"
    priority: float = 0.5           # How urgently this needs resolution
    created_at: float = field(default_factory=time.time)
    resolved: bool = False
    resolved_at: Optional[float] = None
    resolution: Optional[str] = None
    attempts: int = 0
    max_attempts: int = 5
    
    def __post_init__(self):
        if not self.id:
            self.id = f"imp_{int(self.created_at)}_{hash(self.original_query) % 10000}"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.impasse_type.value,
            "query": self.original_query[:100],
            "sub_goal": self.sub_goal,
            "domain": self.domain,
            "priority": self.priority,
            "resolved": self.resolved,
            "attempts": self.attempts,
            "age_seconds": time.time() - self.created_at,
        }


class ImpasseDetector:
    """
    Detects when the system is stuck and generates sub-goals.
    
    The key insight from SOAR: failure is not just "lower the confidence."
    Failure should generate a TYPED reason and a SPECIFIC sub-goal
    that tells the Seeking Drive or Awake Engine what to do next.
    
    Instead of: "proof failed → confidence - 0.2 → move on"
    We get:     "proof failed → no axioms in physics → sub-goal: acquire physics axioms"
    
    This turns failure into directed learning.
    """
    
    def __init__(self):
        # Active impasses (unresolved)
        self.active: List[Impasse] = []
        
        # Resolved impasses (history)
        self.resolved_history: deque = deque(maxlen=100)
        
        # Stats
        self.total_created = 0
        self.total_resolved = 0
    
    def detect(self, query: str, context: Dict[str, Any]) -> Optional[Impasse]:
        """
        Analyze a processing result and detect if an impasse occurred.
        
        Args:
            query: The original query
            context: Dict with keys like:
                - confidence: float
                - proof_result: dict (from reasoning engine)
                - engrams_found: int
                - gate_confidence: float
                - error: str
        """
        confidence = context.get("confidence", 1.0)
        proof = context.get("proof_result", {})
        engrams_found = context.get("engrams_found", 1)
        gate_confidence = context.get("gate_confidence", 1.0)
        error = context.get("error", "")
        
        impasse = None
        
        # Check: Gate couldn't parse input
        if gate_confidence < 0.4:
            impasse = Impasse(
                original_query=query,
                impasse_type=ImpasseType.GATE_REJECTED,
                failure_reason=f"Input too noisy (gate confidence: {gate_confidence:.2f})",
                sub_goal="Expand translator vocabulary or ask user to rephrase",
                priority=0.3,
            )
        
        # Check: No relevant memories
        elif engrams_found == 0:
            domain = self._infer_domain(query)
            impasse = Impasse(
                original_query=query,
                impasse_type=ImpasseType.NO_ENGRAMS,
                failure_reason="No relevant engrams found for this query",
                sub_goal=f"Acquire knowledge in domain: {domain}",
                domain=domain,
                priority=0.7,
            )
        
        # Check: Proof attempted but failed
        elif proof.get("proven") == False:
            domain = proof.get("domain", self._infer_domain(query))
            proof_error = proof.get("error", "unknown")
            
            if "no axioms" in str(proof_error).lower() or proof.get("axioms_used", []) == []:
                impasse = Impasse(
                    original_query=query,
                    impasse_type=ImpasseType.NO_AXIOMS,
                    failure_reason=f"No axioms available in domain: {domain}",
                    sub_goal=f"Seed axioms for domain: {domain}",
                    domain=domain,
                    priority=0.8,
                )
            else:
                impasse = Impasse(
                    original_query=query,
                    impasse_type=ImpasseType.PROOF_FAILED,
                    failure_reason=f"Proof failed: {proof_error}",
                    sub_goal=f"Strengthen reasoning in domain: {domain}",
                    domain=domain,
                    priority=0.6,
                )
        
        # Check: Very low confidence overall
        elif confidence < 0.3:
            domain = self._infer_domain(query)
            impasse = Impasse(
                original_query=query,
                impasse_type=ImpasseType.LOW_CONFIDENCE,
                failure_reason=f"All paths produced low confidence ({confidence:.2f})",
                sub_goal=f"Improve coverage in domain: {domain}",
                domain=domain,
                priority=0.5,
            )
        
        if impasse:
            # Check for duplicate impasses (same type + domain within last hour)
            if not self._is_duplicate(impasse):
                self.active.append(impasse)
                self.total_created += 1
                logger.info(f"🚧 IMPASSE: {impasse.impasse_type.value} — "
                            f"sub-goal: {impasse.sub_goal}")
            else:
                # Increment attempts on existing
                existing = self._find_duplicate(impasse)
                if existing:
                    existing.attempts += 1
                    existing.priority = min(1.0, existing.priority + 0.1)
        
        return impasse
    
    def resolve(self, impasse_id: str, resolution: str):
        """Mark an impasse as resolved"""
        for imp in self.active:
            if imp.id == impasse_id:
                imp.resolved = True
                imp.resolved_at = time.time()
                imp.resolution = resolution
                self.active.remove(imp)
                self.resolved_history.append(imp)
                self.total_resolved += 1
                logger.info(f"✅ Impasse resolved: {imp.impasse_type.value} — {resolution}")
                return
    
    def get_active_by_priority(self) -> List[Impasse]:
        """Get active impasses sorted by priority (highest first)"""
        return sorted(self.active, key=lambda i: i.priority, reverse=True)
    
    def get_active_by_domain(self, domain: str) -> List[Impasse]:
        """Get active impasses for a specific domain"""
        return [i for i in self.active if i.domain == domain]
    
    def get_unresolved_queries(self, hours: int = 24) -> List[str]:
        """Get queries from recent unresolved impasses (for dream replay)"""
        cutoff = time.time() - hours * 3600
        return [
            i.original_query for i in self.active
            if i.created_at > cutoff and not i.resolved
        ]
    
    def get_stats(self) -> dict:
        return {
            "active_impasses": len(self.active),
            "total_created": self.total_created,
            "total_resolved": self.total_resolved,
            "resolution_rate": (
                self.total_resolved / max(self.total_created, 1)
            ),
            "by_type": self._count_by_type(),
        }
    
    def prune_stale(self, max_age_hours: int = 48):
        """Remove impasses that are too old or exceeded max attempts"""
        cutoff = time.time() - max_age_hours * 3600
        stale = [i for i in self.active 
                 if i.created_at < cutoff or i.attempts >= i.max_attempts]
        for imp in stale:
            imp.resolved = True
            imp.resolution = "pruned_stale"
            self.active.remove(imp)
            self.resolved_history.append(imp)
    
    # === Internal ===
    
    def _infer_domain(self, query: str) -> str:
        """Infer domain from query keywords"""
        q = query.lower()
        domains = {
            "physics": ["force", "mass", "energy", "velocity", "acceleration", "gravity", "quantum"],
            "mathematics": ["equation", "number", "sum", "integral", "derivative", "function", "proof"],
            "logic": ["implies", "therefore", "if then", "contradiction", "syllogism"],
            "biology": ["cell", "dna", "gene", "organism", "evolution", "protein"],
            "philosophy": ["consciousness", "existence", "epistemology", "ontology", "ethics"],
            "computer_science": ["algorithm", "data structure", "complexity", "program", "code"],
        }
        for domain, keywords in domains.items():
            if any(kw in q for kw in keywords):
                return domain
        return "general"
    
    def _is_duplicate(self, impasse: Impasse) -> bool:
        """Check if a similar impasse already exists"""
        cutoff = time.time() - 3600  # Within last hour
        for existing in self.active:
            if (existing.impasse_type == impasse.impasse_type 
                and existing.domain == impasse.domain
                and existing.created_at > cutoff):
                return True
        return False
    
    def _find_duplicate(self, impasse: Impasse) -> Optional[Impasse]:
        for existing in self.active:
            if (existing.impasse_type == impasse.impasse_type 
                and existing.domain == impasse.domain):
                return existing
        return None
    
    def _count_by_type(self) -> dict:
        counts = {}
        for imp in self.active:
            t = imp.impasse_type.value
            counts[t] = counts.get(t, 0) + 1
        return counts
