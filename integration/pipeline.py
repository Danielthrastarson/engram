import logging
from core.abstraction_manager import AbstractionManager
from retrieval.search import Searcher
from retrieval.context import ContextBuilder
from integration.llm_interface import LLMInterface
from utils import config

logger = logging.getLogger(__name__)

from core.router import SemanticRouter

# ... (imports)

class EngramPipeline:
    def __init__(self):
        self.manager = AbstractionManager()
        self.searcher = Searcher()
        self.context_builder = ContextBuilder()
        self.llm = LLMInterface()
        self.router = SemanticRouter() # Phase 6: Hyperfocus

    def process_query(self, query: str) -> str:
        """
        Main reasoning loop:
        1. Router (Hyperfocus)
        2. Retrieve relevant abstractions
        3. Build context
        4. LLM Reason
        """
        # 0. Hyperfocus Routing (Phase 6)
        target_cluster = None
        if config.ENABLE_HYPERFOCUS:
            # Get top cluster "Color"
            routes = self.router.route_query(query, top_k=1)
            if routes:
                target_cluster = routes[0]
                logger.info(f"🧠 Pipeline Hyperfocus: Locked onto Cluster {target_cluster}")

        # 1. Retrieve (with optional scope)
        relevant_abs = self.searcher.search(
            query, 
            top_k=config.DEFAULT_TOP_K, 
            cluster_id=target_cluster
        )
        
        # 2. Build Context
        context_str = self.context_builder.format_context(relevant_abs)
        
        # === NORTH TRUTH GATE ===
        from core.truth_guard import TruthGuard

        risk, is_safe = TruthGuard.calculate_risk(relevant_abs)
        honest_forced = TruthGuard.enforce_honest_response(query, risk, relevant_abs)

        if honest_forced:
            response = honest_forced
            # still record usage but mark as low-confidence
            for abs_obj in relevant_abs:
                self.manager.record_usage(abs_obj.id, successful=False)
        else:
            # 3. LLM Reason (normal path)
            response = self.llm.reason(query, context_str)
            
            # 4. Update Usage (Relevance Feedback Loop)
            for abs_obj in relevant_abs:
                self.manager.record_usage(abs_obj.id, successful=True)
            
        return response

    def ingest(self, text: str, source: str = "user"):
        """
        Ingest new knowledge.
        1. Retrieve context (to see if we already know this)
        2. Compress into abstraction
        3. Store
        """
        # 1. Context
        related = self.searcher.search(text, top_k=3)
        context_str = self.context_builder.format_context(related)
        
        # 2. Compress
        compressed_content = self.llm.generate_abstraction(text, context_str)
        
        # 3. Store
        self.manager.create_abstraction(
            compressed_content, 
            metadata={"source": source, "original_length": len(text)}
        )
