
import sys
import logging
from pathlib import Path
import time
import statistics

# Add project root to path
sys.path.append(str(Path("c:/Users/Notandi/Desktop/agi/engram-system")))

from integration.pipeline import EngramPipeline
from core.abstraction_manager import AbstractionManager
from utils import config

# Sample Corpus: Python Concepts
CORPUS = [
    {
        "text": "Python is a high-level, interpreted programming language. It is known for its readability and use of indentation. Python supports multiple programming paradigms, including structured, object-oriented, and functional programming.",
        "source": "python_docs"
    },
    {
        "text": "The Global Interpreter Lock (GIL) is a mutex that protects access to Python objects, preventing multiple threads from executing Python bytecodes at once. This lock is necessary mainly because CPython's memory management is not thread-safe.",
        "source": "python_docs"
    },
    {
        "text": "List comprehensions provide a concise way to create lists. Common applications are to make new lists where each element is the result of some operations applied to each member of another sequence or iterable.",
        "source": "python_tutorial"
    },
    {
        "text": "A decorator in Python is a design pattern that allows a user to add new functionality to an existing object without modifying its structure. Decorators are usually called before the definition of a function you want to decorate.",
        "source": "python_tutorial"
    },
    {
        "text": "Python's garbage collection mechanism uses reference counting and a cyclic garbage collector. Reference counting tracks the number of references to an object and deallocates it when the count reaches zero.",
        "source": "python_docs"
    }
]

def test_corpus_ingestion():
    print("🚀 STARTING CORPUS INGESTION TEST...")
    
    # 1. Setup
    pipeline = EngramPipeline()
    manager = AbstractionManager()
    
    # ensure we start fresh-ish or just track new items? 
    # For this test, let's just ingest and measure.
    
    start_time = time.time()
    initial_count = len(manager.storage.conn.execute("SELECT id FROM abstractions").fetchall())
    
    # 2. Ingest
    print(f"   Ingesting {len(CORPUS)} documents...")
    for item in CORPUS:
        pipeline.ingest(item["text"], source=item["source"])
        sys.stdout.write(".")
        sys.stdout.flush()
    print("\n   ✅ Ingestion Complete.")
    
    # 3. Validation & Metrics
    end_time = time.time()
    final_count = len(manager.storage.conn.execute("SELECT id FROM abstractions").fetchall())
    new_items = final_count - initial_count
    
    print("\n📊 PERFORMANCE METRICS:")
    print(f"   - Time Taken: {end_time - start_time:.2f}s")
    print(f"   - New Abstractions: {new_items}")
    
    # Calculate Compression Ratio (Simulated for V1 since we use full text mostly)
    # 3. Simulate Usage & Verify Retrieval
    print("\n🔎 VERIFYING RETRIEVAL & GENERATING USAGE...")
    query = "Why cannot Python threads run in parallel?"
    
    # Run query 3 times to boost quality score
    for i in range(3):
         pipeline.process_query(query) # This calls record_usage internall
    
    # Check raw retrieval for verification
    retrieved_items = pipeline.searcher.search(query, top_k=3)
    found_concepts = [item.content for item in retrieved_items]
    
    print(f"   Query: '{query}'")
    print(f"   Retrieved {len(retrieved_items)} items:")
    for item in retrieved_items:
        print(f"    - [{item.id[:6]}] {item.content[:100]}...")

    # Verification Logic
    success = any("GIL" in c or "lock" in c or "threads" in c for c in found_concepts)
    
    if success:
        print("   ✅ SUCCESS: Relevant concept retrieved.")
    else:
        print("   ❌ FAIL: Concept missing.")

    # 4. Analyze Quality & Compression (Now that usage is recorded)
    print("\n📊 ABSTRACTION QUALITY ANALYSIS:")
    
    # Fetch details of the new abstractions
    # Note: process_query calls record_usage which updates the DB
    cursor = manager.storage.conn.execute(
        "SELECT id, content, metadata, quality_score FROM abstractions ORDER BY created_at DESC LIMIT ?", 
        (len(CORPUS),)
    )
    rows = cursor.fetchall()
    
    total_compression = 0
    valid_abstractions = 0
    
    print(f"   {'Content Preview':<40} | {'Orig':<5} | {'Abst':<5} | {'Ratio':<5} | {'Qual':<5}")
    print("-" * 88)
    
    for row in rows:
        abs_id, content, metadata_json, quality = row
        import json
        metadata = json.loads(metadata_json)
        original_len = metadata.get("original_length", len(content)) 
        
        abs_len = len(content)
        # Avoid division by zero
        ratio = original_len / abs_len if abs_len > 0 else 1.0
        
        total_compression += ratio
        valid_abstractions += 1
        
        preview = content[:37] + "..." if len(content) > 37 else content
        print(f"   {preview:<40} | {original_len:<5} | {abs_len:<5} | {ratio:<5.2f} | {quality:<5.2f}")

    avg_compression = total_compression / valid_abstractions if valid_abstractions > 0 else 0
    print("-" * 88)
    print(f"   ✅ Average Compression Ratio: {avg_compression:.2f}x")
    
    if avg_compression > 1.1:
        print("   ✅ SUCCESS: Compression is active (>1.1x).")
    else:
        print(f"   ⚠️ WARNING: Low compression (Ratio {avg_compression:.2f}).")

if __name__ == "__main__":
    test_corpus_ingestion()
