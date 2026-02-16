from datetime import datetime
from typing import List, Dict, Optional, Any
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
import hashlib
import json

class Link(BaseModel):
    """Directed edge between abstractions"""
    target_id: str
    type: str = "relates_to" # implies, supports, contradicts, is_part_of
    weight: float = 1.0

class Abstraction(BaseModel):
    """
    Core unit of the Engram Memory System.
    Represents a compressed concept or pattern.
    """
    # Identity & Versioning
    id: str = Field(default_factory=lambda: str(uuid4()))
    version: int = 1
    
    # Core Content
    content: str
    embedding_hash: str  # For quick duplicate detection
    cluster_id: Optional[str] = None
    
    # Extensible Metadata (Source, Domain, etc.)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    image_path: Optional[str] = None # Multi-Modal Support
    
    # Relationships
    links: List[Link] = Field(default_factory=list) # Graph RAG
    source_chunks: List[str] = Field(default_factory=list)

    child_abstractions: List[str] = Field(default_factory=list)
    parent_abstraction: Optional[str] = None
    
    # Emotional Weight (Subconscious)
    salience: float = 1.0 # 0.5 (boring) to 2.0 (vital)

    # Quality Metrics (Cached)
    quality_score: float = 0.0          # CACHED quality score
    usage_count: int = 0                # Raw retrievals
    successful_application_count: int = 0 # Confirmed useful
    last_used: datetime = Field(default_factory=datetime.now)
    created_at: datetime = Field(default_factory=datetime.now)
    
    # Performance Metrics
    compression_ratio: float = 1.0
    accuracy_preserved: float = 1.0
    reuse_contexts: int = 0             # Number of distinct contexts used in
    decay_score: float = 0.0            # 0.0 = fresh, 1.0 = decayed
    
    def update_hash(self):
        """Update embedding hash based on content"""
        self.embedding_hash = hashlib.md5(self.content.encode()).hexdigest()

    def touch(self):
        """Update last_used timestamp"""
        self.last_used = datetime.now()
        
    class Config:
        validate_assignment = True
