
import sys
import time
import logging
from pathlib import Path

# Add project root to path
sys.path.append(str(Path("c:/Users/Notandi/Desktop/agi/engram-system")))

from integration.pipeline import EngramPipeline
from core.clustering import ClusteringEngine
from core.router import ClusterCentroidManager, SemanticRouter
from core.abstraction_manager import AbstractionManager

# Test Data: 2 Distinct Clusters (Need >= 5 items each for HDBSCAN)
PLUMBING_DOCS = [
    "To fix a leaky faucet, first turn off the water supply valve under the sink.",
    "Use a wrench to loosen the packing nut on the faucet handle.",
    "Replace the worn-out O-ring or washer inside the valve stem to stop the drip.",
    "Apply plumber's tape (Teflon tape) to the threads before reassembling the pipe.",
    "Blocked drains can be cleared using a plunger or a snake tool.",
    "Copper pipes are durable but require soldering for connections.",
    "PVC pipes are commonly used for waste lines and are glued together."
]

SOFTWARE_DOCS = [
    "Python is a dynamic programming language used for web development and AI.",
    "Functions in Python are defined using the 'def' keyword.",
    "A list comprehension is a concise way to create lists from existing iterables.",
    "Object-oriented programming (OOP) uses classes and objects to structure code.",
    "The Global Interpreter Lock (GIL) prevents multi-threaded Python bytecode execution.",
    "Docker containers package software with all its dependencies.",
    "Git is a version control system for tracking changes in source code."
]

# Distractor: A 'bridge' concept that could confuse vector search without scoping
# "Pipe" in software context
DISTRACTOR_DOC = "Unix pipes (|) allow you to pass the output of one command to another."

def test_hyperfocus():
    print("🚀 STARTING HYPERFOCUS (PHASE 6) TEST...")
    
    pipeline = EngramPipeline()
    clustering = ClusteringEngine()
    centroid_mgr = ClusterCentroidManager()
    router = SemanticRouter()
    manager = AbstractionManager()
    
    # 0. Clear DB for clean test? 
    # For now, let's just ingest and hope HDBSCAN separates them cleanly from existing data.
    # Actually, to be safe, we might want to clear. 
    # But let's assume we can distinguish by content.
    
    # 1. Ingest Data
    print("   Ingesting Plumbing Docs...")
    for doc in PLUMBING_DOCS:
        pipeline.ingest(doc, source="manual_test_plumbing")
        
    print("   Ingesting Software Docs...")
    for doc in SOFTWARE_DOCS:
        pipeline.ingest(doc, source="manual_test_software")
        
    print("   Ingesting Distractor...")
    pipeline.ingest(DISTRACTOR_DOC, source="manual_test_distractor")
    
    # 2. Force Clustering
    print("   Running Clustering...")
    clustering.perform_clustering()
    
    # 3. Calculate Centroids
    print("   Calculating Centroids...")
    centroid_mgr.recalculate_centroids()
    centroids = centroid_mgr.get_all_centroids()
    print(f"   Generated {len(centroids)} centroids.")
    
    if len(centroids) < 2:
        print("   ⚠️ WARNING: HDBSCAN didn't find 2 clusters. Test might be inconclusive.")
        # Proceed anyway to test mechanism
        
    # 4. Test Routing
    print("\n🧪 TEST 1: SEMANTIC ROUTING")
    
    query_p = "How to stop a water leak?"
    routes_p = router.route_query(query_p, top_k=1)
    print(f"   Query: '{query_p}' -> Cluster {routes_p}")
    
    query_s = "How to define a function in code?"
    routes_s = router.route_query(query_s, top_k=1)
    print(f"   Query: '{query_s}' -> Cluster {routes_s}")
    
    if not routes_p or not routes_s:
        print("   ❌ FAIL: Router returned no clusters.")
        return
        
    plumbing_cluster = routes_p[0]
    software_cluster = routes_s[0]
    
    if plumbing_cluster == software_cluster:
        print("   ⚠️ WARNING: Router mapped both to same cluster (or noise).")
    else:
        print("   ✅ SUCCESS: Distinct clusters identified.")

    # 5. Test Scoped Retrieval (Hyperfocus)
    print("\n🧪 TEST 2: SCOPED RETRIEVAL (SUB-AGENTS)")
    
    # Search for "pipe" in SOFTWARE cluster
    # Context: expecting Unix pipe, NOT water pipe
    query_ambiguous = "How do pipes work?" 
    
    print(f"   Hyperfocusing on SOFTWARE Cluster ({software_cluster})...")
    results = pipeline.searcher.search(query_ambiguous, top_k=5, cluster_id=software_cluster)
    
    found_unix = False
    found_water = False
    
    for r in results:
        print(f"    - {r.content[:60]}...")
        if "Unix" in r.content or "command" in r.content:
            found_unix = True
        if "water" in r.content or "leak" in r.content or "plumber" in r.content:
            found_water = True
            
    if found_unix and not found_water:
        print("   ✅ SUCCESS: Retrieved Unix pipes, ignored Water pipes.")
    elif found_water:
        print("   ❌ FAIL: Leaked distinct domain info (Water pipes found in Software mode).")
    else:
        print("   ⚠️ INDETERMINATE: Didn't find Unix pipe either.")
        
    # Counter-check: Plumbing Scope
    print(f"\n   Hyperfocusing on PLUMBING Cluster ({plumbing_cluster})...")
    results_p = pipeline.searcher.search(query_ambiguous, top_k=5, cluster_id=plumbing_cluster)
    
    found_water_p = False
    for r in results_p:
        print(f"    - {r.content[:60]}...")
        if "water" in r.content or "leak" in r.content:
            found_water_p = True
            
    if found_water_p:
        print("   ✅ SUCCESS: Retrieved Water pipes in Plumbing mode.")

if __name__ == "__main__":
    test_hyperfocus()
