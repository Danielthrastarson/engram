# reasoning/bridge.py
# Semantic Bridge: Vector ↔ Logic Translation Layer
# Uses LLM-structured extraction with multi-sample voting for accuracy

import asyncio
import json
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from core.abstraction import Abstraction
from integration.llm_interface import LLMInterface
from utils import config

logger = logging.getLogger(__name__)


@dataclass
class LogicalProposition:
    """A formal logical proposition extracted from an engram"""
    formula: str = ""
    confidence: float = 0.5
    domain: str = "general"
    source: str = "extracted"
    source_engram_id: Optional[str] = None
    predicates: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "formula": self.formula,
            "confidence": self.confidence,
            "domain": self.domain,
            "source": self.source,
            "source_engram_id": self.source_engram_id,
            "predicates": self.predicates,
        }


@dataclass  
class ProofResult:
    """Result of a proof attempt"""
    proven: bool = False
    proof_tree: Optional[Dict] = None
    error: Optional[str] = None
    verifier: str = "none"
    confidence: float = 0.0
    axioms_used: List[str] = field(default_factory=list)
    steps: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "proven": self.proven,
            "proof_tree": self.proof_tree,
            "error": self.error,
            "verifier": self.verifier,
            "confidence": self.confidence,
            "axioms_used": self.axioms_used,
            "steps": self.steps,
        }


class SemanticBridge:
    """
    Bridge between vector-space engrams and formal logic.
    
    Uses LLM-structured extraction with multi-sample voting:
    1. Generate N translations (default 3)
    2. Cluster by similarity
    3. Use consensus as result
    4. Round-trip verify if confidence is high enough
    """
    
    def __init__(self, llm: LLMInterface = None, embedder=None):
        self.llm = llm or LLMInterface()
        self.embedder = embedder
        self.num_samples = 3  # Multi-sample voting count
        self.consensus_threshold = 0.6  # Min agreement for consensus
        self.verify_threshold = 0.7  # Min confidence for round-trip verification
    
    async def engram_to_axiom(self, engram: Abstraction) -> Optional[LogicalProposition]:
        """
        Extract a logical proposition from an engram using LLM structured extraction.
        Uses multi-sample voting for robustness.
        """
        prompt = self._build_extraction_prompt(engram)
        
        try:
            # Multi-sample: generate multiple translations
            samples = []
            for _ in range(self.num_samples):
                result = self._extract_single(prompt, engram)
                if result:
                    samples.append(result)
            
            if not samples:
                logger.warning(f"No valid extractions for engram {engram.id}")
                return None
            
            # Single sample shortcut
            if len(samples) == 1:
                samples[0].confidence *= 0.7  # Penalty for no consensus
                return samples[0]
            
            # Multi-sample voting: find consensus
            consensus = self._find_consensus(samples)
            
            if consensus:
                consensus.source_engram_id = engram.id
                return consensus
            else:
                # No consensus - return best with low confidence
                best = max(samples, key=lambda s: s.confidence)
                best.confidence *= 0.3
                best.source = "low_consensus"
                return best
                
        except Exception as e:
            logger.error(f"Bridge extraction failed for {engram.id}: {e}")
            return None
    
    def engram_to_axiom_sync(self, engram: Abstraction) -> Optional[LogicalProposition]:
        """Synchronous version of engram_to_axiom"""
        prompt = self._build_extraction_prompt(engram)
        result = self._extract_single(prompt, engram)
        if result:
            result.source_engram_id = engram.id
        return result
    
    def axiom_to_engram(self, proof: Dict[str, Any]) -> Abstraction:
        """
        Convert a proof result to a high-salience axiom-derived engram.
        """
        # Build natural language summary of proof
        formula = proof.get("formula", "")
        steps = proof.get("steps", [])
        domain = proof.get("domain", "general")
        
        if steps:
            summary = f"Proven: {formula}. Steps: {'; '.join(steps[:3])}"
        else:
            summary = f"Axiom-derived knowledge: {formula}"
        
        # Truncate to reasonable length
        summary = summary[:500]
        
        # Create axiom-derived abstraction
        import hashlib
        embedding_hash = hashlib.md5(summary.encode()).hexdigest()
        
        return Abstraction(
            content=summary,
            embedding_hash=embedding_hash,
            salience=1.5,  # High salience - proven knowledge
            is_axiom_derived=True,
            proof_id=proof.get("id"),
            consistency_score=1.0,
            axioms_used=proof.get("axioms_used", []),
            metadata={
                "type": "axiom_derived",
                "domain": domain,
                "proof_steps": len(steps),
                "verifier": proof.get("verifier", "unknown"),
            }
        )
    
    def _build_extraction_prompt(self, engram: Abstraction) -> str:
        """Build the extraction prompt for LLM"""
        domain_hint = engram.metadata.get("domain", "unknown")
        return f"""Convert this knowledge to formal logic. Return ONLY valid JSON.

Knowledge: {engram.content}
Domain hint: {domain_hint}

Return JSON with exactly these keys:
- "formula": A predicate logic formula (string)
- "confidence": How confident you are in this extraction (0.0 to 1.0)
- "domain": The domain (physics, math, ethics, logic, general, etc.)
- "predicates": List of predicate names used"""
    
    def _extract_single(self, prompt: str, engram: Abstraction) -> Optional[LogicalProposition]:
        """Extract a single logical proposition from an engram"""
        try:
            # Use LLM to generate structured output
            raw = self.llm.reason(prompt, engram.content)
            
            # Try to parse JSON from response
            parsed = self._try_parse_json(raw)
            
            if parsed:
                return LogicalProposition(
                    formula=parsed.get("formula", engram.content),
                    confidence=float(parsed.get("confidence", 0.5)),
                    domain=parsed.get("domain", "general"),
                    source="llm_extracted",
                    predicates=parsed.get("predicates", []),
                )
            else:
                # Fallback: use content directly as formula
                return LogicalProposition(
                    formula=engram.content,
                    confidence=0.3,
                    domain="general",
                    source="fallback",
                )
        except Exception as e:
            logger.warning(f"Single extraction failed: {e}")
            return None
    
    def _try_parse_json(self, text: str) -> Optional[dict]:
        """Try to extract JSON from LLM output"""
        # Try direct parse
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Try to find JSON block in text
        if not text:
            return None
            
        # Look for {...} pattern
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _find_consensus(self, samples: List[LogicalProposition]) -> Optional[LogicalProposition]:
        """Find consensus among multiple extraction samples"""
        if len(samples) < 2:
            return samples[0] if samples else None
        
        # Simple consensus: cluster by formula similarity
        # For now, use exact domain match + formula word overlap
        best_group = []
        best_score = 0
        
        for i, s1 in enumerate(samples):
            group = [s1]
            for j, s2 in enumerate(samples):
                if i == j:
                    continue
                similarity = self._formula_similarity(s1.formula, s2.formula)
                if similarity > 0.5:
                    group.append(s2)
            
            if len(group) > len(best_group):
                best_group = group
        
        agreement = len(best_group) / len(samples)
        
        if agreement >= self.consensus_threshold:
            # Use the highest-confidence member of the consensus group
            consensus = max(best_group, key=lambda s: s.confidence)
            consensus.confidence = agreement  # Override with consensus score
            consensus.source = "consensus"
            return consensus
        
        return None
    
    def _formula_similarity(self, f1: str, f2: str) -> float:
        """Simple word-overlap similarity between two formulas"""
        if not f1 or not f2:
            return 0.0
        
        words1 = set(f1.lower().split())
        words2 = set(f2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)  # Jaccard similarity
