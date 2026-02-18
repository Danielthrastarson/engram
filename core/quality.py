import math
from core.abstraction import Abstraction
from utils import config

def calculate_quality_score(abstraction: Abstraction) -> float:
    """
    Calculate quality score based on 6 dimensions:
    1. Usage Count (Normalized)
    2. Reuse Contexts (Normalized)
    3. Compression Ratio (Normalized)
    4. Accuracy Preserved (0-1)
    5. Freshness (Inverse Decay)
    6. Salience (Emotional Weight) - EVOLUTION LEVEL 3
    """
    
    # 1. Normalize Usage
    # Log scale is better for usage count (1 vs 100 matters, 1000 vs 1100 doesn't)
    norm_usage = math.log1p(abstraction.successful_application_count) / 5.0 # Cap at ~5 (=150 uses)
    norm_usage = min(norm_usage, 1.0)
    
    # 2. Normalize Reuse Contexts
    # Reused in >5 contexts is excellent
    norm_reuse = min(abstraction.reuse_contexts / 5.0, 1.0)
    
    # 3. Normalize Compression Ratio
    # >5x compression is excellent
    norm_compression = min(abstraction.compression_ratio / 5.0, 1.0)
    
    # 4. Accuracy
    accuracy = abstraction.accuracy_preserved
    
    # 5. Freshness
    freshness = 1.0 - abstraction.decay_score
    
    # 6. Salience (Emotional Weight) - EVOLUTION SYSTEM
    # Range: 0.5 (boring) to 2.0 (vital). Normalize to 0-1 by: (salience - 0.5) / 1.5
    salience_norm = (abstraction.salience - 0.5) / 1.5
    salience_norm = max(0.0, min(salience_norm, 1.0)) # Clamp
    
    weights = config.WEIGHTS
    
    # EVOLUTION LEVEL 3: Salience gets 0.15 weight
    # Other weights adjusted proportionally to sum to 1.0
    salience_weight = 0.15
    
    score = (
        weights["usage"] * (1 - salience_weight) * norm_usage +
        weights["reuse"] * (1 - salience_weight) * norm_reuse +
        weights["compression"] * (1 - salience_weight) * norm_compression +
        weights["accuracy"] * (1 - salience_weight) * accuracy +
        weights["freshness"] * (1 - salience_weight) * freshness +
        salience_weight * salience_norm
    )
    
    return round(score, 4)

def update_metrics(abstraction: Abstraction):
    """Update all derived metrics for an abstraction"""
    abstraction.quality_score = calculate_quality_score(abstraction)
