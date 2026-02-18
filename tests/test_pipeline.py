import sys
from pathlib import Path
sys.path.append(str(Path("c:/Users/Notandi/Desktop/agi/engram-system")))

import logging
from integration.pipeline import EngramPipeline
from retrieval.search import Searcher
from core.quality import update_metrics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_full_system():
    print("1. Initializing Pipeline...")
    pipeline = EngramPipeline()
    
    # Clean state
    print("   Clearing previous test data...")
    try:
        pipeline.manager.storage.chroma_client.reset()
    except:
        pass
    pipeline.manager.storage.collection = pipeline.manager.storage.chroma_client.get_or_create_collection(
        name="engrams", metadata={"hnsw:space": "cosine"}
    )
    pipeline.manager.storage._init_sqlite()

    print("\n2. Ingesting Knowledge...")
    facts = [
        "The sky is blue because of Rayleigh scattering.",
        "Photosynthesis converts light energy into chemical energy.",
        "Mitochondria generate most of the cell's supply of adenosine triphosphate (ATP)."
    ]
    
    for fact in facts:
        # Ingest (creates abstraction)
        # Note: Pipeline.ingest uses LLM to compress. 
        # Our mock LLM fallback returns first 3 sentences.
        pipeline.ingest(fact, source="test")
        print(f"   Ingested: {fact[:30]}...")

    print("\n3. Testing Retrieval (Searcher)...")
    searcher = Searcher()
    # Search for "cell energy"
    results = searcher.search("cell energy", top_k=2)
    
    print(f"   Found {len(results)} results for 'cell energy'")
    for res in results:
        print(f"   - [{res.id[:6]}] {res.content[:50]}... (Score: {res.quality_score})")
        
    if len(results) >= 1:
        print("   ✅ Retrieval: Success")
    else:
        print("   ❌ Retrieval: Failed (No results)")

    print("\n4. Testing Reasoning (Pipeline)...")
    response = pipeline.process_query("Why is the sky blue?")
    print(f"   Response: {response}")
    
    if "Based on knowledge" in response:
        print("   ✅ Reasoning: Success")
    else:
         print("   ❌ Reasoning: Failed")
         
    print("\n✅ Full System Verification Complete!")

if __name__ == "__main__":
    test_full_system()
