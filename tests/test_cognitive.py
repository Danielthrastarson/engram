
import sys
from pathlib import Path
sys.path.append(str(Path("c:/Users/Notandi/Desktop/agi/engram-system")))

import time
import logging
from core.abstraction_manager import AbstractionManager
from core.cognitive import CognitiveLoop
from utils import config

# Add a test hook to trigger "weakness"
def test_cognitive_loop():
    print("🚀 TESTING COGNITIVE LOOP...")
    
    # 1. Setup
    manager = AbstractionManager()
    loop = CognitiveLoop()
    
    # 2. Create a "Weak" Abstraction
    # We deliberately create one with "REFINE_ME" which acts as a trigger in our LLM mock
    content = "This is a messy abstraction. REFINE_ME. It has bad grammar."
    abs_obj, _ = manager.create_abstraction(content)
    
    # Manually degrade its quality score in DB to ensure it's picked up (lowest possible)
    msg = "Forcing low quality..."
    manager.storage.conn.execute("UPDATE abstractions SET quality_score = -1.0 WHERE id = ?", (abs_obj.id,))
    manager.storage.conn.commit()
    print(f"   Created weak abstraction: {abs_obj.id} (Content: '{content[:30]}...')")
    
    # 3. Run Loop Step
    print("   Running Cognitive Loop Step...")
    # Temporarily ensure config allows it
    config.ENABLE_COGNITIVE_LOOP = True
    config.USE_LLM_COMPRESSION = False # Use simulation mode for deterministic test
    
    loop.step()
    
    # 4. Verify Update
    updated_obj = manager.get_abstraction(abs_obj.id)
    print(f"   New Content: '{updated_obj.content}'")
    print(f"   New Version: {updated_obj.version}")
    
    if "REFINED" in updated_obj.content and updated_obj.version > 1:
        print("✅ SUCCESS: Abstraction was refined and version incremented.")
    else:
        print("❌ FAIL: Abstraction was not refined.")
        
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO) # Enable logs to see loop output
    test_cognitive_loop()
