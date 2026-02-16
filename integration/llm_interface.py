from typing import List
import logging
from utils import config

logger = logging.getLogger(__name__)

class LLMInterface:
    def __init__(self):
        self.provider = "mock" # "ollama", "openai", "mock"
        
    def generate_abstraction(self, text: str, context_str: str) -> str:
        """
        Generate a compressed abstraction from text + context.
        """
        if not config.USE_LLM_COMPRESSION:
             return self._fallback_compression(text)
             
        try:
            # TODO: Implement actual API call here (Ollama/OpenAI)
            # For V1 Prototype, we simulate LLM or use simple extraction
            # return self._call_provider(text, context_str)
            
            # Using fallback for now until user configures API key/Ollama
            return self._fallback_compression(text)
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._fallback_compression(text)

    def _fallback_compression(self, text: str) -> str:
        """Simple extractive summary as fallback"""
        # Aggressive compression for V1 demo: Just take the first sentence
        # This typically gives 2x-4x compression on paragraphs
        sentences = text.split('.')
        summary = sentences[0] + "."
        return summary[:500] 

    def reason(self, query: str, context: str) -> str:
        """
        Perform reasoning based on query and context.
        """
        # Placeholder for V1
        return f"Based on knowledge: {context[:50]}... I reason that..."

    def refine_abstraction(self, content: str) -> str:
        """
        Cognitive Loop: Refine/Compress an abstraction to be better.
        """
        if not config.USE_LLM_COMPRESSION:
             # Simulation mode
             if "REFINE_ME" in content: # Test hook
                 return content.replace("REFINE_ME", "REFINED")
             # Heuristic: Append a tag to show it ran
             if not content.endswith("(Refined)"):
                  return content + " (Refined)"
             return content # No change
             
        try:
            # 1. Construct Self-Correction Prompt
            prompt = f"""
            You are a sub-module of an Artificial General Intelligence memory system.
            Your task is to REFINE a specific memory abstraction to reduce entropy and error.
            
            Input Abstraction:
            "{content}"
            
            Instructions:
            1. Fix any grammatical or logical errors.
            2. Clarify ambiguous phrasing.
            3. Remove redundancy (compress).
            4. Ensure it stands alone as a factual statement.
            5. Return ONLY the refined text.
            """
            
            # TODO: LLM Call
            # For V1 Prototype, use simple heuristic improvement
            # e.g., fix grammar, normalize format.
            # Here we just mock it nicely.
            if len(content) > 100:
                # Mock compression: truncate slightly or summarize?
                # Let's just append a marker for proof of concept
                return content.strip() + " (Refined by Cortex)"
            return content
        except Exception as e:
            logger.error(f"Refining failed: {e}")
            return content
