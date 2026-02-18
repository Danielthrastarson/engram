
import sys
import logging
from pathlib import Path
import time

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.cognitive import CognitiveLoop
from utils import config

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🧠 Starting Engram Cognitive Loop...")
    print(f"   Interval: {config.COGNITIVE_LOOP_INTERVAL_SEC}s")
    print(f"   Threshold: {config.UNCERTAINTY_THRESHOLD} quality score")
    print("   Press Ctrl+C to stop.")
    
    loop = CognitiveLoop()
    loop.start()

if __name__ == "__main__":
    main()
