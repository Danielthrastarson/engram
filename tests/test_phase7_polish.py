
import sys
import time
import pprint
from pathlib import Path
import numpy as np

# Add project root to path
sys.path.append(str(Path("c:/Users/Notandi/Desktop/agi/engram-system")))

from core.abstraction_manager import AbstractionManager
from core.storage import EngramStorage
from integration.pipeline import EngramPipeline
from utils import config

def test_phase7_fixes():
    print("🧹 STARTING PHASE 7 POLISH VERIFICATION...")
    
    manager = AbstractionManager()
    storage = EngramStorage()
    pipeline = EngramPipeline()
    
    # 1. Test Default Values & Embedding Type
    print("\n🧪 TEST 1: Creation Defaults & Numpy Embeddings")
    content = f"Phase 7 Test Content {time.time()}"
    abs_obj, created = manager.create_abstraction(content, metadata={"test": True})
    
    if not created:
        print("   ❌ FAIL: Failed to create new abstraction.")
        return
        
    print(f"   Created ID: {abs_obj.id}")
    
    # Check Defaults
    if abs_obj.compression_ratio == 1.0 and abs_obj.decay_score == 0.0:
        print("   ✅ SUCCESS: Default values applied (Compression=1.0, Decay=0.0)")
    else:
        print(f"   ❌ FAIL: Defaults missmatch. Comp={abs_obj.compression_ratio}, Decay={abs_obj.decay_score}")

    # Check Embedding Type in Storage (via private access for test)
    # trigger a save to ensure it went through storage.add_abstraction
    # We can check what create_abstraction returned, but better to check DB or just trust no crash means it worked.
    # Actually, let's check `manager.embedder.generate_embedding` return type
    emb = manager.embedder.generate_embedding("test")
    if isinstance(emb, np.ndarray):
        print("   ✅ SUCCESS: EmbeddingGenerator returns np.ndarray")
    else:
        print(f"   ❌ FAIL: Embedding return type is {type(emb)}")

    # 2. Test Duplicate Logic
    print("\n🧪 TEST 2: Duplicate Prevention (Embedding Hash)")
    abs_dup, created_dup = manager.create_abstraction(content, metadata={"test": "duplicate"})
    
    if not created_dup and abs_dup.id == abs_obj.id:
        print("   ✅ SUCCESS: Duplicate rejected and original returned.")
    else:
        print(f"   ❌ FAIL: Duplicate creation allowed or wrong object. Created={created_dup}")

    # 3. Test Quality Scoring
    print("\n🧪 TEST 3: Real Quality Scoring")
    try:
        print(f"   Initial Score: {abs_obj.quality_score}")
        
        # Simulate usage
        manager.record_usage(abs_obj.id, successful=True)
        manager.record_usage(abs_obj.id, successful=True)
        
        # Fetch updated
        updated_abs = manager.get_abstraction(abs_obj.id)
        if updated_abs:
            print(f"   Updated Score: {updated_abs.quality_score}")
        
            # Usage=2, Success=2. 
            if updated_abs.quality_score > 0.0:
                print("   ✅ SUCCESS: Quality score increased/calculated.")
            else:
                print("   ⚠️ WARNING: Quality score remains 0.0 (Check formula weights).")
        else:
             print("   ❌ FAIL: get_abstraction returned None")
             
    except Exception as e:
        print(f"   ❌ FAIL: Crash during Quality Scoring test: {e}")
        import traceback
        traceback.print_exc()

    # 4. Test Pipeline Integrity (Hyperfocus)
    print("\n🧪 TEST 4: End-to-End Pipeline (Hyperfocus Check)")
    query = "How to test phase 7?"
    try:
        response = pipeline.process_query(query)
        print("   ✅ SUCCESS: Pipeline processed query without crashing.")
    except Exception as e:
        print(f"   ❌ FAIL: Pipeline crash: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_phase7_fixes()
