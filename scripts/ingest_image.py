
import sys
import argparse
from pathlib import Path
from PIL import Image
import numpy as np

# Add project root to path
# Use absolute path for safety in this environment
ROOT_DIR = Path("c:/Users/Notandi/Desktop/agi/engram-system")
sys.path.append(str(ROOT_DIR))

from core.abstraction_manager import AbstractionManager
from core.embedding import EmbeddingHandler
from core.storage import EngramStorage

def ingest_image(image_path: str, description: str = None):
    print(f"👁️ Eye Opening: Ingesting {image_path}...")
    
    manager = AbstractionManager()
    
    # 1. Load Image
    try:
        img = Image.open(image_path)
    except Exception as e:
        print(f"❌ Error loading image: {e}")
        return

    # 2. Generate Description (if not provided, we could use a VLM, but for V1 we assume user provides or filename)
    if not description:
        description = Path(image_path).stem.replace("_", " ").title()
        print(f"   ℹ️ No description provided. Using filename: '{description}'")

    # 3. Create Abstraction
    # a. Generate embedding manually to ensure we use the image
    # The manager.create_abstraction usually embeds text. 
    # We need to hack/extend it or just do it manually here for Phase 9 prototype.
    
    # A better way: Manager should support image input.
    # But for now, let's do it manually to verify components.
    
    embedding = manager.embedder.generate_embedding(img)
    
    # Create the abstraction object
    # We pass the description as the "content" so text search still works (CLIP aligned space)
    # But use the IMAGE embedding.
    
    # HACK: Manager.create_abstraction re-embeds the content. 
    # We should update Manager to accept `embedding_override`.
    # For now, let's just insert directly to storage to prove the point.
    
    from core.abstraction import Abstraction
    
    abs_obj = Abstraction(
        content=f"[IMAGE] {description}",
        image_path=str(Path(image_path).absolute()),
        embedding_hash="image_" + str(hash(image_path)), # Simple hash for now
        metadata={"type": "image", "source": image_path}
    )
    abs_obj.update_hash() # Actually, let's use the object's logic for hash if possible, but we just set it.
    
    # Save
    manager.storage.add_abstraction(abs_obj, embedding)
    print(f"✅ Image ingested successfully. ID: {abs_obj.id}")
    print(f"   Content: {abs_obj.content}")
    print(f"   Image Path: {abs_obj.image_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest an image into Engram parameters")
    parser.add_argument("path", help="Path to image file")
    parser.add_argument("--desc", help="Text description (optional)", default=None)
    
    args = parser.parse_args()
    ingest_image(args.path, args.desc)
