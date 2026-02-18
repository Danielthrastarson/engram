
import threading
import time
import random
import unittest
import logging
from reasoning.awake_engine import AwakeEngine
from core.abstraction import Abstraction

# Disable logging for stress test
logging.basicConfig(level=logging.CRITICAL)

class MockMarket:
    def register_agent(self, *args, **kwargs): pass
    def submit_proposal(self, *args, **kwargs): pass

class TestAwakeLocking(unittest.TestCase):
    def test_concurrent_access(self):
        print("🚀 Starting Concurrency Stress Test...")
        engine = AwakeEngine()
        engine.set_market(MockMarket())
        
        # Populate queue
        for i in range(100):
            engine.workload_queue.append(Abstraction(
                content=f"Item {i}", 
                embedding_hash="123", 
                embedding=[]
            ))
            
        errors = []
            
        def bid_loop():
            try:
                for _ in range(5000):
                    bid = engine.construct_bid()
                    # Access queue length inside lock
                    # construct_bid does this.
                    # Verify no crash
            except Exception as e:
                errors.append(e)
                
        def consume_loop():
            try:
                for _ in range(5000):
                    # Simulate _think logic (Lock -> Pop)
                    with engine._lock:
                        if engine.workload_queue:
                            engine.workload_queue.pop(0)
                        else:
                            # Refill
                            engine.workload_queue.append(Abstraction(
                                content="Refill", 
                                embedding_hash="REF", 
                                embedding=[]
                            ))
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=bid_loop)
        t2 = threading.Thread(target=consume_loop)
        
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()
        
        if errors:
            print(f"❌ Errors found: {errors}")
            self.fail(f"Concurrency errors: {errors}")
        else:
            print("✅ Concurrency Test Passed (10,000 Ops)")

if __name__ == "__main__":
    unittest.main()
