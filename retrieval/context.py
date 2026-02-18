from typing import List
from core.abstraction import Abstraction

class ContextBuilder:
    def format_context(self, abstractions: List[Abstraction], max_tokens: int = 2000) -> str:
        """
        Format abstractions into a clean context string for LLM.
        """
        if not abstractions:
            return "No relevant past knowledge found."
            
        context_parts = []
        current_tokens = 0 # Rough estimate
        
        header = "## Relevant Past Abstractions:\n"
        context_parts.append(header)
        
        for abs_obj in abstractions:
            # Format: [ID] (Quality: X) Content
            entry = f"- [{abs_obj.id[:6]}] (Quality: {abs_obj.quality_score}): {abs_obj.content}\n"
            
            # Rough token count (4 chars ~= 1 token)
            entry_tokens = len(entry) / 4
            
            if current_tokens + entry_tokens > max_tokens:
                break
                
            context_parts.append(entry)
            current_tokens += entry_tokens
            
        return "".join(context_parts)
