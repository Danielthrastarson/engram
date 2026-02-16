import requests
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class OllamaClient:
    """
    Lightweight Ollama client for LLM operations.
    Uses local Ollama server (http://localhost:11434)
    """
    def __init__(self, model: str = "llama3.2"):
        self.base_url = "http://localhost:11434"
        self.model = model
        
    def generate(self, prompt: str, max_tokens: int = 100) -> Optional[str]:
        """Generate text completion"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.7
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                logger.error(f"Ollama error: {response.status_code}")
                return None
                
        except requests.exceptions.ConnectionError:
            logger.warning("Ollama not running. Install: https://ollama.ai")
            return None
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return None
            
    def rate_salience(self, content: str) -> float:
        """Ask LLM to rate emotional importance (0.5-2.0)"""
        prompt = f"""Rate the emotional importance of this information from 0.5 (trivial) to 2.0 (vital).
Consider: urgency, personal impact, novelty.

Content: {content}

Answer with ONLY a number between 0.5 and 2.0."""

        response = self.generate(prompt, max_tokens=10)
        if not response:
            return 1.0  # Default
            
        try:
            # Parse number from response
            value = float(response.strip())
            return max(0.5, min(value, 2.0))  # Clamp
        except:
            return 1.0
            
    def connect_concepts(self, content_a: str, content_b: str) -> Optional[str]:
        """Generate insight connecting two concepts"""
        prompt = f"""What underlying principle or concept connects these two ideas? Answer in one short sentence.

Concept 1: {content_a}

Concept 2: {content_b}

Connection:"""

        return self.generate(prompt, max_tokens=50)
        
    def expand_query(self, query: str) -> list[str]:
        """Generate alternative query phrasings"""
        prompt = f"""Rephrase this query 3 different ways that mean the same thing. One per line.

Query: {query}

Rephrasings:"""

        response = self.generate(prompt, max_tokens=100)
        if not response:
            return [query]
            
        # Parse lines
        variants = [line.strip() for line in response.split('\n') if line.strip()]
        return [query] + variants[:3]
