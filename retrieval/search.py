import logging
import random
import numpy as np
from typing import List, Optional
from core.storage import EngramStorage
from core.abstraction import Abstraction
from core.embedding import EmbeddingHandler
from retrieval.ranking import mmr_rerank, CrossEncoderReranker
from utils import config

logger = logging.getLogger(__name__)

class Searcher:
    def __init__(self):
        self.storage = EngramStorage()
        self.embedder = EmbeddingHandler()
        self.reranker = CrossEncoderReranker() # Initialize the Pro Reranker

    def search(self, query: str, top_k: int = config.DEFAULT_TOP_K, cluster_id: Optional[str] = None, graph_depth: int = 0) -> List[Abstraction]:
        """
        Full search pipeline with optional Cluster Scoping (Hyperfocus).
        
        Args:
            cluster_id: If set, restricts search to this specific cluster (Sub-Agent mode).
        """
        query_emb = self.embedder.generate_embedding(query)
        
        # Build Filter
        # Note: We filter both general search AND trusted sources to respect Hyperfocus
        base_where = {}
        if cluster_id:
            base_where["cluster_id"] = cluster_id
            logger.info(f"🔎 Hyperfocus Active: Searching only in Cluster {cluster_id}")
        
        # 1. Broad Retrieval (Hybrid: Semantic + Trusted Source)
        
        # 1. Broad Retrieval (Hybrid: Semantic + Trusted Source)
        
        # A. Standard vector search (Text)
        broad_k = max(40, top_k * 10)
        results_std = self.storage.collection.query(
            query_embeddings=[query_emb],
            n_results=broad_k,
            where=base_where if base_where else None,
            include=['metadatas', 'documents', 'embeddings']
        )

        # A.2 Image Search (Cross-Modal)
        # We also embed the query with CLIP (512d) and search the image collection
        # This allows "text -> image" retrieval
        try:
            # Force CLIP embedding for query (even if it's text)
            clip_model = self.embedder._get_clip_model()
            clip_emb = clip_model.encode(query, convert_to_numpy=True)
            
            # Normalize
            norm = np.linalg.norm(clip_emb)
            if norm > 0: clip_emb = clip_emb / norm
            
            results_img = self.storage.image_collection.query(
                query_embeddings=[clip_emb.tolist()],
                n_results=5, # Top 5 images
                where=base_where if base_where else None,
                include=['metadatas', 'documents', 'embeddings']
            )
        except Exception as e:
            logger.warning(f"Image search failed: {e}")
            results_img = None
        
        # B. Trusted Source Injection (The "CEO Priority" Channel)
        # We must respect the cluster filter here too if active
        trust_where = {"source": "truth"}
        if cluster_id:
            trust_where = {"$and": [{"source": "truth"}, {"cluster_id": cluster_id}]}
            
        results_trust = self.storage.collection.query(
            query_embeddings=[query_emb],
            n_results=10,
            where=trust_where, 
            include=['metadatas', 'documents', 'embeddings']
        )
        
        # Merge results (deduplicate by ID)
        seen_ids = set()
        candidates = []
        
        # Helper to process results
        def process_batch(res_obj):
            if not res_obj or not res_obj['ids'] or not res_obj['ids'][0]: return
            ids = res_obj['ids'][0]
            embeddings = res_obj['embeddings'][0]
            
            for i, abs_id in enumerate(ids):
                if abs_id in seen_ids: continue
                seen_ids.add(abs_id)
                
                abs_obj = self.storage.get_abstraction(abs_id)
                if abs_obj:
                    abs_obj._embedding_cache = embeddings[i]
                    candidates.append(abs_obj)

        process_batch(results_std)
        process_batch(results_trust)
        process_batch(results_img) # Add images to candidates



        # 2. Quality Sorting (Initial Sort)
        candidates.sort(key=lambda x: x.quality_score, reverse=True)
        
        # 3. Cross-Encoder Re-ranking (The "Pro" Step)
        # This will attach _rerank_score to top N candidates
        if config.ENABLE_RERANKING:
             # Rerank ALL candidates so we don't drop trusted ones yet
             # (Cross-Encoder might hate them initially, but metadata saves them)
             candidates = self.reranker.rerank(query, candidates, top_k=len(candidates))
             
             # FINAL FUSION: Combine Rerank Score + Source Authority
             # This fixes the "Adversarial Distracter" problem where lies look like truth.
             for cand in candidates:
                 # Base score from Cross-Encoder (usually -10 to 10 range logits)
                 final_score = getattr(cand, '_rerank_score', 0.0)
                 
                 # Source Authority Boost
                 source = cand.metadata.get('source', '')
                 if source in ['truth', 'ceo_email', 'documentation']:
                     final_score += 100.0 # BOMBPROOF boost: Truth always wins
                                      
                 cand._final_score = final_score
                 cand._rerank_score = final_score # CRITICAL: Ensure MMR uses the boosted score!
            
             # Filter out noise (low relevance items)
             # Cross-encoder logits: >0 usually relevant, <-2 usually irrelevant
             MIN_RERANK_SCORE = -2.0
             candidates = [c for c in candidates if c._final_score > MIN_RERANK_SCORE]
             
             # Sort by the Fused Score
             candidates.sort(key=lambda x: getattr(x, '_final_score', -999), reverse=True)
             
             # NOW we truncate to top 50
             candidates = candidates[:50]

        # 4. MMR Re-ranking (Diversity)
        # Uses the new scores from step 3 if available
        ranked = mmr_rerank(candidates, query_emb, top_k=top_k)
        
        # 5. Serendipity Injection
        if config.SERENDIPITY_ENABLED and len(ranked) < top_k:
             # Try to find a random high-quality item from a DIFFERENT cluster
             # (Simplified for V1: Just random high quality)
             serendipity = self._get_serendipity_item(exclude_ids=[x.id for x in ranked])
             if serendipity:
                 logger.info(f"Injecting serendipity: {serendipity.id}")
                 ranked.append(serendipity)
        
        # 6. Graph RAG Expansion (Chain of Abstraction)
        if graph_depth > 0:
            try:
                from core.graph_manager import GraphManager
                gm = GraphManager()
                
                current_ids = {doc.id for doc in ranked}
                expanded_docs = []
                
                # Expand top results
                for doc in ranked[:5]: # Only expand top 5 to avoid explosion
                    subgraph = gm.explore_subgraph(doc.id, depth=graph_depth)
                    for node in subgraph:
                        if node.id not in current_ids:
                            current_ids.add(node.id)
                            node.metadata['graph_hop'] = True # Mark as derived
                            expanded_docs.append(node)
                
                if expanded_docs:
                    logger.info(f"🕸️ Graph RAG: Expanded {len(expanded_docs)} new nodes.")
                    ranked.extend(expanded_docs)
            except ImportError:
                logger.warning("GraphManager not available for expansion.")
            except Exception as e:
                logger.error(f"Graph expansion failed: {e}")

        # 7. Implicit Priming (Subconscious)
        # Boost the cluster of the top result
        if ranked:
            try:
                top_result = ranked[0]
                if top_result.cluster_id:
                    from core.subconscious import Subconscious
                    Subconscious().implicit_priming(top_result.cluster_id)
            except Exception as e:
                logger.warning(f"Implicit priming failed: {e}")

        return ranked[:top_k + len(expanded_docs) if 'expanded_docs' in locals() else top_k]

    def _get_serendipity_item(self, exclude_ids: List[str]) -> Optional[Abstraction]:
        """Fetch one random high-quality abstraction"""
        try:
            # SQLite efficient random sample
            cursor = self.storage.conn.execute(
                f"""
                SELECT id FROM abstractions 
                WHERE quality_score > ? 
                ORDER BY RANDOM() LIMIT 1
                """, 
                (config.SERENDIPITY_MIN_QUALITY,)
            )
            row = cursor.fetchone()
            if row and row[0] not in exclude_ids:
                return self.storage.get_abstraction(row[0])
        except Exception as e:
            logger.warning(f"Serendipity fetch failed: {e}")
        return None
