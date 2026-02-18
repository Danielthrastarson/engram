
import sys
import time
from pathlib import Path

# Add project root to path
ROOT_DIR = Path("c:/Users/Notandi/Desktop/agi/engram-system")
sys.path.append(str(ROOT_DIR))

from core.abstraction_manager import AbstractionManager
from core.graph_manager import GraphManager
from retrieval.search import Searcher

def test_graph_rag():
    print("🕸️ TESTING GRAPH RAG (CHAIN OF ABSTRACTION)...")
    
    am = AbstractionManager()
    gm = GraphManager()
    searcher = Searcher()
    
    # 1. Create Source and Target Abstractions
    print("\n1️⃣ Creating Nodes...")
    source_text = "The quick brown fox jumps over the lazy dog."
    target_text = "A pangram is a sentence using every letter of the alphabet."
    
    # Check if they exist or create new (using unique content to avoid collision)
    # adding timestamp to ensure uniqueness
    ts = int(time.time())
    source_content = f"Fox Source {ts}: {source_text}"
    target_content = f"Pangram Target {ts}: {target_text}"
    
    source_abs, _ = am.create_abstraction(source_content, metadata={"source": "truth"})
    target_abs, _ = am.create_abstraction(target_content)
    
    print(f"   Created Source: {source_abs.id[:8]}")
    print(f"   Created Target: {target_abs.id[:8]}")
    
    # 2. Link them
    print("\n2️⃣ Linking Nodes...")
    success = gm.add_link(source_abs.id, target_abs.id, type="exemplifies", weight=0.9)
    if success:
        print("   ✅ Linked Source -> Target")
    else:
        print("   ❌ Failed to link")
        return

    # 3. Search WITHOUT Graph
    print("\n3️⃣ Search Baseline (No Graph)...")
    results_base = searcher.search(f"Fox Source {ts}", top_k=1, graph_depth=0)
    found_target = any(r.id == target_abs.id for r in results_base)
    print(f"   Target found in baseline? {found_target}")
    
    # 4. Search WITH Graph
    print("\n4️⃣ Search with Graph RAG (Depth=1)...")
    results_graph = searcher.search(f"Fox Source {ts}", top_k=1, graph_depth=1)
    
    target_node = next((r for r in results_graph if r.id == target_abs.id), None)
    
    if target_node:
        print("   ✅ SUCCESS: Target retrieved via Graph RAG!")
        if target_node.metadata.get('graph_hop'):
            print("   ✅ Verified 'graph_hop' metadata is present.")
        else:
             print("   ⚠️  'graph_hop' metadata missing.")
             # The source might have been retrieved semantically too?
             # If target is semantically similar to query (which it isn't really), it won't have graph_hop
             # But here query is "Fox Source..." which is very different from "Pangram Target..." embedding wise (maybe)
             pass
    else:
        print("   ❌ FAIL: Target NOT found in Graph RAG results.")
        # Debug
        print(f"   Results: {[r.content for r in results_graph]}")

if __name__ == "__main__":
    test_graph_rag()
