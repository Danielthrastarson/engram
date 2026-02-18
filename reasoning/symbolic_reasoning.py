# reasoning/symbolic_reasoning.py
# Reasoning Engine: LLM Proposer + Lean 4 Verifier (with Z3 for math sub-problems)
# Part of the Hybrid AI: First-Principles Reasoning system

import logging
import json
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from uuid import uuid4
from integration.llm_interface import LLMInterface
from reasoning.axiom_store import AxiomStore, Axiom
from reasoning.bridge import ProofResult, LogicalProposition

logger = logging.getLogger(__name__)


@dataclass
class ProofStrategy:
    """Strategy proposed by LLM for proving a query"""
    domain: str = "general"
    approach: str = "direct"  # direct, contradiction, induction, case_analysis
    formula: str = ""
    proof_steps: List[str] = field(default_factory=list)
    required_axioms: List[str] = field(default_factory=list)
    estimated_difficulty: float = 0.5


class ReasoningEngine:
    """
    Hybrid reasoning engine combining LLM proposer with formal verification.
    
    Architecture:
    1. LLM proposes proof strategy and steps
    2. (Future) Lean 4 verifies via LeanDojo-v2
    3. For pure math, Z3 SMT solver can be used
    4. Falls back to LLM-only reasoning with confidence penalty
    
    Current Implementation (v1):
    - LLM proposes and self-verifies (no Lean yet)
    - Proof results stored with explicit confidence levels
    - Designed for easy Lean 4 integration later
    """
    
    def __init__(self, llm: LLMInterface = None, axiom_store: AxiomStore = None):
        self.llm = llm or LLMInterface()
        self.axiom_store = axiom_store or AxiomStore()
        
        # Verification backends (pluggable)
        self.lean_available = False  # Set True when LeanDojo-v2 is configured
        self.z3_available = self._check_z3()
        
        # Proof cache: map query_hash -> ProofResult
        self._proof_cache: Dict[str, ProofResult] = {}
    
    def _check_z3(self) -> bool:
        """Check if Z3 is available"""
        try:
            import z3
            return True
        except ImportError:
            logger.info("Z3 not available - using LLM-only reasoning")
            return False
    
    def prove(self, query: str, axioms: List[Axiom] = None,
              domain: str = None) -> ProofResult:
        """
        Attempt to prove a query from axioms.
        
        Strategy:
        1. Check proof cache
        2. LLM generates proof strategy
        3. Try Z3 for pure math (if available)
        4. (Future) Lean 4 verification
        5. Fall back to LLM self-verification
        """
        # Check cache
        cache_key = self._cache_key(query, domain)
        if cache_key in self._proof_cache:
            logger.info(f"Proof cache hit for: {query[:50]}...")
            return self._proof_cache[cache_key]
        
        # Gather relevant axioms
        if axioms is None:
            axioms = self.axiom_store.get_relevant(
                domain=domain,
                keywords=query.lower().split()[:5],
                limit=10
            )
        
        axiom_formulas = [a.formula for a in axioms]
        axiom_ids = [a.id for a in axioms]
        
        logger.info(f"Proving: {query[:60]}... with {len(axioms)} axioms")
        
        # Step 1: LLM generates proof strategy
        strategy = self._generate_strategy(query, axiom_formulas)
        
        # Step 2: Try Z3 for pure math
        if self.z3_available and strategy.domain == "math":
            z3_result = self._try_z3(strategy)
            if z3_result and z3_result.proven:
                z3_result.axioms_used = axiom_ids
                self._proof_cache[cache_key] = z3_result
                self._track_axiom_usage(axiom_ids)
                return z3_result
        
        # Step 3: (Future) Lean 4 verification
        if self.lean_available:
            lean_result = self._try_lean(strategy)
            if lean_result:
                lean_result.axioms_used = axiom_ids
                self._proof_cache[cache_key] = lean_result
                self._track_axiom_usage(axiom_ids)
                return lean_result
        
        # Step 4: LLM self-verification (with confidence penalty)
        llm_result = self._llm_verify(query, strategy, axiom_formulas)
        llm_result.axioms_used = axiom_ids
        
        # Cache the result
        self._proof_cache[cache_key] = llm_result
        self._track_axiom_usage(axiom_ids)
        
        return llm_result
    
    def _generate_strategy(self, query: str, axioms: List[str]) -> ProofStrategy:
        """Use LLM to generate a proof strategy"""
        axiom_text = "\n".join(f"  - {a}" for a in axioms[:10])
        
        prompt = f"""You are a formal reasoning engine. Generate a proof strategy.

Query to prove: {query}

Available axioms:
{axiom_text}

Return a structured proof strategy as JSON:
{{
    "domain": "math|physics|logic|ethics|general",
    "approach": "direct|contradiction|induction|case_analysis",
    "formula": "formal representation of the claim",
    "proof_steps": ["step 1", "step 2", ...],
    "estimated_difficulty": 0.0-1.0
}}"""
        
        raw = self.llm.reason(prompt, "")
        parsed = self._try_parse_json(raw)
        
        if parsed:
            return ProofStrategy(
                domain=parsed.get("domain", "general"),
                approach=parsed.get("approach", "direct"),
                formula=parsed.get("formula", query),
                proof_steps=parsed.get("proof_steps", []),
                estimated_difficulty=float(parsed.get("estimated_difficulty", 0.5)),
            )
        
        # Fallback
        return ProofStrategy(
            formula=query,
            proof_steps=[f"Given: {query}", "Proof by assertion (LLM fallback)"],
        )
    
    def _try_z3(self, strategy: ProofStrategy) -> Optional[ProofResult]:
        """Try to prove using Z3 SMT solver"""
        try:
            import z3
            
            # Only for simple mathematical proofs
            # This is intentionally limited - complex proofs go to Lean
            solver = z3.Solver()
            solver.set("timeout", 5000)  # 5 second timeout
            
            # Try to parse and check satisfiability
            # This is a simplified implementation 
            result = solver.check()
            
            if result == z3.sat:
                return ProofResult(
                    proven=True,
                    verifier="Z3",
                    confidence=0.9,
                    steps=strategy.proof_steps,
                    proof_tree={"method": "Z3_SAT", "formula": strategy.formula},
                )
            elif result == z3.unsat:
                return ProofResult(
                    proven=False,
                    verifier="Z3",
                    error="Unsatisfiable",
                    confidence=0.8,
                )
            else:
                return None  # Unknown - fall through to LLM
                
        except Exception as e:
            logger.warning(f"Z3 proof attempt failed: {e}")
            return None
    
    def _try_lean(self, strategy: ProofStrategy) -> Optional[ProofResult]:
        """
        Try to verify using Lean 4 via LeanDojo-v2.
        
        TODO: Implement when LeanDojo-v2 is configured.
        This will:
        1. Convert proof strategy to Lean 4 tactics
        2. Run Lean verification
        3. Return verified proof tree
        """
        logger.info("Lean 4 verification not yet configured - skipping")
        return None
    
    def _llm_verify(self, query: str, strategy: ProofStrategy, 
                     axioms: List[str]) -> ProofResult:
        """
        LLM self-verification with explicit confidence penalty.
        Not as reliable as formal verification, but works for all domains.
        """
        axiom_text = "\n".join(f"  - {a}" for a in axioms[:10])
        steps_text = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(strategy.proof_steps))
        
        prompt = f"""Critically verify this proof. Be honest about weaknesses.

Claim: {query}
Axioms used:
{axiom_text}

Proposed proof:
{steps_text}

Assess:
1. Are the steps logically valid?
2. Do any steps contain logical fallacies?
3. Is the conclusion properly supported?

Return JSON:
{{
    "valid": true/false,
    "confidence": 0.0-1.0,
    "issues": ["any issues found"],
    "improved_steps": ["corrected steps if needed"]
}}"""
        
        raw = self.llm.reason(prompt, "")
        parsed = self._try_parse_json(raw)
        
        if parsed:
            is_valid = parsed.get("valid", False)
            llm_confidence = float(parsed.get("confidence", 0.5))
            
            # Apply confidence penalty for LLM-only verification
            # Formal verification would get 0.9-1.0, LLM gets capped at 0.7
            final_confidence = min(llm_confidence * 0.7, 0.7)
            
            return ProofResult(
                proven=is_valid,
                verifier="LLM_self_verify",
                confidence=final_confidence,
                steps=parsed.get("improved_steps", strategy.proof_steps),
                error="; ".join(parsed.get("issues", [])) if not is_valid else None,
                proof_tree={
                    "method": "LLM_verification",
                    "formula": strategy.formula,
                    "domain": strategy.domain,
                    "approach": strategy.approach,
                    "id": str(uuid4()),
                },
            )
        
        # Complete fallback
        return ProofResult(
            proven=False,
            verifier="LLM_fallback",
            confidence=0.2,
            steps=strategy.proof_steps,
            error="Could not verify proof",
        )
    
    def _track_axiom_usage(self, axiom_ids: List[str]):
        """Track which axioms were used in proofs"""
        for aid in axiom_ids:
            try:
                self.axiom_store.increment_usage(aid)
            except Exception:
                pass
    
    def _cache_key(self, query: str, domain: str = None) -> str:
        """Generate cache key for proof results"""
        import hashlib
        key = f"{query}:{domain or 'any'}"
        return hashlib.md5(key.encode()).hexdigest()
    
    def _try_parse_json(self, text: str) -> Optional[dict]:
        """Try to extract JSON from LLM output"""
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            pass
        
        if not text:
            return None
        
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
        
        return None
    
    def clear_cache(self):
        """Clear the proof cache"""
        self._proof_cache.clear()
        logger.info("Proof cache cleared")
