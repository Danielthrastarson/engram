import sys
from pathlib import Path
sys.path.append(str(Path("c:/Users/Notandi/Desktop/agi/engram-system")))

import logging
from core.abstraction_manager import AbstractionManager
from core.quality import update_metrics
from core.storage import EngramStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_core_pipeline():
    print("1. Initializing Manager...")
    manager = AbstractionManager()
    
    # Clean state for testing
    print("   Clearing previous test data...")
    try:
        manager.storage.chroma_client.reset()
    except Exception as e:
        print(f"   Warning during reset: {e}")
        
    # Re-initialize collection after reset
    manager.storage.collection = manager.storage.chroma_client.get_or_create_collection(
        name="engrams",
        metadata={"hnsw:space": "cosine"}
    )
    manager.storage._init_sqlite() # Re-init tables
    
    print("\n2. Creating Abstractions...")
    concepts = [
        "The mitochondria is the powerhouse of the cell.",
        "Python functions are first-class objects.",
        "Machine learning models require vast amounts of data."
    ]
    
    ids = []
    for concept in concepts:
        abs_obj, created = manager.create_abstraction(concept, metadata={"source": "test_script"})
        if created:
            print(f"   Created: {abs_obj.content[:30]}... ID: {abs_obj.id}")
            ids.append(abs_obj.id)
        else:
            print(f"   Duplicate: {concept[:30]}...")

    print("\n3. Verifying Persistence...")
    # Check retrieval
    retrieved = manager.get_abstraction(ids[0])
    if retrieved and retrieved.content == concepts[0]:
        print("   ✅ SQLite Persistence: Success")
    else:
        print("   ❌ SQLite Persistence: Failed")
        
    # Check Chroma
    results = manager.storage.collection.get(ids=[ids[0]])
    if results['ids']:
        print("   ✅ Chroma Persistence: Success")
    else:
        print("   ❌ Chroma Persistence: Failed")

    print("\n4. Testing Quality & Usage...")
    # Simulate usage
    print(f"   Initial Quality Score: {retrieved.quality_score}")
    
    manager.record_usage(ids[0], successful=True)
    manager.record_usage(ids[0], successful=True)
    
    # Manually trigger full quality update (normally happens in background/hooks)
    updated_abs = manager.get_abstraction(ids[0])
    update_metrics(updated_abs)
    manager.storage.update_metrics(updated_abs)
    
    final_abs = manager.get_abstraction(ids[0])
    print(f"   Updated Quality Score: {final_abs.quality_score}")
    
    if final_abs.usage_count == 2 and final_abs.quality_score > 0:
        print("   ✅ Usage Tracking: Success")
    else:
        print(f"   ❌ Usage Tracking: Failed (Usage: {final_abs.usage_count}, Score: {final_abs.quality_score})")

    print("\n✅ Core Pipeline Verification Complete!")

if __name__ == "__main__":
    test_core_pipeline()
