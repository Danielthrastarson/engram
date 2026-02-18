# scripts/bulk_ingest.py
# Bulk ingestion of .txt, .md, .json files into the Engram system

import sys
import os
import json
import glob
import argparse
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from integration.pipeline import EngramPipeline

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


def ingest_file(pipeline, filepath: str, source: str) -> bool:
    """Ingest a single file"""
    try:
        ext = os.path.splitext(filepath)[1].lower()
        
        if ext == ".json":
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Handle both {"content": "..."} and ["item1", "item2"]
            if isinstance(data, dict):
                text = data.get("content", json.dumps(data))
            elif isinstance(data, list):
                for item in data:
                    content = item if isinstance(item, str) else json.dumps(item)
                    pipeline.ingest(content, source=source)
                return True
            else:
                text = str(data)
        else:
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
        
        if not text.strip():
            return False
        
        # Split long texts into chunks (~500 chars each)
        if len(text) > 600:
            chunks = _chunk_text(text, max_chars=500)
            for chunk in chunks:
                if chunk.strip():
                    pipeline.ingest(chunk.strip(), source=source)
        else:
            pipeline.ingest(text.strip(), source=source)
        
        return True
    except Exception as e:
        logger.error(f"Failed to ingest {filepath}: {e}")
        return False


def _chunk_text(text: str, max_chars: int = 500) -> list:
    """Split text into chunks at sentence boundaries"""
    sentences = text.replace("\n\n", ". ").split(". ")
    chunks = []
    current = []
    current_len = 0
    
    for sent in sentences:
        if current_len + len(sent) > max_chars and current:
            chunks.append(". ".join(current) + ".")
            current = [sent]
            current_len = len(sent)
        else:
            current.append(sent)
            current_len += len(sent)
    
    if current:
        chunks.append(". ".join(current))
    
    return chunks


def main():
    parser = argparse.ArgumentParser(description="Bulk ingest files into Engram")
    parser.add_argument("directory", help="Directory containing files to ingest")
    parser.add_argument("--source", default="bulk_ingest", help="Source label")
    parser.add_argument("--extensions", default=".txt,.md,.json", help="File extensions")
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"Error: {args.directory} is not a directory")
        sys.exit(1)
    
    exts = [e.strip() for e in args.extensions.split(",")]
    
    # Find all matching files
    files = []
    for ext in exts:
        pattern = os.path.join(args.directory, f"**/*{ext}")
        files.extend(glob.glob(pattern, recursive=True))
    
    if not files:
        print(f"No files found matching {exts} in {args.directory}")
        sys.exit(0)
    
    print(f"Found {len(files)} files to ingest")
    print("Initializing Engram pipeline...")
    pipeline = EngramPipeline()
    
    success = 0
    failed = 0
    
    for i, filepath in enumerate(files):
        print(f"  [{i+1}/{len(files)}] {os.path.basename(filepath)}...", end=" ")
        if ingest_file(pipeline, filepath, args.source):
            success += 1
            print("✓")
        else:
            failed += 1
            print("✗")
    
    print(f"\nDone: {success} ingested, {failed} failed")
    pipeline.stop_engines()


if __name__ == "__main__":
    main()
