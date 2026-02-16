import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MetricsTracker:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
        
    def _init(self):
        self.metrics_file = Path("c:/Users/Notandi/Desktop/agi/engram-system/data/metrics.json")
        self.data = self._load()
        
    def _load(self) -> Dict[str, Any]:
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {
            "refinements_total": 0,
            "queries_total": 0,
            "errors_total": 0,
            "last_cycle_timestamp": None,
            "refinement_history": [] # List of {timestamp, id, old_len, new_len}
        }
        
    def _save(self):
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

    def track_refinement(self, abs_id: str, old_len: int, new_len: int):
        self.data["refinements_total"] += 1
        self.data["last_cycle_timestamp"] = datetime.now().isoformat()
        
        # Keep history short (last 100)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "id": abs_id,
            "delta": new_len - old_len
        }
        self.data["refinement_history"].insert(0, entry)
        self.data["refinement_history"] = self.data["refinement_history"][:100]
        
        self._save()
        
    def get_stats(self) -> str:
        return f"Refinements: {self.data['refinements_total']} | Queries: {self.data['queries_total']}"
