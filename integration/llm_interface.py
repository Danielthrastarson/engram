from typing import List, Optional
import logging
from utils import config

logger = logging.getLogger(__name__)


class LLMInterface:
    """
    Auto-detecting LLM interface.
    Tries: Ollama → OpenAI → Mock (always has a fallback)
    """
    
    def __init__(self):
        self.provider = "mock"
        self._ollama = None
        self._auto_detect()
    
    def _auto_detect(self):
        """Try each provider in order, use first available"""
        # Try Ollama (local)
        try:
            from integration.ollama_client import OllamaClient
            client = OllamaClient()
            # Quick check if Ollama is running
            import requests
            resp = requests.get("http://localhost:11434/api/tags", timeout=2)
            if resp.status_code == 200:
                self._ollama = client
                self.provider = "ollama"
                logger.info("🤖 LLM: Ollama detected (local)")
                return
        except Exception:
            pass
        
        # Try OpenAI
        try:
            import os
            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                self.provider = "openai"
                self._openai_key = api_key
                logger.info("🤖 LLM: OpenAI detected (API key)")
                return
        except Exception:
            pass
        
        # Fallback to mock
        self.provider = "mock"
        logger.info("🤖 LLM: Mock mode (no LLM detected)")
    
    def generate_abstraction(self, text: str, context_str: str) -> str:
        """Generate a compressed abstraction from text + context."""
        if self.provider == "ollama" and self._ollama:
            prompt = (
                f"Compress this into a single concise factual statement. "
                f"Context: {context_str[:200]}\n\nText: {text}\n\nCompressed:"
            )
            result = self._ollama.generate(prompt, max_tokens=100)
            if result:
                return result
        
        if self.provider == "openai":
            result = self._openai_call(
                f"Compress this into one concise factual statement:\n{text}"
            )
            if result:
                return result
        
        return self._fallback_compression(text)

    def _fallback_compression(self, text: str) -> str:
        """Simple extractive summary as fallback"""
        sentences = text.split('.')
        summary = sentences[0] + "."
        return summary[:500]

    def reason(self, query: str, context: str) -> str:
        """Perform reasoning based on query and context."""
        if self.provider == "ollama" and self._ollama:
            prompt = (
                f"Using this context, answer the question concisely.\n\n"
                f"Context: {context[:500]}\n\nQuestion: {query}\n\nAnswer:"
            )
            result = self._ollama.generate(prompt, max_tokens=200)
            if result:
                return result
        
        if self.provider == "openai":
            result = self._openai_call(
                f"Context: {context[:500]}\n\nQuestion: {query}\n\nAnswer concisely:"
            )
            if result:
                return result
        
        return f"Based on knowledge: {context[:50]}... I reason that..."

    def refine_abstraction(self, content: str) -> str:
        """Cognitive Loop: Refine/Compress an abstraction."""
        if self.provider == "ollama" and self._ollama:
            prompt = (
                f"Refine this memory to be more precise and concise. "
                f"Fix errors, remove redundancy. Return ONLY the refined text.\n\n"
                f"Original: {content}\n\nRefined:"
            )
            result = self._ollama.generate(prompt, max_tokens=100)
            if result:
                return result
        
        if self.provider == "openai":
            result = self._openai_call(
                f"Refine this to be more precise: {content}"
            )
            if result:
                return result
        
        # Mock fallback
        if "REFINE_ME" in content:
            return content.replace("REFINE_ME", "REFINED")
        if not content.endswith("(Refined)"):
            return content + " (Refined)"
        return content
    
    def _openai_call(self, prompt: str) -> Optional[str]:
        """Make an OpenAI API call"""
        try:
            import openai
            client = openai.OpenAI(api_key=self._openai_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI call failed: {e}")
            return None
