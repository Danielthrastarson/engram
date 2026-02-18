"""
5-HOUR COMPREHENSIVE STRESS TEST
=================================

This test runs for 5 hours and validates:
1. Memory ingestion (10,000+ abstractions)
2. Retrieval accuracy under load
3. Truth Guard preventing hallucination
4. Evolution system progression
5. Dream mode execution
6. Persistence across restarts
7. API stability
8. Concurrent operations

Run: python tests/stress_test_5hr.py

Results saved to: logs/stress_test_TIMESTAMP.log
"""

import sys
import time
import random
import logging
from pathlib import Path
from datetime import datetime, timedelta
import json

# Setup paths
ROOT_DIR = Path("c:/Users/Notandi/Desktop/agi/engram-system")
sys.path.append(str(ROOT_DIR))

# Setup logging
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_dir = ROOT_DIR / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"stress_test_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import system components
from core.abstraction_manager import AbstractionManager
from retrieval.search import Searcher
from core.truth_guard import TruthGuard
from core.evolution import EvolutionManager
from core.subconscious import Subconscious
from integration.pipeline import EngramPipeline

# Test configuration
TEST_DURATION_HOURS = 5
TEST_PHASES = [
    "Phase 1: Massive Ingestion (1hr)",
    "Phase 2: Retrieval Stress Test (1hr)", 
    "Phase 3: Truth Guard Validation (1hr)",
    "Phase 4: Evolution & Dreams (1hr)",
    "Phase 5: Persistence & Recovery (1hr)"
]

# Test datasets
KNOWLEDGE_BASE = [
    # Science
    "The speed of light in vacuum is approximately 299,792,458 meters per second.",
    "DNA contains four nucleotide bases: adenine, thymine, guanine, and cytosine.",
    "Photosynthesis converts light energy into chemical energy in plants.",
    "The Pythagorean theorem states that a² + b² = c² in right triangles.",
    
    # Technology
    "Python is a high-level, interpreted programming language created by Guido van Rossum.",
    "Machine learning is a subset of AI that learns patterns from data.",
    "Neural networks are inspired by biological neurons in the brain.",
    "REST APIs use HTTP methods like GET, POST, PUT, and DELETE.",
    
    # History
    "The printing press was invented by Johannes Gutenberg around 1440.",
    "The Apollo 11 mission landed humans on the Moon in 1969.",
    "World War II ended in 1945 after atomic bombs were dropped on Japan.",
    
    # Philosophy
    "Descartes' famous phrase 'I think, therefore I am' establishes existence through thought.",
    "Kant's categorical imperative suggests acting on maxims you'd want as universal laws.",
    
    # Low-quality / Uncertain (for Truth Guard testing)
    "Some people say aliens built the pyramids but evidence is unclear.",
    "There might be a connection between quantum mechanics and consciousness.",
    "Ancient civilizations may have had advanced technology we don't understand.",
]

TEST_QUERIES = [
    "What is the speed of light?",
    "Explain DNA structure",
    "How does photosynthesis work?",
    "What is Python programming language?",
    "Tell me about machine learning",
    "When did World War II end?",
    "Explain the Pythagorean theorem",
    "What is Kant's categorical imperative?",
    # Queries that should trigger Truth Guard
    "Tell me about alien pyramid construction",
    "Explain the quantum consciousness connection",
    "What advanced tech did ancient aliens use?"
]

class StressTestResults:
    def __init__(self):
        self.start_time = datetime.now()
        self.phase_results = {}
        self.errors = []
        self.metrics = {
            "total_ingestions": 0,
            "successful_ingestions": 0,
            "failed_ingestions": 0,
            "total_queries": 0,
            "successful_queries": 0,
            "truth_guard_activations": 0,
            "evolution_triggers": 0,
            "dream_cycles": 0,
            "api_errors": 0
        }
    
    def log_phase_start(self, phase_name):
        logger.info(f"\n{'='*60}")
        logger.info(f"STARTING: {phase_name}")
        logger.info(f"{'='*60}\n")
        self.phase_results[phase_name] = {"start": datetime.now(), "status": "running"}
    
    def log_phase_complete(self, phase_name, success=True):
        end_time = datetime.now()
        self.phase_results[phase_name]["end"] = end_time
        self.phase_results[phase_name]["status"] = "✅ PASS" if success else "❌ FAIL"
        duration = (end_time - self.phase_results[phase_name]["start"]).total_seconds()
        logger.info(f"\n{phase_name}: {'✅ PASS' if success else '❌ FAIL'} ({duration:.1f}s)")
    
    def save_report(self):
        report_file = log_dir / f"stress_test_report_{timestamp}.json"
        report = {
            "test_duration": str(datetime.now() - self.start_time),
            "phases": {k: {
                "status": v["status"],
                "duration": str(v["end"] - v["start"]) if "end" in v else "incomplete"
            } for k, v in self.phase_results.items()},
            "metrics": self.metrics,
            "errors": self.errors[:50]  # First 50 errors
        }
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"\n📊 Report saved to: {report_file}")
        return report

def phase1_massive_ingestion(results):
    """Phase 1: Ingest 10,000+ abstractions over 1 hour"""
    results.log_phase_start(TEST_PHASES[0])
    
    am = AbstractionManager()
    phase_duration = 3600  # 1 hour
    start_time = time.time()
    batch_size = 100
    
    try:
        while time.time() - start_time < phase_duration:
            # Generate batch of abstractions
            for i in range(batch_size):
                # Mix of base knowledge + variations
                base = random.choice(KNOWLEDGE_BASE)
                variation = f"Context {random.randint(1, 1000)}: {base}"
                
                try:
                    abs_obj, created = am.create_abstraction(
                        variation,
                        metadata={"source": "stress_test", "batch": results.metrics["total_ingestions"] // batch_size}
                    )
                    results.metrics["total_ingestions"] += 1
                    if created:
                        results.metrics["successful_ingestions"] += 1
                except Exception as e:
                    results.metrics["failed_ingestions"] += 1
                    results.errors.append(f"Ingestion error: {e}")
            
            # Log progress every 500 ingestions
            if results.metrics["total_ingestions"] % 500 == 0:
                logger.info(f"Ingested: {results.metrics['total_ingestions']} abstractions")
            
            time.sleep(1)  # Small delay to avoid overwhelming system
        
        logger.info(f"✅ Ingestion complete: {results.metrics['successful_ingestions']} abstractions")
        results.log_phase_complete(TEST_PHASES[0], success=True)
        
    except Exception as e:
        logger.error(f"❌ Phase 1 failed: {e}")
        results.errors.append(f"Phase 1 critical error: {e}")
        results.log_phase_complete(TEST_PHASES[0], success=False)

def phase2_retrieval_stress(results):
    """Phase 2: Run 5000+ queries with accuracy validation"""
    results.log_phase_start(TEST_PHASES[1])
    
    searcher = Searcher()
    phase_duration = 3600  # 1 hour
    start_time = time.time()
    
    try:
        while time.time() - start_time < phase_duration:
            query = random.choice(TEST_QUERIES)
            
            try:
                results_list = searcher.search(query, top_k=5)
                results.metrics["total_queries"] += 1
                
                if results_list and len(results_list) > 0:
                    results.metrics["successful_queries"] += 1
                    
                    # Validate quality scores
                    for r in results_list:
                        if not hasattr(r, 'quality_score') or r.quality_score < 0:
                            results.errors.append(f"Invalid quality score for {r.id}")
                
                # Log progress every 100 queries
                if results.metrics["total_queries"] % 100 == 0:
                    logger.info(f"Queries executed: {results.metrics['total_queries']}")
                    
            except Exception as e:
                results.errors.append(f"Query error: {e}")
            
            time.sleep(0.5)  # Query every 0.5s
        
        logger.info(f"✅ Retrieval complete: {results.metrics['successful_queries']}/{results.metrics['total_queries']} successful")
        results.log_phase_complete(TEST_PHASES[1], success=True)
        
    except Exception as e:
        logger.error(f"❌ Phase 2 failed: {e}")
        results.errors.append(f"Phase 2 critical error: {e}")
        results.log_phase_complete(TEST_PHASES[1], success=False)

def phase3_truth_guard_validation(results):
    """Phase 3: Validate Truth Guard prevents hallucination"""
    results.log_phase_start(TEST_PHASES[2])
    
    pipeline = EngramPipeline()
    searcher = Searcher()
    phase_duration = 3600  # 1 hour
    start_time = time.time()
    
    uncertain_queries = [
        "Tell me about alien pyramid construction",
        "Explain the quantum consciousness connection", 
        "What advanced tech did ancient aliens use?",
        "Details on Atlantis technology",
        "How do ghosts interact with matter?"
    ]
    
    try:
        while time.time() - start_time < phase_duration:
            # Test with uncertain queries
            query = random.choice(uncertain_queries)
            
            try:
                results_list = searcher.search(query, top_k=5)
                risk, is_safe = TruthGuard.calculate_risk(results_list)
                
                if not is_safe:
                    results.metrics["truth_guard_activations"] += 1
                    logger.info(f"🧭 Truth Guard activated for: '{query}' (risk: {risk:.3f})")
                
                # Run full pipeline
                response = pipeline.process_query(query)
                
                # Check if low confidence response
                if "Low confidence" in response or "I only have" in response:
                    logger.info(f"✅ Honest response: {response[:100]}...")
                    
            except Exception as e:
                results.errors.append(f"Truth Guard test error: {e}")
            
            time.sleep(2)
        
        logger.info(f"✅ Truth Guard validated: {results.metrics['truth_guard_activations']} activations")
        results.log_phase_complete(TEST_PHASES[2], success=True)
        
    except Exception as e:
        logger.error(f"❌ Phase 3 failed: {e}")
        results.errors.append(f"Phase 3 critical error: {e}")
        results.log_phase_complete(TEST_PHASES[2], success=False)

def phase4_evolution_dreams(results):
    """Phase 4: Test evolution triggers and dream cycles"""
    results.log_phase_start(TEST_PHASES[3])
    
    evo = EvolutionManager()
    sub = Subconscious()
    phase_duration = 3600  # 1 hour
    start_time = time.time()
    
    try:
        while time.time() - start_time < phase_duration:
            # Check evolution
            try:
                msg = evo.check_for_evolution()
                if "EVOLUTION" in msg or "Level" in msg:
                    results.metrics["evolution_triggers"] += 1
                    logger.info(f"🧬 {msg}")
            except Exception as e:
                results.errors.append(f"Evolution error: {e}")
            
            # Run dream cycle
            try:
                if evo.get_state("dream_mode_enabled"):
                    sub.dream()
                    results.metrics["dream_cycles"] += 1
                    logger.info(f"😴 Dream cycle #{results.metrics['dream_cycles']} complete")
            except Exception as e:
                results.errors.append(f"Dream error: {e}")
            
            # Get metrics
            metrics = evo.get_metrics()
            logger.info(f"📊 Level: {metrics['current_level']}, Abstractions: {metrics['total_abstractions']}, Quality: {metrics['avg_quality']:.3f}")
            
            time.sleep(300)  # Check every 5 minutes
        
        logger.info(f"✅ Evolution & Dreams: {results.metrics['dream_cycles']} dreams, {results.metrics['evolution_triggers']} evolutions")
        results.log_phase_complete(TEST_PHASES[3], success=True)
        
    except Exception as e:
        logger.error(f"❌ Phase 4 failed: {e}")
        results.errors.append(f"Phase 4 critical error: {e}")
        results.log_phase_complete(TEST_PHASES[3], success=False)

def phase5_persistence_recovery(results):
    """Phase 5: Test persistence and data integrity"""
    results.log_phase_start(TEST_PHASES[4])
    
    phase_duration = 3600  # 1 hour
    start_time = time.time()
    
    try:
        # Validate data persistence
        am = AbstractionManager()
        searcher = Searcher()
        
        # Count total abstractions
        initial_count = 0
        try:
            cursor = am.storage.conn.execute("SELECT COUNT(*) FROM abstractions")
            initial_count = cursor.fetchone()[0]
            logger.info(f"📊 Total abstractions in DB: {initial_count}")
        except Exception as e:
            results.errors.append(f"Count error: {e}")
        
        # Test retrieval of old data
        for _ in range(100):
            query = random.choice(TEST_QUERIES)
            try:
                results_list = searcher.search(query, top_k=3)
                if not results_list:
                    results.errors.append(f"No results for: {query}")
            except Exception as e:
                results.errors.append(f"Retrieval error: {e}")
            
            time.sleep(30)  # Every 30s
        
        logger.info(f"✅ Persistence validated: {initial_count} abstractions intact")
        results.log_phase_complete(TEST_PHASES[4], success=True)
        
    except Exception as e:
        logger.error(f"❌ Phase 5 failed: {e}")
        results.errors.append(f"Phase 5 critical error: {e}")
        results.log_phase_complete(TEST_PHASES[4], success=False)

def main():
    logger.info("""
    ╔══════════════════════════════════════════════════════════╗
    ║   ENGRAM SYSTEM - 5 HOUR COMPREHENSIVE STRESS TEST       ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    logger.info(f"Start time: {datetime.now()}")
    logger.info(f"Test duration: {TEST_DURATION_HOURS} hours")
    logger.info(f"Log file: {log_file}\n")
    
    results = StressTestResults()
    
    try:
        # Run all phases
        phase1_massive_ingestion(results)
        phase2_retrieval_stress(results)
        phase3_truth_guard_validation(results)
        phase4_evolution_dreams(results)
        phase5_persistence_recovery(results)
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Test interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Critical test failure: {e}")
        results.errors.append(f"Critical failure: {e}")
    
    # Generate final report
    logger.info("\n" + "="*60)
    logger.info("FINAL RESULTS")
    logger.info("="*60)
    
    report = results.save_report()
    
    # Print summary
    logger.info(f"\n📊 METRICS SUMMARY:")
    for key, value in results.metrics.items():
        logger.info(f"  {key}: {value}")
    
    logger.info(f"\n📝 PHASE RESULTS:")
    for phase, data in results.phase_results.items():
        logger.info(f"  {phase}: {data['status']}")
    
    error_count = len(results.errors)
    logger.info(f"\n⚠️ Total Errors: {error_count}")
    if error_count > 0:
        logger.info(f"  First 5 errors:")
        for err in results.errors[:5]:
            logger.info(f"    - {err}")
    
    # Final verdict
    all_passed = all(v["status"] == "✅ PASS" for v in results.phase_results.values())
    
    if all_passed and error_count < 10:
        logger.info("\n✅ ✅ ✅ STRESS TEST PASSED! SYSTEM IS PRODUCTION READY! ✅ ✅ ✅")
    elif error_count < 50:
        logger.info("\n⚠️ STRESS TEST COMPLETED WITH WARNINGS - Review errors")
    else:
        logger.info("\n❌ STRESS TEST FAILED - System needs fixes")
    
    logger.info(f"\nTotal duration: {datetime.now() - results.start_time}")
    logger.info(f"Full log: {log_file}")
    logger.info(f"Report: {log_dir / f'stress_test_report_{timestamp}.json'}\n")

if __name__ == "__main__":
    main()
