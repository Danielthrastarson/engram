import hdbscan
import numpy as np
import logging
from typing import List, Dict, Tuple
from core.storage import EngramStorage
from core.abstraction import Abstraction
from utils import config

logger = logging.getLogger(__name__)


def compute_axiom_affinity(abstraction: Abstraction) -> float:
    """
    Score how axiom-like an abstraction is (0.0 to 1.0).
    Higher = more foundational, should be protected from decay.
    """
    score = 0.0
    
    # Axiom-derived engrams are foundational
    if abstraction.is_axiom_derived:
        score += 0.4
    
    # Used in proofs = important
    if abstraction.metadata.get('proof_count', 0) > 0:
        score += 0.3
    elif len(abstraction.axioms_used) > 0:
        score += 0.15  # Lower score for using axioms vs being used
    
    # High consistency = foundational
    if abstraction.consistency_score > 0.9:
        score += 0.3
    elif abstraction.consistency_score > 0.7:
        score += 0.1
    
    return min(score, 1.0)


class ClusteringEngine:
    def __init__(self):
        self.storage = EngramStorage()
        self.clusterer = hdbscan.HDBSCAN(
            min_cluster_size=config.HDBSCAN_MIN_CLUSTER_SIZE,
            min_samples=config.HDBSCAN_MIN_SAMPLES,
            metric=config.HDBSCAN_METRIC,
            cluster_selection_epsilon=config.HDBSCAN_EPSILON,
            prediction_data=config.HDBSCAN_PREDICTION_DATA
        )
        self.fitted = False
        
        # Axiom affinity threshold for protection
        self.axiom_affinity_threshold = 0.7
        self.axiom_decay_multiplier = 0.1  # 10x slower decay for foundational clusters

    def perform_clustering(self):
        """
        Run full clustering on all abstractions.
        Updates cluster_id for all items in storage.
        Now with axiom affinity protection.
        """
        # 1. Fetch all embeddings & IDs
        # Note: In production with >10k items, we'd batch this or use incremental
        embeddings_data = self.storage.collection.get(include=['embeddings', 'metadatas'])
        
        if not embeddings_data['ids']:
            logger.info("No data to cluster.")
            return

        ids = embeddings_data['ids']
        embeddings = np.array(embeddings_data['embeddings'])
        
        if len(ids) < config.HDBSCAN_MIN_CLUSTER_SIZE:
            logger.info("Not enough data to cluster yet.")
            return

        # 2. Fit HDBSCAN
        logger.info(f"Clustering {len(ids)} items...")
        self.clusterer.fit(embeddings)
        self.fitted = True
        
        labels = self.clusterer.labels_
        
        # 3. Update Storage with axiom affinity awareness
        updates = []
        foundational_count = 0
        
        for i, doc_id in enumerate(ids):
            label = labels[i]
            cluster_id = str(label) if label != -1 else "noise"
            
            abs_obj = self.storage.get_abstraction(doc_id)
            if abs_obj and abs_obj.cluster_id != cluster_id:
                # Check axiom affinity before moving to noise
                affinity = compute_axiom_affinity(abs_obj)
                
                if cluster_id == "noise" and affinity > self.axiom_affinity_threshold:
                    # Protect axiom-derived engrams from being classified as noise
                    cluster_id = "foundational"
                    foundational_count += 1
                
                abs_obj.cluster_id = cluster_id
                self.storage.add_abstraction(abs_obj, embeddings[i])
                updates.append(doc_id)
                
        num_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        logger.info(f"Clustering complete. Updated {len(updates)} items. "
                     f"Found {num_clusters} clusters. "
                     f"Protected {foundational_count} foundational engrams.")

    def predict_cluster(self, embedding: List[float]) -> str:
        """
        Predict cluster for a new point (Approximate).
        Returns cluster_id or "noise".
        """
        if not self.fitted:
            return "unclustered"
            
        try:
            # Reshape for single prediction
            embedding_np = np.array(embedding).reshape(1, -1)
            label, strength = hdbscan.approximate_predict(self.clusterer, embedding_np)
            return str(label[0]) if label[0] != -1 else "noise"
        except Exception as e:
            logger.warning(f"Prediction failed (model likely not ready): {e}")
            return "unclustered"
    
    def get_axiom_affinity_stats(self) -> Dict[str, int]:
        """Get stats about axiom affinity across all engrams"""
        try:
            cursor = self.storage.conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN is_axiom_derived = 1 THEN 1 ELSE 0 END) as axiom_derived,
                    SUM(CASE WHEN consistency_score > 0.9 THEN 1 ELSE 0 END) as high_consistency,
                    SUM(CASE WHEN consistency_score < 0.5 THEN 1 ELSE 0 END) as low_consistency
                FROM abstractions
            """)
            row = cursor.fetchone()
            if row:
                return {
                    "total": row[0],
                    "axiom_derived": row[1] or 0,
                    "high_consistency": row[2] or 0,
                    "low_consistency": row[3] or 0,
                }
        except Exception as e:
            logger.warning(f"Failed to get axiom stats: {e}")
        
        return {"total": 0, "axiom_derived": 0, "high_consistency": 0, "low_consistency": 0}
