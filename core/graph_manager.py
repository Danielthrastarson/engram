
import logging
from typing import List, Optional, Tuple
from core.storage import EngramStorage
from core.abstraction import Abstraction, Link

logger = logging.getLogger(__name__)

class GraphManager:
    """
    Manages the Knowledge Graph layer of the Engram System.
    Handles linking abstractions and traversing relationships.
    """
    def __init__(self):
        self.storage = EngramStorage()

    def add_link(self, source_id: str, target_id: str, type: str = "relates_to", weight: float = 1.0):
        """Create a directed link between two abstractions"""
        # Verify both exist
        source = self.storage.get_abstraction(source_id)
        target = self.storage.get_abstraction(target_id)
        
        if not source or not target:
            logger.error(f"Cannot link {source_id} -> {target_id}: One or both not found.")
            return False
            
        # Update source's link list and save
        # Check if link exists to update weight/type?
        # For simplicity, we just append/overwrite in list logic
        
        new_link = Link(target_id=target_id, type=type, weight=weight)
        
        # Remove existing link to same target if any
        source.links = [l for l in source.links if l.target_id != target_id]
        source.links.append(new_link)
        
        # Save via storage (which updates links table)
        # We need the embedding to call add_abstraction... this is a design flaw in V1 storage.add_abstraction
        # It requires embedding every time.
        # OPTIMIZATION: We should have a specific update_links method in storage.
        # For now, let's add that method to storage or use a direct SQL execution here for efficiency.
        
        try:
            self.storage.conn.execute("""
                INSERT OR REPLACE INTO links VALUES (?, ?, ?, ?)
            """, (source_id, target_id, type, weight))
            self.storage.conn.commit()
            logger.info(f"🔗 Linked {source_id[:8]} -> {target_id[:8]} ({type})")
            return True
        except Exception as e:
            logger.error(f"Failed to add link: {e}")
            return False

    def get_related(self, source_id: str, min_weight: float = 0.5) -> List[Abstraction]:
        """Get all abstractions linked FROM this source"""
        cursor = self.storage.conn.execute("""
            SELECT target_id, weight FROM links 
            WHERE source_id = ? AND weight >= ?
            ORDER BY weight DESC
        """, (source_id, min_weight))
        
        related_ids = cursor.fetchall()
        results = []
        for rid, weight in related_ids:
            abs_obj = self.storage.get_abstraction(rid)
            if abs_obj:
                # Inject equality weight for context?
                abs_obj.metadata['_link_weight'] = weight
                results.append(abs_obj)
        
        return results

    def get_backlinks(self, target_id: str) -> List[Abstraction]:
        """Get all abstractions that point TO this target"""
        cursor = self.storage.conn.execute("""
            SELECT source_id, type FROM links 
            WHERE target_id = ?
        """, (target_id,))
        
        results = []
        for sid, type_ in cursor.fetchall():
            abs_obj = self.storage.get_abstraction(sid)
            if abs_obj:
                abs_obj.metadata['_link_type'] = type_
                results.append(abs_obj)
        return results

    def explore_subgraph(self, start_id: str, depth: int = 2) -> List[Abstraction]:
        """Recursive traversal to build a reasoning context"""
        visited = set()
        results = []
        
        def _traverse(current_id, current_depth):
            if current_depth > depth or current_id in visited:
                return
            
            visited.add(current_id)
            abs_obj = self.storage.get_abstraction(current_id)
            if abs_obj:
                results.append(abs_obj)
                
                # Get neighbors
                related = self.get_related(current_id)
                for rel in related:
                    _traverse(rel.id, current_depth + 1)
        
        _traverse(start_id, 0)
        return results
