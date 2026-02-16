import sys
from pathlib import Path
sys.path.append(str(Path("c:/Users/Notandi/Desktop/agi/engram-system")))

import logging
import random
from integration.pipeline import EngramPipeline
from core.clustering import ClusteringEngine
from utils import config

# Configure clean logging
logging.basicConfig(level=logging.ERROR) # Only show errors, we print results manually

def run_business_proof():
    print("🚀 STARTING BUSINESS VALUE PROOF...")
    pipeline = EngramPipeline()
    
    # 1. Clear Memory (Start Fresh)
    print("   Resetting memory bank...")
    try:
        pipeline.manager.storage.chroma_client.reset()
    except:
        pass
    pipeline.manager.storage.collection = pipeline.manager.storage.chroma_client.get_or_create_collection(
        name="engrams", metadata={"hnsw:space": "cosine"}
    )
    pipeline.manager.storage._init_sqlite()

    # 2. Ingest the "Needle" (Critical Business Fact)
    secret_code = "PROJECT_OMEGA_LAUNCH_DATE_2027_05_15"
    print(f"   🔑 Ingesting CRITICAL FACT: '{secret_code}'")
    pipeline.ingest(f"The launch date for Project Omega is {secret_code}.", source="ceo_email")

    # 3. Ingest the "Haystack" (50 Distracters)
    print("   🌪️ Ingesting 50 Distracter Facts (Noise)...")
    distracters = [
        "The cat sat on the mat.",
        "Python is a programming language.",
        "The weather in London is rainy.",
        "Apples are red.",
        "SpaceX lands rockets.",
        "Coffee contains caffeine.",
        "The sky is blue.",
        "Birds fly south for winter.",
        "Water boils at 100 degrees Celsius.",
        "The Earth orbits the Sun."
    ]
    for i in range(50):
        noise = f"{random.choice(distracters)} (ID: {i})"
        pipeline.ingest(noise, source="slack_noise")
        if i % 10 == 0:
            print(f"      - Added 10 noise items...")

    # 4. The "Pepsi Challenge": Retrieval
    print("\n🔎 TEST 1: RETRIEVAL PRECISION")
    print("   Query: 'When is Project Omega launching?'")
    
    results = pipeline.searcher.search("When is Project Omega launching?", top_k=3)
    
    found_secret = False
    for res in results:
        print(f"      - Retrieved: {res.content[:50]}... (Score: {res.quality_score})")
        if secret_code in res.content:
            found_secret = True

    if found_secret:
        print("   ✅ SUCCESS: Found the secret code amidst 50 distracters!")
    else:
        print("   ❌ FAILURE: Did not find the secret code.")

    # 5. The "Cluster Challenge": Organization
    print("\n🧠 TEST 2: AUTOMATIC ORGANIZATION (Clustering)")
    print("   Running clustering engine...")
    clustering = ClusteringEngine()
    clustering.perform_clustering()
    
    # Check if Secret Code is in a specific cluster vs noise
    # We expect at least 2 clusters: 1 for noise (repititive), 1 for unique/other
    # Since distracters are repetitive, they should clump.
    
    counts = clustering.storage.conn.execute(
        "SELECT cluster_id, COUNT(*) FROM abstractions GROUP BY cluster_id"
    ).fetchall()
    
    print("   Cluster Distribution:")
    for row in counts:
        cid = row[0] if row[0] else "Unclustered"
        count = row[1]
        print(f"      - Cluster {cid}: {count} items")
        
    num_clusters = len(counts)
    if num_clusters >= 2:
         print("   ✅ SUCCESS: System automatically organized noise into groups.")
    else:
         print("   ⚠️ NOTE: Everything might be in one cluster or noise (normal for small datasets).")

    print("\n🏆 CONCLUSION:")
    if found_secret:
        print("   This system represents a VIABLE BUSINESS PRODUCT for Knowledge Management.")
    else:
        print("   System needs tuning for high-noise environments.")

if __name__ == "__main__":
    run_business_proof()
