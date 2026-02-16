import logging
import time
import threading
from datetime import datetime
from pathlib import Path
from core.storage import EngramStorage

logger = logging.getLogger(__name__)

class SystemMonitor:
    """
    Real-time system health monitoring (Phase 12).
    Tracks QPS, latency, errors, storage size.
    """
    def __init__(self):
        self.storage = EngramStorage()
        self.metrics = {
            "queries_total": 0,
            "queries_last_minute": 0,
            "avg_latency_ms": 0,
            "error_count": 0,
            "storage_mb": 0
        }
        self._lock = threading.Lock()
        self._start_monitoring()
        
    def _start_monitoring(self):
        """Background thread to update metrics"""
        def _monitor_loop():
            while True:
                self._update_storage_size()
                time.sleep(60)  # Every minute
                
        thread = threading.Thread(target=_monitor_loop, daemon=True)
        thread.start()
        
    def _update_storage_size(self):
        """Calculate total storage usage"""
        from utils import config
        
        # ChromaDB size (rough estimate)
        chroma_path = Path(config.CHROMA_PERSIST_DIRECTORY)
        chroma_size = sum(f.stat().st_size for f in chroma_path.rglob('*') if f.is_file())
        
        # SQLite size
        sqlite_path = Path(config.METADATA_DB_PATH)
        sqlite_size = sqlite_path.stat().st_size if sqlite_path.exists() else 0
        
        total_mb = (chroma_size + sqlite_size) / (1024 * 1024)
        
        with self._lock:
            self.metrics["storage_mb"] = round(total_mb, 2)
            
    def record_query(self, latency_ms: float, error: bool = False):
        """Record a query execution"""
        with self._lock:
            self.metrics["queries_total"] += 1
            self.metrics["queries_last_minute"] += 1
            
            # Running average
            prev_avg = self.metrics["avg_latency_ms"]
            self.metrics["avg_latency_ms"] = (prev_avg * 0.9) + (latency_ms * 0.1)
            
            if error:
                self.metrics["error_count"] += 1
                
    def get_metrics(self) -> dict:
        """Get current metrics snapshot"""
        with self._lock:
            return self.metrics.copy()
            
    def get_health(self) -> dict:
        """Health check for deployment"""
        metrics = self.get_metrics()
        
        # Define thresholds
        is_healthy = (
            metrics["avg_latency_ms"] < 1000 and  # < 1s avg
            (metrics["error_count"] / max(metrics["queries_total"], 1)) < 0.05  # < 5% errors
        )
        
        return {
            "status": "healthy" if is_healthy else "degraded",
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics
        }
