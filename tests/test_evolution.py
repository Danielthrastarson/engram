
import sys
import time
from pathlib import Path

# Add project root to path
ROOT_DIR = Path("c:/Users/Notandi/Desktop/agi/engram-system")
sys.path.append(str(ROOT_DIR))

from core.evolution import EvolutionManager
from core.subconscious import Subconscious
from core.abstraction_manager import AbstractionManager

def test_evolution_system():
    print("🧬 TESTING EVOLUTION SYSTEM...")
    
    evo = EvolutionManager()
    am = AbstractionManager()
    
    # Reset state for testing
    print("\n1️⃣ Resetting Evolution State...")
    evo.set_state("evolution_level", 0)
    evo.set_state("dream_mode_enabled", False)
    evo.set_state("implicit_priming_enabled", False)
    
    # Verify Reset
    level = evo.get_state("evolution_level", 0)
    print(f"   Current Level: {level}")
    if level != 0:
        print("   ❌ FAIL: Reset failed.")
        return

    # 2. Simulate Growth (Force Metrics via Mocking or direct SQL)
    # We need 100 abstractions and avg quality > 0.6 for Level 1
    print("\n2️⃣ Simulating Growth (Mocking Metrics)...")
    
    # We can't easily insert 100 abstractions quickly in a test without valid embeddings (slow).
    # So we will mock the `get_metrics` method on the instance for this test.
    
    original_get_metrics = evo.get_metrics
    
    def mock_get_metrics():
        return {
            "total_abstractions": 105,
            "avg_quality": 0.75,
            "avg_compression": 2.5,
            "total_refinements": 50,
            "total_reuse": 10,
            "dream_insights": 0,
            "current_level": 0
        }
    
    evo.get_metrics = mock_get_metrics
    
    # 3. Trigger Check
    print("   Running Check for Evolution...")
    msg = evo.check_for_evolution()
    print(f"   Result: {msg}")
    
    # 4. Verify Level Up
    new_level = evo.get_state("evolution_level")
    dream_enabled = evo.get_state("dream_mode_enabled")
    
    print(f"   New Level: {new_level}")
    print(f"   Dream Mode: {dream_enabled}")
    
    if new_level == 1 and dream_enabled:
        print("   ✅ SUCCESS: System evolved to Level 1!")
    else:
        print("   ❌ FAIL: System did not evolve.")
        
    # 5. Test Dream Mode
    print("\n5️⃣ Testing Dream Mode execution...")
    # Trigger dream
    sub = Subconscious()
    # verify it runs without crashing (it might not find high quality nodes in empty DB, but should handle gracefully)
    try:
        sub.dream()
        print("   ✅ Dream cycle ran successfully.")
    except Exception as e:
        print(f"   ❌ Dream cycle crashed: {e}")

if __name__ == "__main__":
    test_evolution_system()
