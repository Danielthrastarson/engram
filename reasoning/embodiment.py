# reasoning/embodiment.py
# WebSocket bridge between the 3D world (browser) and the Motor Cortex (Python)
# Runs alongside the existing API on a separate WebSocket endpoint

import asyncio
import json
import logging
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import websockets
    import websockets.server
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False
    logger.warning("websockets not installed. Run: pip install websockets")


class EmbodimentBridge:
    """
    WebSocket bridge for the 3D embodied world.
    
    Protocol:
    - Browser sends:  {"type": "sensor", "data": {...}}
    - Python returns:  {"type": "command", "action": "MOVE_FORWARD", ...}
    - Browser sends:  {"type": "world_info", "goals": [...], ...}
    - Python can send: {"type": "set_goal", "position": [x, y, z]}
    """
    
    def __init__(self, motor_cortex, pipeline=None, host="localhost", port=8765):
        self.motor_cortex = motor_cortex
        self.pipeline = pipeline  # For creating motor engrams
        self.host = host
        self.port = port
        self.running = False
        self._thread = None
        self._connected_clients = set()
        
        # Stats
        self.ticks_processed = 0
        self.last_command = None
    
    def start(self):
        """Start the WebSocket server in a background thread"""
        if not HAS_WEBSOCKETS:
            logger.error("Cannot start embodiment bridge: websockets not installed")
            return
        
        self.running = True
        self._thread = threading.Thread(
            target=self._run_server,
            daemon=True,
            name="EmbodimentBridge"
        )
        self._thread.start()
        logger.info(f"🌍 Embodiment bridge started on ws://{self.host}:{self.port}")
    
    def stop(self):
        """Stop the WebSocket server"""
        self.running = False
    
    def _run_server(self):
        """Run the async WebSocket server"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def serve():
            async with websockets.server.serve(
                self._handle_client, self.host, self.port
            ):
                while self.running:
                    await asyncio.sleep(0.1)
        
        try:
            loop.run_until_complete(serve())
        except Exception as e:
            logger.error(f"Embodiment bridge error: {e}")
        finally:
            loop.close()
    
    async def _handle_client(self, websocket):
        """Handle a connected 3D world client"""
        self._connected_clients.add(websocket)
        logger.info(f"🌍 3D World connected ({len(self._connected_clients)} clients)")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    response = self._process_message(data)
                    if response:
                        await websocket.send(json.dumps(response))
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON from world")
                except Exception as e:
                    logger.error(f"Embodiment error: {e}")
        finally:
            self._connected_clients.discard(websocket)
            logger.info(f"🌍 3D World disconnected ({len(self._connected_clients)} clients)")
    
    def _process_message(self, data: dict) -> Optional[dict]:
        """Process a message from the 3D world"""
        msg_type = data.get("type", "")
        
        if msg_type == "sensor":
            # Process sensor data through motor cortex
            sensor_data = data.get("data", {})
            command = self.motor_cortex.tick(sensor_data)
            self.ticks_processed += 1
            self.last_command = command
            
            # High prediction error → create motor engram
            if (self.pipeline and self.pipeline._reasoning_ready 
                and command.get("prediction_error", 0) > 0.5):
                self._create_motor_engram(sensor_data, command)
            
            return {
                "type": "command",
                "action": command["action"],
                "source": command["source"],
                "tick": command["tick"],
            }
        
        elif msg_type == "world_info":
            # World is telling us about available goals
            goals = data.get("goals", [])
            if goals and not self.motor_cortex.current_goal:
                # Pick nearest goal
                if self.motor_cortex.last_sensor:
                    pos = self.motor_cortex.last_sensor.position
                    nearest = min(goals, key=lambda g: (
                        (g[0]-pos[0])**2 + (g[2]-pos[2])**2
                    ))
                    self.motor_cortex.set_goal(nearest)
            return None
        
        elif msg_type == "goal_reached":
            # Agent reached a goal
            logger.info("🎯 Goal reached!")
            return {"type": "status", "message": "goal_reached"}
        
        elif msg_type == "fell":
            # Agent fell off the world
            logger.info("💀 Agent fell!")
            return {"type": "status", "message": "fell"}
        
        elif msg_type == "status_request":
            return {
                "type": "motor_status",
                **self.motor_cortex.get_status(),
            }
        
        return None
    
    def _create_motor_engram(self, sensor_data: dict, command: dict):
        """Store high-error motor experiences as engrams"""
        try:
            content = (
                f"Motor experience: action={command['action']} at "
                f"position={sensor_data.get('position', [0,0,0])}, "
                f"prediction_error={command['prediction_error']:.2f}, "
                f"reward={command['reward']:.2f}"
            )
            self.pipeline.ingest(content, source="motor_experience")
        except Exception as e:
            logger.debug(f"Motor engram creation failed: {e}")
    
    def get_status(self) -> dict:
        return {
            "running": self.running,
            "connected_clients": len(self._connected_clients),
            "ticks_processed": self.ticks_processed,
            "last_command": self.last_command,
        }
