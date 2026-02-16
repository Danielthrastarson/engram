from typing import Dict, Any
from pathlib import Path

# Base Paths
BASE_DIR = Path("c:/Users/Notandi/Desktop/agi/engram-system")
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

# Database Config
CHROMA_PERSIST_DIRECTORY = str(DATA_DIR / "chroma_db")
METADATA_DB_PATH = str(DATA_DIR / "metadata.db")

# Embedding Config
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  # Fast, efficient
EMBEDDING_DIMENSION = 384

# Reranking Config (New for Phase 3)
RERANKING_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2" # Better accuracy than TinyBERT
ENABLE_RERANKING = True

# Clustering Config
HDBSCAN_MIN_CLUSTER_SIZE = 5
HDBSCAN_MIN_SAMPLES = 3        # Optimized for cold-start (from 2)
HDBSCAN_METRIC = 'euclidean'   # Changed from 'cosine' (not supported by ball_tree) - L2 on normalized vectors is equivalent
HDBSCAN_EPSILON = 0.2
HDBSCAN_PREDICTION_DATA = True # Essential for fast classification

# Decay & Pruning Config
DECAY_RATE_DAILY = 0.05
PRUNE_THRESHOLD = 0.4
PROTECT_ACCURACY_THRESHOLD = 0.95
MAINTENANCE_HOUR = 3  # 3 AM local

# Retrieval Config
DEFAULT_TOP_K = 5
MMR_LAMBDA = 0.7  # Diversity factor (0.7 = balance relevance/diversity)

# Feature Flags
SERENDIPITY_ENABLED = False       # Default OFF for precision
SERENDIPITY_MIN_QUALITY = 0.90
USE_LLM_COMPRESSION = True        # Can be toggled for offline/fast mode
ENABLE_HYPERFOCUS = True          # Enable Semantic Routing (Phase 6)

# Quality Scoring Weights
WEIGHTS = {
    "usage": 0.3,
    "reuse": 0.2,
    "compression": 0.2,
    "accuracy": 0.2,
    "freshness": 0.1
}

# Cognitive Loop Config (Phase 4)
ENABLE_COGNITIVE_LOOP = True
COGNITIVE_LOOP_INTERVAL_SEC = 60  # Run every minute
UNCERTAINTY_THRESHOLD = 0.6       # Refine abstractions with quality below this
MAX_REFINEMENTS_PER_RUN = 5       # Don't overload the LLM
