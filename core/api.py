
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import json
import asyncio
from typing import List
import logging
from pathlib import Path

# Engram Core
from core.abstraction_manager import AbstractionManager
from core.router import ClusterCentroidManager
from utils import config

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VisualCortex")

app = FastAPI(title="Engram Visual Cortex")

# Allow CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Core Systems
manager = AbstractionManager()
centroid_mgr = ClusterCentroidManager()

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

ws_manager = ConnectionManager()

@app.get("/api/clusters")
def get_clusters():
    """Get all cluster centroids (Galaxies)"""
    centroids = centroid_mgr.get_all_centroids()
    # Format for UI: {id, vector, size}
    # For now, size is just 1.0, later we can count members
    data = []
    for c_id, vec in centroids.items():
        data.append({
            "id": c_id,
            "x": float(vec[0]) * 10, # Project to 3D roughly
            "y": float(vec[1]) * 10,
            "z": float(vec[2]) * 10,
            "color": f"hsl({hash(c_id) % 360}, 70%, 50%)"
        })
    return data

@app.get("/api/abstractions")
def get_abstractions():
    """Get recent abstractions (Stars)"""
    # This is expensive, so limit to 500 for demo
    # In V2 we need a proper DB query for basic metadata only
    # Getting from chroma is hard to iterate, so let's use SQLite
    cursor = manager.storage.conn.execute("SELECT id, cluster_id, content, quality_score FROM abstractions ORDER BY last_used DESC LIMIT 500")
    rows = cursor.fetchall()
    
    nodes = []
    for row in rows:
        r = dict(row)
        nodes.append({
            "id": r["id"],
            "group": r["cluster_id"] or "noise",
            "label": r["content"][:30] + "...",
            "val": r["quality_score"], # Size
        })
    return nodes

# CONTROL CENTER API ENDPOINTS (Phase 13)

@app.get("/api/evolution/status")
def get_evolution_status():
    """Get current evolution level and metrics"""
    from core.evolution import EvolutionManager
    evo = EvolutionManager()
    metrics = evo.get_metrics()
    return {
        "level": metrics["current_level"],
        "metrics": metrics,
        "pending_upgrade": evo.get_state("pending_upgrade")
    }

@app.post("/api/evolution/upgrade/{level}")
def apply_evolution_upgrade(level: int):
    """Manually apply an evolution upgrade"""
    from core.evolution import EvolutionManager
    evo = EvolutionManager()
    result = evo.apply_upgrade(level)
    return {"message": result}

@app.post("/api/dream/trigger")
def trigger_dream():
    """Manually trigger a dream cycle"""
    from core.subconscious import Subconscious
    sub = Subconscious()
    sub.dream()
    return {"message": "Dream cycle triggered"}

@app.get("/api/dream/history")
def get_dream_history():
    """Get recent dream connections"""
    cursor = manager.storage.conn.execute("""
        SELECT source_id, target_id, weight FROM links 
        WHERE type = 'dream_association' OR type = 'dreamt_association'
        ORDER BY rowid DESC LIMIT 10
    """)
    dreams = []
    for row in cursor.fetchall():
        source = manager.storage.get_abstraction(row[0])
        target = manager.storage.get_abstraction(row[1])
        dreams.append({
            "source": {"id": row[0], "content": source.content[:50] if source else "N/A"},
            "target": {"id": row[1], "content": target.content[:50] if target else "N/A"},
            "weight": row[2]
        })
    return dreams

@app.put("/api/abstraction/{abs_id}/salience")
def update_salience(abs_id: str, salience: float):
    """Update salience value for an abstraction"""
    abs_obj = manager.storage.get_abstraction(abs_id)
    if not abs_obj:
        return {"error": "Abstraction not found"}
    abs_obj.salience = max(0.5, min(salience, 2.0))  # Clamp
    manager.storage.update_metrics(abs_obj)
    return {"message": f"Salience updated to {abs_obj.salience}"}

@app.get("/api/graph/{abs_id}")
def get_subgraph(abs_id: str, depth: int = 1):
    """Get graph structure around an abstraction"""
    from core.graph_manager import GraphManager
    gm = GraphManager()
    nodes = gm.explore_subgraph(abs_id, depth=depth)
    
    # Format as nodes + edges
    node_list = [{"id": n.id, "content": n.content[:30], "quality": n.quality_score} for n in nodes]
    
    # Get edges
    edges = []
    for node in nodes:
        for link in node.links:
            edges.append({"source": node.id, "target": link.target_id, "type": link.type})
    
    return {"nodes": node_list, "edges": edges}

@app.get("/api/memory/search")
def search_memories(q: str = "", cluster: str = None, min_quality: float = 0.0):
    """Search and filter memories"""
    query = "SELECT id, content, quality_score, cluster_id, salience, last_used FROM abstractions WHERE 1=1"
    params = []
    
    if q:
        query += " AND content LIKE ?"
        params.append(f"%{q}%")
    if cluster:
        query += " AND cluster_id = ?"
        params.append(cluster)
    if min_quality > 0:
        query += " AND quality_score >= ?"
        params.append(min_quality)
    
    query += " ORDER BY quality_score DESC LIMIT 100"
    
    cursor = manager.storage.conn.execute(query, params)
    results = []
    for row in cursor.fetchall():
        r = dict(row)
        results.append(r)
    return results


@app.get("/api/graph/all_links")
def get_all_links():
    """Get all graph links for 3D visualization"""
    cursor = manager.storage.conn.execute("""
        SELECT source_id, target_id, type, weight FROM links 
        LIMIT 1000
    """)
    links = []
    for row in cursor.fetchall():
        links.append({
            "source": row[0],
            "target": row[1],
            "type": row[2],
            "value": row[3]
        })
    return links


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep alive
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except:
        ws_manager.disconnect(websocket)

# Serve Static UI
# Create ui directory if not exists
ui_path = Path("c:/Users/Notandi/Desktop/agi/engram-system/ui")
ui_path.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=str(ui_path), html=True), name="ui")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
