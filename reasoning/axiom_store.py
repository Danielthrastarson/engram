# reasoning/axiom_store.py
# Persistent axiom storage with versioning and domain-based retrieval
# Part of the Hybrid AI: First-Principles Reasoning system

import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4
from pathlib import Path
from utils import config

logger = logging.getLogger(__name__)


class Axiom:
    """Represents a formal axiom / logical truth"""
    def __init__(self, id: str = None, formula: str = "", domain: str = "general",
                 confidence: float = 1.0, version: int = 1, source: str = "manual",
                 metadata: Dict[str, Any] = None):
        self.id = id or str(uuid4())
        self.formula = formula
        self.domain = domain
        self.confidence = confidence
        self.version = version
        self.source = source  # "manual", "derived", "learned"
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.usage_count = 0
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "formula": self.formula,
            "domain": self.domain,
            "confidence": self.confidence,
            "version": self.version,
            "source": self.source,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "usage_count": self.usage_count,
        }
    
    @classmethod
    def from_row(cls, row) -> 'Axiom':
        ax = cls(
            id=row["id"],
            formula=row["formula"],
            domain=row["domain"],
            confidence=row["confidence"],
            version=row["version"],
            source=row["source"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )
        ax.created_at = datetime.fromisoformat(row["created_at"])
        ax.usage_count = row["usage_count"]
        return ax


class AxiomStore:
    """Persistent axiom storage with versioning and domain search"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        db_path = str(config.DATA_DIR / "axioms.db")
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self._init_schema()
        self._initialized = True
        logger.info(f"AxiomStore initialized at {db_path}")
    
    def _init_schema(self):
        """Create axiom tables"""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS axioms (
                id TEXT PRIMARY KEY,
                formula TEXT NOT NULL,
                domain TEXT DEFAULT 'general',
                confidence REAL DEFAULT 1.0,
                version INTEGER DEFAULT 1,
                source TEXT DEFAULT 'manual',
                metadata TEXT DEFAULT '{}',
                created_at TIMESTAMP,
                usage_count INTEGER DEFAULT 0
            );
            
            CREATE INDEX IF NOT EXISTS idx_axiom_domain ON axioms(domain);
            CREATE INDEX IF NOT EXISTS idx_axiom_confidence ON axioms(confidence);
            CREATE INDEX IF NOT EXISTS idx_axiom_source ON axioms(source);
            
            CREATE TABLE IF NOT EXISTS axiom_history (
                axiom_id TEXT,
                version INTEGER,
                formula TEXT,
                changed_at TIMESTAMP,
                reason TEXT,
                PRIMARY KEY (axiom_id, version)
            );
        """)
        self.conn.commit()
    
    def add(self, formula: str, domain: str = "general", confidence: float = 1.0,
            source: str = "manual", metadata: Dict[str, Any] = None) -> Axiom:
        """Add an axiom to the store"""
        axiom = Axiom(
            formula=formula,
            domain=domain,
            confidence=confidence,
            source=source,
            metadata=metadata or {},
        )
        
        self.conn.execute("""
            INSERT OR REPLACE INTO axioms 
            (id, formula, domain, confidence, version, source, metadata, created_at, usage_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            axiom.id, axiom.formula, axiom.domain, axiom.confidence,
            axiom.version, axiom.source, json.dumps(axiom.metadata),
            axiom.created_at.isoformat(), 0
        ))
        self.conn.commit()
        
        logger.info(f"Added axiom [{axiom.domain}]: {axiom.formula[:60]}...")
        return axiom
    
    def get(self, axiom_id: str) -> Optional[Axiom]:
        """Get a single axiom by ID"""
        row = self.conn.execute(
            "SELECT * FROM axioms WHERE id = ?", (axiom_id,)
        ).fetchone()
        return Axiom.from_row(row) if row else None
    
    def get_by_domain(self, domain: str, min_confidence: float = 0.5) -> List[Axiom]:
        """Get all axioms in a domain above confidence threshold"""
        rows = self.conn.execute("""
            SELECT * FROM axioms 
            WHERE domain = ? AND confidence >= ?
            ORDER BY confidence DESC
        """, (domain, min_confidence)).fetchall()
        return [Axiom.from_row(r) for r in rows]
    
    def get_relevant(self, domain: str = None, keywords: List[str] = None,
                     limit: int = 20) -> List[Axiom]:
        """Get relevant axioms by domain and/or keyword search"""
        if domain:
            rows = self.conn.execute("""
                SELECT * FROM axioms 
                WHERE (domain = ? OR domain = 'general')
                AND confidence >= 0.5
                ORDER BY confidence DESC, usage_count DESC
                LIMIT ?
            """, (domain, limit)).fetchall()
        elif keywords:
            # Simple keyword search in formula
            conditions = " OR ".join(["formula LIKE ?" for _ in keywords])
            params = [f"%{kw}%" for kw in keywords] + [limit]
            rows = self.conn.execute(f"""
                SELECT * FROM axioms 
                WHERE ({conditions})
                AND confidence >= 0.5
                ORDER BY confidence DESC
                LIMIT ?
            """, params).fetchall()
        else:
            rows = self.conn.execute("""
                SELECT * FROM axioms 
                WHERE confidence >= 0.5
                ORDER BY usage_count DESC
                LIMIT ?
            """, (limit,)).fetchall()
        
        return [Axiom.from_row(r) for r in rows]
    
    def increment_usage(self, axiom_id: str):
        """Track that an axiom was used in a proof"""
        self.conn.execute(
            "UPDATE axioms SET usage_count = usage_count + 1 WHERE id = ?",
            (axiom_id,)
        )
        self.conn.commit()
    
    def update_confidence(self, axiom_id: str, new_confidence: float, reason: str = ""):
        """Update axiom confidence with history tracking"""
        axiom = self.get(axiom_id)
        if not axiom:
            return
        
        # Save history
        self.conn.execute("""
            INSERT INTO axiom_history (axiom_id, version, formula, changed_at, reason)
            VALUES (?, ?, ?, ?, ?)
        """, (axiom_id, axiom.version, axiom.formula, datetime.now().isoformat(), reason))
        
        # Update
        self.conn.execute("""
            UPDATE axioms SET confidence = ?, version = version + 1 WHERE id = ?
        """, (new_confidence, axiom_id))
        self.conn.commit()
        
        logger.info(f"Updated axiom {axiom_id} confidence: {axiom.confidence} -> {new_confidence}")
    
    def count(self) -> int:
        """Total number of axioms"""
        return self.conn.execute("SELECT COUNT(*) FROM axioms").fetchone()[0]
    
    def seed_foundational(self):
        """Seed basic foundational axioms if store is empty"""
        if self.count() > 0:
            return
        
        foundational = [
            ("∀x: x = x", "logic", "Identity: everything equals itself"),
            ("∀P: P ∨ ¬P", "logic", "Law of excluded middle"),
            ("¬(P ∧ ¬P)", "logic", "Law of non-contradiction"),
            ("∀x,y: (x = y) → (P(x) ↔ P(y))", "logic", "Leibniz's law"),
            ("F = ma", "physics", "Newton's second law"),
            ("E = mc²", "physics", "Mass-energy equivalence"),
            ("∀x: cause(x) → precedes(x, effect(x))", "causality", "Causality principle"),
            ("∀A,B: P(A|B) = P(B|A)P(A)/P(B)", "math", "Bayes' theorem"),
        ]
        
        for formula, domain, description in foundational:
            self.add(
                formula=formula,
                domain=domain,
                confidence=1.0,
                source="foundational",
                metadata={"description": description}
            )
        
        logger.info(f"Seeded {len(foundational)} foundational axioms")
