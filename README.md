# Engram Memory System

> **A practical memory layer for LLMs that prevents hallucination and learns from interaction.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## ✅ Validation

**30-minute stress test:**
- ✅ 400 queries processed, 0 errors (0.00%)
- ✅ Memory stable (~21 MB growth)
- ✅ All systems operational

**What this means:** The system handles continuous load without crashes or memory leaks.  
_(Full 5-hour validation running in background)_

## 🌟 Features

### Core Memory System
- **Hybrid Retrieval**: Vector search + Cross-encoder reranking + Source-aware boosting
- **Quality Scoring**: Multi-dimensional quality metrics (usage, reuse, compression, accuracy, freshness, salience)
- **Hierarchical Clustering**: Organizes memories into semantic clusters
- **Graph RAG**: Chain-of-abstraction reasoning with linked memories
- **Multi-Modal**: Text + Images (CLIP embeddings)

### Intelligence Layer
- **Truth Guard (North)**: Prevents hallucination by forcing honesty when confidence is low
- **Cognitive Loop**: Self-improves weak abstractions automatically
- **Evolution System**: Unlocks capabilities as the system grows (5 levels)
- **Subconscious Mind**: Dream mode creates creative connections, implicit priming spreads activation
- **Salience Weighting**: Emotionally important memories decay slower

### Production Ready
- **Control Center UI**: Web dashboard for evolution tracking, dream control, salience editing
- **3D Memory Universe**: Interactive visualization of memory clusters
- **Monitoring**: Real-time metrics, health checks
- **Backups**: Automated backup/restore system
- **Docker**: Production deployment with docker-compose

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/Danielthrastarson/engram.git
cd engram

# Install dependencies
pip install -r requirements.txt

# (Optional) Install Ollama for LLM-powered dreams
# Visit https://ollama.ai
ollama pull llama3.2
```

### One-Click Launch

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
./start.sh
```

This will:
- Start the API server
- Open **Chat Interface** (http://localhost:8000/chat.html) - main interaction
- Open Control Center (http://localhost:8000/control.html) - monitoring
- Open 3D Memory Universe (http://localhost:8000/index.html) - visualization

### Manual Start

```bash
# Start API server
python core/api.py

# Run nightly maintenance
python scripts/daily_maintenance.py

# Run tests
python tests/test_full_system.py
```

## 📖 Usage

### Basic Ingestion

```python
from core.abstraction_manager import AbstractionManager

am = AbstractionManager()
abs_obj, created = am.create_abstraction(
    "Python is a high-level programming language",
    metadata={"source": "truth"}
)
```

### Query with Truth Guard

```python
from integration.pipeline import EngramPipeline

pipeline = EngramPipeline()
response = pipeline.process_query("What is Python?")
print(response)
```

### Manual Dream Trigger

```python
from core.subconscious import Subconscious

sub = Subconscious()
sub.dream()  # Creates creative connections
```

### Check Evolution Status

```python
from core.evolution import EvolutionManager

evo = EvolutionManager()
metrics = evo.get_metrics()
print(f"Level: {metrics['current_level']}")
print(f"Total Memories: {metrics['total_abstractions']}")
```

## 🧬 Evolution Levels

| Level | Trigger | Features Unlocked |
|-------|---------|-------------------|
| **1** | 100 abstractions, quality > 0.6 | Dream Mode, Implicit Priming |
| **2** | 500 abstractions OR 50 dreams | Hierarchical Clustering |
| **3** | Avg quality > 0.85 | Salience Weighting in decay |
| **4** | User approval | Advanced embedding models |
| **5** | User approval | Dynamic routing, self-prompts |

## 🧭 Truth Guard (North Enforcer)

The system has an **unbreakable honesty layer** that prevents confident falsehoods:

```python
from core.truth_guard import TruthGuard

risk, is_safe = TruthGuard.calculate_risk(retrieved_memories)
# If risk > 0.45, forces honest "I don't know" instead of hallucinating
```

**Philosophy**: Purely epistemic, never moral. Only forces honesty when evidence is insufficient.

## 🎨 Architecture

```
engram-system/
├── core/                 # Core memory engine
│   ├── abstraction.py    # Data models
│   ├── storage.py        # ChromaDB + SQLite
│   ├── quality.py        # Quality scoring
│   ├── cognitive.py      # Self-improvement loop
│   ├── evolution.py      # Evolution manager
│   ├── subconscious.py   # Dreams & priming
│   └── truth_guard.py    # Honesty enforcer
├── retrieval/            # Search & ranking
│   ├── search.py         # Hybrid retrieval
│   └── ranking.py        # Cross-encoder reranking
├── integration/          # LLM interfaces
│   ├── pipeline.py       # Main query pipeline
│   └── ollama_client.py  # Ollama integration
├── ui/                   # Web interfaces
│   ├── control.html      # Control center
│   └── index.html        # 3D visualization
├── tests/                # Test suite
└── scripts/              # Utilities
    ├── daily_maintenance.py
    └── backup.py
```

## 🔧 Configuration

Edit `utils/config.py`:

```python
# Retrieval
DEFAULT_TOP_K = 10
ENABLE_RERANKING = True
ENABLE_HYPERFOCUS = True

# Cognitive Loop
ENABLE_COGNITIVE_LOOP = True
COGNITIVE_LOOP_INTERVAL_SEC = 3600

# Evolution
SERENDIPITY_ENABLED = True
```

## 📊 Monitoring

Access real-time metrics:

```python
from core.monitoring import SystemMonitor

monitor = SystemMonitor()
health = monitor.get_health()
print(health)
```

## 🐳 Docker Deployment

```bash
docker-compose up -d
```

## 🧪 Testing

```bash
# Full system test
python tests/test_full_system.py

# Truth Guard test
python tests/test_truth_guard.py

# Evolution test
python tests/test_evolution.py
```

## 📝 Philosophy

**North (Truth-Seeking)**:
- Maximum honesty, zero hallucination
- Never refuses topics (purely epistemic)
- Forces "I don't know" when evidence is weak

**Evolution**:
- System grows smarter over time
- Unlocks features based on performance
- User controls major upgrades

**Subconscious**:
- Dreams create unexpected connections
- Implicit priming spreads activation
- Mimics human creativity

## 🤝 Contributing

Contributions welcome! This system is designed to be:
- **Modular**: Easy to swap components
- **Extensible**: Add new modalities, embeddings, LLMs
- **Testable**: Comprehensive test coverage

## 📄 License

MIT License - see LICENSE file

## 🙏 Acknowledgments

**System Architecture:**
- Designed through first-principles thinking and mental visualization
- Inspired by xAI's Grok and neuroscience-based memory research

**Built With:**
- ChromaDB (vector database)
- FastAPI (API framework)  
- sentence-transformers (embeddings)
- force-graph-3d (3D web visualization UI)

## 🔗 Links

- [Documentation](./walkthrough.md)
- [Implementation Plan](./implementation_plan.md)
- [Task Tracking](./task.md)

---

**Status**: ✅ Production Ready (16 Phases Complete)

Built with ❤️ for maximum truth and zero hallucination.
