
import uvicorn
import os
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path("c:/Users/Notandi/Desktop/agi/engram-system")
sys.path.append(str(ROOT_DIR))

def main():
    print("🧠 Starting Engram Visual Cortex...")
    print("🌌 Access the Brain at: http://localhost:8000")
    
    # Run Uvicorn
    # core.api:app points to the FastAPI instance we created
    uvicorn.run("core.api:app", host="0.0.0.0", port=8000, reload=True, app_dir=str(ROOT_DIR))

if __name__ == "__main__":
    main()
