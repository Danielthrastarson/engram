import logging
import numpy as np
from typing import List, Dict, Tuple, Optional
from core.storage import EngramStorage
from core.embedding import EmbeddingHandler
from utils import config

logger = logging.getLogger(__name__)

class ClusterCentroidManager:
    """
    Manages the "Color" of each cluster by calculating and storing centroids.
    """
    def __init__(self):
        self.storage = EngramStorage()
        self.centroids: Dict[str, np.ndarray] = {} # cluster_id -> vector
        
    def recalculate_centroids(self):
        """
        Scan all abstractions and calculate mean embedding for each cluster.
        """
        logger.info("Recalculating cluster centroids...")
        
        # 1. Fetch all data (cluster_id, embedding)
        # Optimization: Fetch only needed columns
        cursor = self.storage.conn.execute("SELECT id, cluster_id FROM abstractions WHERE cluster_id IS NOT NULL")
        rows = cursor.fetchall()
        
        if not rows:
            logger.info("No clustered data found.")
            return

        # Map cluster_id -> list of IDs
        cluster_map: Dict[str, List[str]] = {}
        for r in rows:
            doc_id, c_id = r
            if c_id == "noise" or c_id == "unclustered":
                continue
            if c_id not in cluster_map:
                cluster_map[c_id] = []
            cluster_map[c_id].append(doc_id)
            
        # 2. Calculate Centroids
        new_centroids = {}
        
        for c_id, doc_ids in cluster_map.items():
            # Get embeddings for these docs
            embeddings = self.storage.collection.get(ids=doc_ids, include=['embeddings'])['embeddings']
            if embeddings is None or len(embeddings) == 0:
                continue
                
            # Mean vector
            centroid = np.mean(embeddings, axis=0)
            # Normalize? Cosine similarity usually requires normalized vectors for best results
            norm = np.linalg.norm(centroid)
            if norm > 0:
                centroid = centroid / norm
                
            new_centroids[c_id] = centroid
            
        self.centroids = new_centroids
        logger.info(f"Calculated {len(self.centroids)} centroids.")
        
    def get_centroid(self, cluster_id: str) -> Optional[np.ndarray]:
        return self.centroids.get(cluster_id)
        
    def get_all_centroids(self) -> Dict[str, np.ndarray]:
        if not self.centroids:
            self.recalculate_centroids()
        return self.centroids


class SemanticRouter:
    """
    The "Scout" that routes queries to relevant clusters.
    """
    def __init__(self):
        self.centroid_manager = ClusterCentroidManager()
        self.embedder = EmbeddingHandler()
        
    def route_query(self, query: str, top_k: int = 1) -> List[str]:
        """
        Return top_k cluster_ids that match the query.
        """
        # 1. Embed Query
        query_vec = self.embedder.generate_embedding(query)
        
        # Ensure it's numpy (it should be now, but be safe)
        if hasattr(query_vec, 'numpy'):
            query_vec = query_vec.numpy()
        if isinstance(query_vec, list):
            query_vec = np.array(query_vec)
            
        # 2. Get Centroids
        centroids = self.centroid_manager.get_all_centroids()
        if not centroids:
            logger.warning("No centroids available for routing.")
            return []
            
        # 3. Calculate Similarity (Dot product since normalized)
        # scores: List[Tuple[score, cluster_id]]
        scores = []
        for c_id, vec in centroids.items():
            score = np.dot(query_vec, vec)
            scores.append((score, c_id))
            
        # 4. Sort and return top_k
        scores.sort(key=lambda x: x[0], reverse=True)
        
        # Debug log
        top_matches = scores[:top_k]
        logger.info(f"Query '{query}' routed to: {top_matches}")
        
        return [c_id for score, c_id in top_matches]
