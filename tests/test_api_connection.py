
import sys
import time
import requests
import threading
from pathlib import Path
import uvicorn

sys.path.append(str(Path("c:/Users/Notandi/Desktop/agi/engram-system")))
from core.api import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="error")

def test_api():
    print("🧠 TESTING VISUAL CORTEX API...")
    
    # Start server in background thread
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(3) # Wait for startup
    
    try:
        # Test Clusters
        print("\n🌌 Testing /api/clusters...")
        r = requests.get("http://127.0.0.1:8001/api/clusters")
        if r.status_code == 200:
            data = r.json()
            print(f"   ✅ SUCCESS: Got {len(data)} clusters.")
        else:
            print(f"   ❌ FAIL: Status {r.status_code}")

        # Test Abstractions
        print("\n⭐ Testing /api/abstractions...")
        r = requests.get("http://127.0.0.1:8001/api/abstractions")
        if r.status_code == 200:
            data = r.json()
            print(f"   ✅ SUCCESS: Got {len(data)} abstractions.")
            if len(data) > 0:
                print(f"   Sample: {data[0]}")
        else:
            print(f"   ❌ FAIL: Status {r.status_code}")
            
    except Exception as e:
         print(f"   ❌ CRASH: {e}")

if __name__ == "__main__":
    test_api()
