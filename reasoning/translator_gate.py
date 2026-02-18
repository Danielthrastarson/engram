# reasoning/translator_gate.py
# Layer 0: Secure Translator Gate
# Multi-translator ensemble with Truth Guard for noise filtering
# Ensures clean input before it reaches memory or reasoning engines

import logging
import hashlib
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from core.truth_guard import TruthGuard
from integration.llm_interface import LLMInterface

logger = logging.getLogger(__name__)


@dataclass
class FilteredInput:
    """Result of input filtering through Layer 0"""
    content: str = ""
    original: str = ""
    confidence: float = 1.0
    is_clean: bool = False
    needs_clarification: bool = False
    truth_guard_flagged: bool = False
    risk_score: float = 0.0
    noise_warning: Optional[str] = None
    translations: List[str] = field(default_factory=list)
    consensus_agreement: float = 1.0
    
    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "confidence": self.confidence,
            "is_clean": self.is_clean,
            "needs_clarification": self.needs_clarification,
            "truth_guard_flagged": self.truth_guard_flagged,
            "risk_score": self.risk_score,
            "consensus_agreement": self.consensus_agreement,
        }


class SecureTranslatorGate:
    """
    Layer 0: Multi-translator ensemble with noise filtering.
    
    Pipeline:
    1. Parallel translation by N translators (different prompts/configs)
    2. Consensus voting via similarity clustering
    3. Truth Guard safety check
    4. Output clean, confidence-scored input
    
    This prevents noisy/ambiguous/adversarial input from polluting
    the engram memory or corrupting reasoning chains.
    """
    
    def __init__(self, llm: LLMInterface = None, 
                 num_translators: int = 3,
                 min_agreement: float = 0.6):
        self.llm = llm or LLMInterface()
        self.num_translators = num_translators
        self.min_agreement = min_agreement
        
        # Translation prompt variants for diversity (7-translator ensemble)
        self.prompt_variants = [
            self._variant_concise,
            self._variant_precise,
            self._variant_structured,
            self._variant_semantic,
            self._variant_inferential,
            self._variant_decomposed,
            self._variant_adversarial,
        ]
        
        # Cache to avoid re-processing identical inputs
        self._cache: Dict[str, FilteredInput] = {}
        self._cache_max = 200
    
    def filter_input(self, raw_input: str) -> FilteredInput:
        """
        Run input through the Secure Translator Gate.
        
        Returns FilteredInput with confidence score and clean content.
        """
        if not raw_input or not raw_input.strip():
            return FilteredInput(
                content="",
                original=raw_input,
                confidence=0.0,
                needs_clarification=True,
                noise_warning="Empty input received"
            )
        
        # Check cache
        cache_key = hashlib.md5(raw_input.encode()).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Step 1: Generate translations
        translations = self._generate_translations(raw_input)
        
        if not translations:
            return FilteredInput(
                content=raw_input,
                original=raw_input,
                confidence=0.3,
                noise_warning="Translation failed - using raw input"
            )
        
        # Step 2: Compute consensus
        consensus_content, agreement = self._compute_consensus(translations)
        
        if agreement < self.min_agreement:
            result = FilteredInput(
                content=raw_input,
                original=raw_input,
                confidence=agreement,
                needs_clarification=True,
                noise_warning=f"Low consensus ({agreement:.0%}) - input may be ambiguous",
                translations=translations,
                consensus_agreement=agreement,
            )
            self._cache_result(cache_key, result)
            return result
        
        # Step 3: Truth Guard check
        risk_score = self._truth_guard_check(consensus_content)
        
        if risk_score > 0.6:
            result = FilteredInput(
                content=consensus_content,
                original=raw_input,
                confidence=agreement * 0.5,
                truth_guard_flagged=True,
                risk_score=risk_score,
                translations=translations,
                consensus_agreement=agreement,
            )
            self._cache_result(cache_key, result)
            return result
        
        # Step 4: Clean result
        result = FilteredInput(
            content=consensus_content,
            original=raw_input,
            confidence=agreement,
            is_clean=True,
            risk_score=risk_score,
            translations=translations,
            consensus_agreement=agreement,
        )
        self._cache_result(cache_key, result)
        return result
    
    def _generate_translations(self, raw_input: str) -> List[str]:
        """Generate N translations of the input for voting"""
        translations = []
        
        for i in range(min(self.num_translators, len(self.prompt_variants))):
            try:
                prompt = self.prompt_variants[i](raw_input)
                result = self.llm.reason(prompt, raw_input)
                
                if result and result.strip():
                    translations.append(result.strip())
            except Exception as e:
                logger.warning(f"Translation variant {i} failed: {e}")
        
        # Always include raw input as a baseline
        if raw_input.strip() not in translations:
            translations.append(raw_input.strip())
        
        return translations
    
    def _compute_consensus(self, translations: List[str]) -> tuple:
        """
        Find consensus among translations using word-overlap similarity.
        Returns (consensus_content, agreement_score).
        """
        if len(translations) <= 1:
            return translations[0] if translations else "", 1.0
        
        # Score each translation against all others
        scores = []
        for i, t1 in enumerate(translations):
            avg_sim = 0.0
            for j, t2 in enumerate(translations):
                if i != j:
                    avg_sim += self._text_similarity(t1, t2)
            avg_sim /= max(len(translations) - 1, 1)
            scores.append((avg_sim, i))
        
        # Best translation = highest average similarity to others
        scores.sort(reverse=True)
        best_idx = scores[0][1]
        agreement = scores[0][0]
        
        return translations[best_idx], agreement
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Jaccard similarity between two texts"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def _truth_guard_check(self, content: str) -> float:
        """Run Truth Guard on the filtered content"""
        try:
            from core.abstraction import Abstraction
            # Create a temporary abstraction to check
            temp = Abstraction(
                content=content,
                embedding_hash="temp",
                quality_score=0.5,
            )
            risk, _ = TruthGuard.calculate_risk([temp])
            return risk
        except Exception as e:
            logger.warning(f"Truth Guard check failed: {e}")
            return 0.0
    
    def _cache_result(self, key: str, result: FilteredInput):
        """Cache result with size limit"""
        if len(self._cache) >= self._cache_max:
            # Evict oldest (simple FIFO)
            oldest = next(iter(self._cache))
            del self._cache[oldest]
        self._cache[key] = result
    
    # === Translation Prompt Variants ===
    
    def _variant_concise(self, raw: str) -> str:
        return f"""Clean and clarify this input. Remove noise, fix grammar, 
preserve core meaning. Return ONLY the cleaned text, nothing else.

Input: {raw}"""
    
    def _variant_precise(self, raw: str) -> str:
        return f"""Parse this input with maximum precision. 
Extract the core question or statement. Remove ambiguity.
Return ONLY the precise, unambiguous version.

Input: {raw}"""
    
    def _variant_structured(self, raw: str) -> str:
        return f"""Normalize this input into a clear, well-formed statement or question.
Ensure it is grammatically correct and unambiguous.
Return ONLY the normalized text.

Input: {raw}"""
    
    def _variant_semantic(self, raw: str) -> str:
        return f"""Identify the core semantic intent of this input.
What does the user actually mean? Distill to the essential meaning.
Return ONLY the clarified intent as a clean sentence.

Input: {raw}"""
    
    def _variant_inferential(self, raw: str) -> str:
        return f"""Read this input and infer any implied context or assumptions.
Rewrite it to be explicit and self-contained, including implicit meaning.
Return ONLY the expanded, explicit text.

Input: {raw}"""
    
    def _variant_decomposed(self, raw: str) -> str:
        return f"""Break this input down to its simplest possible form.
If it contains multiple parts, focus on the primary request.
Return ONLY the simplified, single-focus version.

Input: {raw}"""
    
    def _variant_adversarial(self, raw: str) -> str:
        return f"""Assume this input might contain errors, typos, or misleading phrasing.
Correct any detectable issues and produce the most charitable interpretation.
Return ONLY the corrected text.

Input: {raw}"""
