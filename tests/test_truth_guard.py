import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path("c:/Users/Notandi/Desktop/agi/engram-system")
sys.path.append(str(ROOT_DIR))

from core.truth_guard import TruthGuard
from core.abstraction_manager import AbstractionManager
from retrieval.search import Searcher

def test_truth_guard():
    print("🧭 TESTING TRUTH GUARD (NORTH ENFORCER)...\n")
    
    am = AbstractionManager()
    searcher = Searcher()
    
    # Test 1: High-confidence query (should pass)
    print("1️⃣ Testing HIGH CONFIDENCE scenario...")
    query_good = "What is Python?"
    results_good = searcher.search(query_good, top_k=5)
    
    if results_good:
        risk, is_safe = TruthGuard.calculate_risk(results_good)
        print(f"   Risk Score: {risk:.3f}")
        print(f"   Is Safe: {is_safe}")
        
        forced = TruthGuard.enforce_honest_response(query_good, risk, results_good)
        if forced:
            print(f"   Response: {forced[:100]}...")
        else:
            print("   ✅ PASS: Normal LLM reasoning allowed")
    else:
        print("   ⚠️ No results found")
    
    # Test 2: Low-confidence query (should force honesty)
    print("\n2️⃣ Testing LOW CONFIDENCE scenario...")
    
    # Create some weak abstractions for testing
    weak1, _ = am.create_abstraction(
        "Something vague about a topic",
        metadata={"source": "unknown"}
    )
    weak1.quality_score = 0.2
    weak1.decay_score = 0.8
    am.storage.update_metrics(weak1)
    
    weak2, _ = am.create_abstraction(
        "Another uncertain memory",
        metadata={"source": "unknown"}
    )
    weak2.quality_score = 0.15
    weak2.decay_score = 0.9
    am.storage.update_metrics(weak2)
    
    weak_results = [weak1, weak2]
    risk, is_safe = TruthGuard.calculate_risk(weak_results)
    
    print(f"   Risk Score: {risk:.3f}")
    print(f"   Is Safe: {is_safe}")
    
    forced = TruthGuard.enforce_honest_response("Tell me about quantum computing", risk, weak_results)
    if forced:
        print(f"   ✅ FORCED HONESTY:\n   {forced}")
    else:
        print("   ❌ FAIL: Should have forced honesty")
    
    print("\n✅ Truth Guard test complete!")

if __name__ == "__main__":
    test_truth_guard()
