
import sys
import argparse
from pathlib import Path
from PIL import Image

# Add project root to path
ROOT_DIR = Path("c:/Users/Notandi/Desktop/agi/engram-system")
sys.path.append(str(ROOT_DIR))

from core.abstraction_manager import AbstractionManager
from core.storage import EngramStorage
from scripts.ingest_image import ingest_image

def test_image_flow(image_path):
    print("👁️ TESTING MULTI-MODAL EYE...")
    
    # 1. Ingest Image
    print("\n1️⃣ Ingesting Image...")
    try:
        # Use ingest_image function from script
        # Mock argparse or just call function directly
        # Let's import the function logic or call it via shell?
        # Calling function directly is cleaner for test.
        
        # We need to adapt the script to be importable or just copy logic.
        # I made it importable in previous step by defining `ingest_image` function.
        
        ingest_image(image_path)
            
    except Exception as e:
        print(f"❌ Ingestion Failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # 2. Search for it using TEXT
    print("\n2️⃣ Searching with Text Query: 'red square shape'")
    manager = AbstractionManager()
    
    # We use the searcher
    from retrieval.search import Searcher
    searcher = Searcher()
    
    results = searcher.search("red square shape", top_k=5)
    
    found = False
    for res in results:
        print(f"   - Found: {res.content} (Score: {res.quality_score})")
        if "[IMAGE]" in res.content:
            found = True
            print("   ✅ SUCCESS: Image retrieved via text query!")
            
    if not found:
        print("   ❌ FAIL: Image not found in top results.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("image_path", help="Path to test image")
    args = parser.parse_args()
    
    test_image_flow(args.image_path)
