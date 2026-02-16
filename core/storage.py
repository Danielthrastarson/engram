import chromadb
from chromadb.config import Settings
import sqlite3
import json
from typing import List, Optional, Dict
from pathlib import Path
from datetime import datetime
from core.abstraction import Abstraction
from utils import config

class EngramStorage:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EngramStorage, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=config.CHROMA_PERSIST_DIRECTORY,
            settings=Settings(allow_reset=True)
        )
        
        self.collection = self.chroma_client.get_or_create_collection(
            name="engrams",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Image Collection (CLIP 512d)
        self.image_collection = self.chroma_client.get_or_create_collection(
            name="engram_images",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize Metadata DB (SQLite)
        self._init_sqlite()
        self._initialized = True
        
    def _init_sqlite(self):
        """Initialize SQLite for robust metadata and fast indexing"""
        self.conn = sqlite3.connect(config.METADATA_DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # Enable WAL mode for concurrency
        self.conn.execute("PRAGMA journal_mode=WAL;")
        
        # Create table if not exists (mirroring Pydantic model)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS abstractions (
                id TEXT PRIMARY KEY,
                version INTEGER,
                content TEXT,
                embedding_hash TEXT,
                cluster_id TEXT,
                metadata TEXT,
                quality_score REAL,
                usage_count INTEGER,
                successful_application_count INTEGER,
                last_used TIMESTAMP,
                created_at TIMESTAMP,
                compression_ratio REAL,
                accuracy_preserved REAL,
                reuse_contexts INTEGER,
                decay_score REAL,
                image_path TEXT,
                salience REAL
            )
        """)
        
        # New Links Table for Graph RAG
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS links (
                source_id TEXT,
                target_id TEXT,
                type TEXT,
                weight REAL,
                PRIMARY KEY (source_id, target_id, type)
            )
        """)
        
        # CRITICAL: Create indexes for performance (User Request #2)
        # Check if column exists (migration for existing DB)
        try:
            self.conn.execute("ALTER TABLE abstractions ADD COLUMN image_path TEXT")
        except sqlite3.OperationalError:
            pass # Column already exists

        try:
            self.conn.execute("ALTER TABLE abstractions ADD COLUMN salience REAL")
        except sqlite3.OperationalError:
            pass # Column already exists
            
        self.conn.executescript("""
            CREATE INDEX IF NOT EXISTS idx_cluster_id ON abstractions(cluster_id);
            CREATE INDEX IF NOT EXISTS idx_last_used ON abstractions(last_used);
            CREATE INDEX IF NOT EXISTS idx_quality ON abstractions(quality_score);
            CREATE INDEX IF NOT EXISTS idx_successful ON abstractions(successful_application_count);
            CREATE INDEX IF NOT EXISTS idx_hash ON abstractions(embedding_hash);
            CREATE INDEX IF NOT EXISTS idx_salience ON abstractions(salience);
            
            CREATE INDEX IF NOT EXISTS idx_link_source ON links(source_id);
            CREATE INDEX IF NOT EXISTS idx_link_target ON links(target_id);
        """)
        self.conn.commit()

    def add_abstraction(self, abstraction: Abstraction, embedding: List[float]):
        """Add abstraction to both Chroma (vector) and SQLite (metadata)"""
        
        # 1. Add to Chroma
        # Ensure embedding is list (Chroma requirement)
        if hasattr(embedding, 'tolist'):
            embedding = embedding.tolist()
            
        # Check dimensionality to route to correct collection
        # Text (MiniLM) = 384, Image (CLIP) = 512
        if len(embedding) == 512:
            self.image_collection.upsert(
                ids=[abstraction.id],
                embeddings=[embedding],
                metadatas=[{"cluster_id": str(abstraction.cluster_id) if abstraction.cluster_id else ""}],
                documents=[abstraction.content]
            )
        else:
            self.collection.upsert(
                ids=[abstraction.id],
                embeddings=[embedding],
                metadatas=[{"cluster_id": str(abstraction.cluster_id) if abstraction.cluster_id else ""}],
                documents=[abstraction.content] # Optional, but good for debug
            )
        
        # 2. Add to SQLite (Abstractions Table)
        self.conn.execute("""
            INSERT OR REPLACE INTO abstractions VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """, (
            abstraction.id,
            abstraction.version,
            abstraction.content,
            abstraction.embedding_hash,
            abstraction.cluster_id,
            json.dumps(abstraction.metadata),
            abstraction.quality_score,
            abstraction.usage_count,
            abstraction.successful_application_count,
            abstraction.last_used.isoformat(),
            abstraction.created_at.isoformat(),
            abstraction.compression_ratio,
            abstraction.accuracy_preserved,
            abstraction.reuse_contexts,
            abstraction.decay_score,
            abstraction.image_path,
            abstraction.salience
        ))
        
        # 3. Add Links (Graph RAG)
        if abstraction.links:
            for link in abstraction.links:
                self.conn.execute("""
                    INSERT OR REPLACE INTO links VALUES (?, ?, ?, ?)
                """, (abstraction.id, link.target_id, link.type, link.weight))
                
        self.conn.commit()
        
    def get_abstraction(self, abstraction_id: str) -> Optional[Abstraction]:
        cursor = self.conn.execute("SELECT * FROM abstractions WHERE id = ?", (abstraction_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
            
        data = dict(row)
        
        # Parse JSON and datetime fields
        data['metadata'] = json.loads(data['metadata'])
        data['last_used'] = datetime.fromisoformat(data['last_used']) 
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        # Fetch Links
        link_cursor = self.conn.execute("SELECT target_id, type, weight FROM links WHERE source_id = ?", (abstraction_id,))
        links_data = link_cursor.fetchall()
        
        # Reconstruct Link objects
        # We need to import Link inside function to avoid circular import if defined in abstraction.py
        # But we can just use the dict structure or assume Abstraction validates it
        links_list = []
        for l_row in links_data:
            links_list.append({
                "target_id": l_row[0],
                "type": l_row[1],
                "weight": l_row[2]
            })
            
        data['links'] = links_list
        
        # Handle potential None from schema migration
        if data.get('salience') is None:
            data['salience'] = 1.0
            
        return Abstraction(**data)
 
    def update_metrics(self, abstraction: Abstraction):
        """Update just the metrics for an abstraction (fast path)"""
        self.conn.execute("""
            UPDATE abstractions SET 
                usage_count = ?,
                successful_application_count = ?,
                quality_score = ?,
                last_used = ?,
                decay_score = ?,
                salience = ?
            WHERE id = ?
        """, (
            abstraction.usage_count,
            abstraction.successful_application_count,
            abstraction.quality_score,
            abstraction.last_used.isoformat(),
            abstraction.decay_score,
            abstraction.salience,
            abstraction.id
        ))
        self.conn.commit()
    
    def get_abstraction_by_hash(self, embedding_hash: str) -> Optional[Abstraction]:
        """Fast lookup by hash for duplicate checking"""
        cursor = self.conn.execute("SELECT * FROM abstractions WHERE embedding_hash = ?", (embedding_hash,))
        row = cursor.fetchone()
        
        if not row:
            return None
            
        data = dict(row)
        data['metadata'] = json.loads(data['metadata'])
        data['last_used'] = datetime.fromisoformat(data['last_used']) 
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        return Abstraction(**data)
