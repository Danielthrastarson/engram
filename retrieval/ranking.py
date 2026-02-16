import numpy as np
from typing import List, Tuple
from core.abstraction import Abstraction
from core.embedding import EmbeddingHandler
from utils import config
import logging

try:
    from sentence_transformers import CrossEncoder
    HAS_CROSS_ENCODER = True
except ImportError:
    HAS_CROSS_ENCODER = False

logger = logging.getLogger(__name__)

class CrossEncoderReranker:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CrossEncoderReranker, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        if HAS_CROSS_ENCODER and config.ENABLE_RERANKING:
            logger.info(f"Loading Reranker Model: {config.RERANKING_MODEL_NAME}...")
            # We use a small, fast model for CPU
            self.model = CrossEncoder(config.RERANKING_MODEL_NAME)
            self.enabled = True
        else:
            logger.warning("Reranker disabled or dependencies missing.")
            self.model = None
            self.enabled = False
        
        self._initialized = True

    def rerank(self, query: str, candidates: List[Abstraction], top_k: int) -> List[Abstraction]:
        """
        Re-score candidates using Cross-Encoder.
        Returns top_k sorted by new score.
        """
        if not self.enabled or not candidates:
            return candidates[:top_k]

        # Prepare pairs [Query, Doc Text]
        pairs = [[query, doc.content] for doc in candidates]
        
        # Predict scores
        # scores is a list of floats, higher is better
        scores = self.model.predict(pairs)
        
        # Attach scores to objects (for debug/transparency)
        for i, doc in enumerate(candidates):
            doc._rerank_score = float(scores[i])
            
        # Sort by new score
        # Zip together (score, doc) and sort
        scored_candidates = list(zip(scores, candidates))
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        
        # Unzip
        reranked = [doc for score, doc in scored_candidates]
        return reranked[:top_k]

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    # Robust check for mixed dimension spaces (Text 384d vs Image 512d)
    # Check for None explicitly
    if v1 is None or v2 is None:
        return 0.0
        
    # Check lengths (works for list and numpy)
    if len(v1) != len(v2):
        return 0.0
        
    return np.dot(v1, v2)

def mmr_rerank(
    candidates: List[Abstraction],
    query_embedding: List[float],
    lambda_param: float = config.MMR_LAMBDA,
    top_k: int = config.DEFAULT_TOP_K
) -> List[Abstraction]:
    """
    Maximal Marginal Relevance (MMR) re-ranking.
    """
    if not candidates:
        return []
    
    selected = []
    pool = candidates.copy()
    
    while len(selected) < top_k and pool:
        best_score = -float('inf')
        best_item = None
        
        for item in pool:
            # Check for Vector Embedding
            if not hasattr(item, '_embedding_cache'):
                continue

            # Relevance: Prefer Cross-Encoder score if available
            if hasattr(item, '_rerank_score'):
                 # Normalize High logits (simplistic sigmoid-like clip for MMR mix)
                 # 0..10 range roughly
                 relevance = max(0, min(10, item._rerank_score)) / 10.0
            else:
                 relevance = cosine_similarity(item._embedding_cache, query_embedding)
            
            # Diversity: Max Sim(item, selected)
            max_sim_to_selected = 0.0
            for sel in selected:
                if not hasattr(sel, '_embedding_cache'): continue
                sim = cosine_similarity(item._embedding_cache, sel._embedding_cache)
                if sim > max_sim_to_selected:
                    max_sim_to_selected = sim
            
            # MMR Score
            mmr_score = (lambda_param * relevance) - ((1 - lambda_param) * max_sim_to_selected)
            
            if mmr_score > best_score:
                best_score = mmr_score
                best_item = item
        
        if best_item:
            selected.append(best_item)
            pool.remove(best_item)
        else:
            selected.extend(pool[:top_k-len(selected)])
            break
            
    return selected
