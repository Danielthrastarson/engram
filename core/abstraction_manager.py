from typing import List, Optional, Tuple
from core.abstraction import Abstraction
from core.storage import EngramStorage
from core.embedding import EmbeddingHandler
from core.quality import calculate_quality_score
from utils import config
import logging

logger = logging.getLogger(__name__)

class AbstractionManager:
    def __init__(self):
        self.storage = EngramStorage()
        self.embedder = EmbeddingHandler()
        


    def create_abstraction(self, content: str, metadata: dict = None) -> Tuple[Abstraction, bool]:
        """
        Create a new abstraction.
        Returns (Abstraction, created: bool).
        If duplicate content exists, returns (existing, False).
        """
        # 1. Create temporary object to get hash
        temp = Abstraction(content=content, embedding_hash="")
        temp.update_hash()
        
        # 2. Check for exact duplicate via hash (Duplicate Check)
        # Check if hash exists in DB metadata (optimization)
        existing = self.storage.get_abstraction_by_hash(temp.embedding_hash)
        if existing:
            logger.info(f"Duplicate abstraction found: {existing.id[:8]}")
            return existing, False
        
        # 3. Generate embedding
        embedding = self.embedder.generate_embedding(content)
        
        # 4. Create final object with DEFAULT VALUES
        abs_obj = Abstraction(
            content=content,
            embedding_hash=temp.embedding_hash,
            metadata=metadata or {},
            compression_ratio=1.0,  # Default
            accuracy_preserved=1.0, # Default
            decay_score=0.0,        # Fresh
            cluster_id=None
        )
        
        # 5. Persist
        self.storage.add_abstraction(abs_obj, embedding)
        logger.info(f"Created abstraction {abs_obj.id[:8]}")
        
        return abs_obj, True

    def get_abstraction(self, abs_id: str) -> Optional[Abstraction]:
        return self.storage.get_abstraction(abs_id)
        
    def record_usage(self, abs_id: str, successful: bool = True):
        """Record usage and update quality metrics using REAL formula."""
        abs_obj = self.storage.get_abstraction(abs_id)
        if not abs_obj:
            return
            
        abs_obj.usage_count += 1
        abs_obj.touch()
        if successful:
            abs_obj.successful_application_count += 1
            
        # Recalculate quality score using core.quality
        abs_obj.quality_score = calculate_quality_score(abs_obj)
        
        self.storage.update_metrics(abs_obj)

    def update_abstraction(self, abs_id: str, content: str) -> Optional[Abstraction]:
        """
        Update abstraction content (Cognitive Loop).
        1. Update content
        2. Re-embed
        3. Save
        """
        abs_obj = self.storage.get_abstraction(abs_id)
        if not abs_obj:
            return None
            
        # 1. Update Content & Version
        abs_obj.content = content
        abs_obj.update_hash()
        abs_obj.version += 1
        abs_obj.touch()
        
        # 2. Re-Embed
        embedding = self.embedder.generate_embedding(content)
        
        # 3. Save (Upsert handles duplicate ID)
        self.storage.add_abstraction(abs_obj, embedding)
        logger.info(f"Updated abstraction {abs_id[:8]} to v{abs_obj.version}")
        
        return abs_obj
