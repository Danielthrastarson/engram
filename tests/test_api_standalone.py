
import sys
import time
import requests
import multiprocessing
import uvicorn
from pathlib import Path

# Add project root to path
ROOT_DIR = Path("c:/Users/Notandi/Desktop/agi/engram-system")
sys.path.append(str(ROOT_DIR))

# Import app (must be top level for pickling sometimes, but inside helper is fine for spawn)
import subprocess

# ...

def test_api_standalone():
    print("🧠 TESTING VISUAL CORTEX API (STANDALONE SUBPROCESS)...")
    
    # Start server as subprocess
    # Run the uvicorn command directly
    cmd = [sys.executable, "-m", "uvicorn", "core.api:app", "--host", "127.0.0.1", "--port", "8002", "--app-dir", str(ROOT_DIR)]
    
    p = subprocess.Popen(cmd)
    
    try:
        # Retry loop for connection
        connected = False
        for i in range(15): # 30 seconds max
            try:
                requests.get("http://127.0.0.1:8002/docs", timeout=1)
                connected = True
                print("   ✅ Server is up.", flush=True)
                break
            except:
                time.sleep(2)
                print(f"   Errors connecting... retry {i+1}/15", flush=True)
        
        if not connected:
            print("   ❌ CRITICAL: Server failed to start.", flush=True)
            return

        # Test Clusters
        print("\n🌌 Testing /api/clusters...", flush=True)
        try:
            r = requests.get("http://127.0.0.1:8002/api/clusters")
            if r.status_code == 200:
                data = r.json()
                print(f"   ✅ SUCCESS: Got {len(data)} clusters.", flush=True)
            else:
                print(f"   ❌ FAIL: Status {r.status_code}", flush=True)
        except Exception as e:
             print(f"   ❌ FAIL: Connection Error {e}", flush=True)

        # Test Abstractions
        print("\n⭐ Testing /api/abstractions...", flush=True)
        try:
            r = requests.get("http://127.0.0.1:8002/api/abstractions")
            if r.status_code == 200:
                data = r.json()
                print(f"   ✅ SUCCESS: Got {len(data)} abstractions.", flush=True)
                if len(data) > 0:
                    print(f"   Sample: {data[0]}", flush=True)
            else:
                print(f"   ❌ FAIL: Status {r.status_code}", flush=True)
        except Exception as e:
            print(f"   ❌ FAIL: Connection Error {e}", flush=True)
            
    finally:
        print("\n🛑 Stopping Server...", flush=True)
        p.terminate()
        p.wait()

if __name__ == "__main__":
    test_api_standalone()
