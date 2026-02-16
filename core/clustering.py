import hdbscan
import numpy as np
import logging
from typing import List, Dict, Tuple
from core.storage import EngramStorage
from core.abstraction import Abstraction
from utils import config

logger = logging.getLogger(__name__)

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

    def perform_clustering(self):
        """
        Run full clustering on all abstractions.
        Updates cluster_id for all items in storage.
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
        
        # 3. Update Storage
        updates = []
        for i, doc_id in enumerate(ids):
            label = labels[i]
            cluster_id = str(label) if label != -1 else "noise"
            
            # We need to update this on the abstraction object
            # This is slow O(N) DB writes - optimization: Batch update
            # For V1 prototype, individual updates are acceptable (<1000 items)
            abs_obj = self.storage.get_abstraction(doc_id)
            if abs_obj and abs_obj.cluster_id != cluster_id:
                abs_obj.cluster_id = cluster_id
                self.storage.add_abstraction(abs_obj, embeddings[i]) # Re-save
                updates.append(doc_id)
                
        logger.info(f"Clustering complete. Updated {len(updates)} items. Found {len(set(labels)) - (1 if -1 in labels else 0)} clusters.")

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
