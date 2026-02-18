import sys
from pathlib import Path
sys.path.append(str(Path("c:/Users/Notandi/Desktop/agi/engram-system")))

import logging
from core.clustering import ClusteringEngine
from core.decay import DecaySystem
from utils import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=str(config.LOG_DIR / "maintenance.log")
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

logger = logging.getLogger("Maintenance")

def run_daily_maintenance():
    logger.info("Starting Daily Maintenance Job")
    
    # 1. Run Decay & Pruning
    # (Delete old stuff first so we don't cluster garbage)
    try:
        logger.info("Phase 1: Decay & Pruning")
        decay_sys = DecaySystem()
        decay_sys.run_decay_cycle()
    except Exception as e:
        logger.error(f"Decay phase failed: {e}", exc_info=True)

    # 2. Run Clustering
    try:
        logger.info("Phase 2: Clustering")
        clustering = ClusteringEngine()
        clustering.perform_clustering()
        
        # 3. Update Centroids (The "Color" System)
        logger.info("Phase 3: Update Cluster Centroids")
        from core.router import ClusterCentroidManager
        centroid_mgr = ClusterCentroidManager()
        centroid_mgr.recalculate_centroids()
        
    except Exception as e:
        logger.error(f"Clustering/Centroid phase failed: {e}", exc_info=True)

    # 4. EVOLUTION SYSTEM
    try:
        logger.info("Phase 4: Evolution & Subconscious")
        from core.evolution import EvolutionManager
        from core.subconscious import Subconscious
        
        evo_mgr = EvolutionManager()
        
        # Check for Level Up
        msg = evo_mgr.check_for_evolution()
        logger.info(msg)
        
        # Run Dream Mode (if enabled)
        if evo_mgr.get_state("dream_mode_enabled"):
             sub = Subconscious()
             sub.dream()
             logger.info("Dream cycle complete.")
             
    except Exception as e:
        logger.error(f"Evolution phase failed: {e}", exc_info=True)
        
    logger.info("Daily Maintenance Job Complete")

if __name__ == "__main__":
    run_daily_maintenance()
