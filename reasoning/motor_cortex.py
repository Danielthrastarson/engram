# reasoning/motor_cortex.py
# Neuroscience-correct motor cortex with 3 brain layers:
#   1. Basal Ganglia  — reinforcement-based action selection
#   2. Forward Model   — predict sensory consequences (cerebellum)
#   3. Inverse Model   — plan action sequences to reach goals (premotor cortex)
#   + Habituation      — successful sequences become automatic

import logging
import time
import math
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque

logger = logging.getLogger(__name__)

# ============================================================
# Data Types
# ============================================================

ACTIONS = [
    "MOVE_FORWARD", "MOVE_BACK", "MOVE_LEFT", "MOVE_RIGHT",
    "TURN_LEFT", "TURN_RIGHT", "JUMP", "IDLE"
]


@dataclass
class SensorData:
    """What the agent perceives"""
    position: List[float] = field(default_factory=lambda: [0, 0, 0])
    velocity: List[float] = field(default_factory=lambda: [0, 0, 0])
    rotation: float = 0.0
    is_grounded: bool = True
    vision: List[dict] = field(default_factory=list)
    touching: List[str] = field(default_factory=list)
    reward: float = 0.0
    
    @staticmethod
    def from_dict(d: dict) -> "SensorData":
        return SensorData(
            position=d.get("position", [0, 0, 0]),
            velocity=d.get("velocity", [0, 0, 0]),
            rotation=d.get("rotation", 0),
            is_grounded=d.get("is_grounded", True),
            vision=d.get("vision", []),
            touching=d.get("touching", []),
            reward=d.get("reward", 0),
        )
    
    def state_key(self) -> str:
        """Discretize position into grid cell for Q-table lookup"""
        gx = round(self.position[0])
        gy = round(self.position[1])
        gz = round(self.position[2])
        gr = round(self.rotation / 45) * 45  # 8 directions
        grounded = 1 if self.is_grounded else 0
        # Include nearby vision (simplified)
        near = "clear"
        for v in self.vision[:3]:
            if v.get("distance", 10) < 2.0:
                near = "blocked"
                break
        return f"{gx},{gy},{gz},{gr},{grounded},{near}"


@dataclass
class MotorPrediction:
    """Forward model's prediction of what will happen"""
    predicted_position: List[float]
    predicted_grounded: bool
    predicted_velocity: List[float]
    action: str


@dataclass
class MotorExperience:
    """One motor experience (for engram storage)"""
    state_before: str
    action: str
    state_after: str
    prediction_error: float
    reward: float
    timestamp: float = field(default_factory=time.time)


# ============================================================
# Layer 1: Basal Ganglia (Action Selection via Reinforcement)
# ============================================================

class BasalGanglia:
    """
    Selects actions using Q-learning.
    Good outcomes → repeat action. Bad outcomes → avoid.
    Epsilon-greedy exploration.
    """
    
    def __init__(self, learning_rate: float = 0.1, discount: float = 0.95,
                 epsilon: float = 0.3, epsilon_decay: float = 0.999):
        # Q-table: state_key → {action → value}
        self.q_table: Dict[str, Dict[str, float]] = {}
        self.lr = learning_rate
        self.discount = discount
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = 0.05
        
        # Stats
        self.total_decisions = 0
        self.explorations = 0
    
    def select_action(self, state_key: str, goal_bias: Dict[str, float] = None) -> str:
        """
        Choose action using epsilon-greedy + optional goal bias.
        """
        self.total_decisions += 1
        
        # Ensure state exists in Q-table
        if state_key not in self.q_table:
            self.q_table[state_key] = {a: 0.0 for a in ACTIONS}
        
        # Epsilon-greedy exploration
        if random.random() < self.epsilon:
            self.explorations += 1
            return random.choice(ACTIONS)
        
        # Exploit: pick action with highest Q-value
        q_values = self.q_table[state_key].copy()
        
        # Apply goal bias (e.g., "MOVE_FORWARD" toward target)
        if goal_bias:
            for action, bias in goal_bias.items():
                if action in q_values:
                    q_values[action] += bias
        
        best_action = max(q_values, key=q_values.get)
        return best_action
    
    def update(self, state: str, action: str, reward: float, next_state: str):
        """Q-learning update"""
        if state not in self.q_table:
            self.q_table[state] = {a: 0.0 for a in ACTIONS}
        if next_state not in self.q_table:
            self.q_table[next_state] = {a: 0.0 for a in ACTIONS}
        
        current_q = self.q_table[state][action]
        max_next_q = max(self.q_table[next_state].values())
        
        # Q-learning formula
        new_q = current_q + self.lr * (
            reward + self.discount * max_next_q - current_q
        )
        self.q_table[state][action] = new_q
        
        # Decay epsilon
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)


# ============================================================
# Layer 2: Forward Model (Cerebellum — Predict Consequences)
# ============================================================

class ForwardModel:
    """
    Predicts sensory consequences of an action.
    Learns from prediction error over time.
    Initially naive → improves with experience.
    """
    
    def __init__(self):
        # Simple physics model that gets refined
        self.move_speed = 1.0     # Estimated speed (updated from experience)
        self.turn_speed = 45.0    # Degrees per action
        self.jump_speed = 3.0     # Estimated jump velocity
        self.gravity = -9.8       # Known physics
        
        # Learning
        self.position_errors: deque = deque(maxlen=100)
        self.avg_error = 1.0  # Starts high (naive model)
        self.total_predictions = 0
    
    def predict(self, sensor: SensorData, action: str) -> MotorPrediction:
        """Predict the next state after executing action"""
        self.total_predictions += 1
        
        pos = list(sensor.position)
        vel = list(sensor.velocity)
        rot = sensor.rotation
        grounded = sensor.is_grounded
        
        # Predict based on action
        rad = math.radians(rot)
        
        if action == "MOVE_FORWARD":
            pos[0] += math.sin(rad) * self.move_speed
            pos[2] += math.cos(rad) * self.move_speed
        elif action == "MOVE_BACK":
            pos[0] -= math.sin(rad) * self.move_speed
            pos[2] -= math.cos(rad) * self.move_speed
        elif action == "MOVE_LEFT":
            pos[0] += math.cos(rad) * self.move_speed
            pos[2] -= math.sin(rad) * self.move_speed
        elif action == "MOVE_RIGHT":
            pos[0] -= math.cos(rad) * self.move_speed
            pos[2] += math.sin(rad) * self.move_speed
        elif action == "TURN_LEFT":
            rot -= self.turn_speed
        elif action == "TURN_RIGHT":
            rot += self.turn_speed
        elif action == "JUMP" and grounded:
            vel[1] = self.jump_speed
            grounded = False
        
        # Gravity prediction
        if not grounded:
            vel[1] += self.gravity * 0.1  # dt = 0.1s
            pos[1] += vel[1] * 0.1
        
        return MotorPrediction(
            predicted_position=pos,
            predicted_grounded=grounded,
            predicted_velocity=vel,
            action=action,
        )
    
    def compute_error(self, prediction: MotorPrediction, 
                      actual: SensorData) -> float:
        """Compute prediction error and update model"""
        # Position error (Euclidean)
        dx = prediction.predicted_position[0] - actual.position[0]
        dy = prediction.predicted_position[1] - actual.position[1]
        dz = prediction.predicted_position[2] - actual.position[2]
        pos_error = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        # Grounded prediction error
        ground_error = 1.0 if prediction.predicted_grounded != actual.is_grounded else 0.0
        
        # Combined
        error = pos_error * 0.8 + ground_error * 0.2
        
        # Track
        self.position_errors.append(pos_error)
        self.avg_error = self.avg_error * 0.95 + error * 0.05
        
        # Learn from error — adjust move speed estimate
        if prediction.action in ("MOVE_FORWARD", "MOVE_BACK", "MOVE_LEFT", "MOVE_RIGHT"):
            actual_dist = math.sqrt(
                (actual.position[0] - actual.velocity[0])**2 + 
                (actual.position[2] - actual.velocity[2])**2
            )
            if actual_dist > 0.01:
                self.move_speed = self.move_speed * 0.9 + actual_dist * 0.1 * 10
        
        return error


# ============================================================
# Layer 3: Inverse Model (Premotor Cortex — Plan to Reach Goal)
# ============================================================

class InverseModel:
    """
    Given current state and goal, plan sequence of actions.
    Uses forward model to simulate outcomes.
    Replans on high prediction error.
    """
    
    def __init__(self, forward_model: ForwardModel):
        self.forward = forward_model
        self.current_plan: List[str] = []
        self.plan_index: int = 0
    
    def plan(self, sensor: SensorData, goal_pos: List[float]) -> List[str]:
        """Generate action sequence toward goal"""
        actions = []
        
        # Simple reactive planning:
        dx = goal_pos[0] - sensor.position[0]
        dz = goal_pos[2] - sensor.position[2]
        dist = math.sqrt(dx*dx + dz*dz)
        
        if dist < 1.0:
            return ["IDLE"]  # Close enough
        
        # Calculate desired angle
        desired_angle = math.degrees(math.atan2(dx, dz)) % 360
        current_angle = sensor.rotation % 360
        
        # Turn toward goal
        angle_diff = (desired_angle - current_angle + 180) % 360 - 180
        
        if abs(angle_diff) > 30:
            if angle_diff > 0:
                actions.extend(["TURN_RIGHT"] * max(1, int(abs(angle_diff) / 45)))
            else:
                actions.extend(["TURN_LEFT"] * max(1, int(abs(angle_diff) / 45)))
        
        # Move toward goal
        steps = max(1, int(dist / max(self.forward.move_speed, 0.5)))
        actions.extend(["MOVE_FORWARD"] * min(steps, 10))
        
        # Check if obstacle ahead
        for v in sensor.vision[:3]:
            if v.get("distance", 10) < 2.0 and v.get("type") == "block":
                # Obstacle — try jumping over
                actions.insert(0, "JUMP")
                break
        
        self.current_plan = actions
        self.plan_index = 0
        return actions
    
    def next_action(self) -> Optional[str]:
        """Get next action from current plan"""
        if self.plan_index < len(self.current_plan):
            action = self.current_plan[self.plan_index]
            self.plan_index += 1
            return action
        return None
    
    def needs_replan(self, error: float) -> bool:
        """Should we replan? (high prediction error = plan isn't working)"""
        return error > 0.5 or self.plan_index >= len(self.current_plan)


# ============================================================
# Habituation: Successful Sequences Become Automatic
# ============================================================

class Habituation:
    """
    Frequently successful action sequences become cached.
    Skips full planning → direct state → action mapping.
    """
    
    def __init__(self, threshold: int = 5):
        # state_pattern → (action, success_count)
        self.habits: Dict[str, Tuple[str, int]] = {}
        self.threshold = threshold
    
    def record(self, state_key: str, action: str, was_good: bool):
        """Record action outcome for habituation"""
        if was_good:
            if state_key in self.habits:
                stored_action, count = self.habits[state_key]
                if stored_action == action:
                    self.habits[state_key] = (action, count + 1)
                else:
                    # Different action won — update
                    self.habits[state_key] = (action, 1)
            else:
                self.habits[state_key] = (action, 1)
    
    def get_habitual_action(self, state_key: str) -> Optional[str]:
        """Get cached action if habit is strong enough"""
        if state_key in self.habits:
            action, count = self.habits[state_key]
            if count >= self.threshold:
                return action
        return None


# ============================================================
# Motor Cortex: Orchestrates All Layers
# ============================================================

class MotorCortex:
    """
    Full motor cortex orchestrating:
    - Basal Ganglia (action selection)
    - Forward Model (prediction)
    - Inverse Model (planning)
    - Habituation (automation)
    
    10 Hz tick rate (matches retrieval rhythm).
    """
    
    def __init__(self):
        self.forward_model = ForwardModel()
        self.inverse_model = InverseModel(self.forward_model)
        self.basal_ganglia = BasalGanglia()
        self.habituation = Habituation()
        
        # State
        self.last_sensor: Optional[SensorData] = None
        self.last_action: Optional[str] = None
        self.last_prediction: Optional[MotorPrediction] = None
        self.current_goal: Optional[List[float]] = None
        self.visited_positions: set = set()
        
        # Experience buffer (for engram creation)
        self.experiences: deque = deque(maxlen=500)
        
        # Stats
        self.tick_count = 0
        self.total_reward = 0.0
        self.avg_prediction_error = 0.5
        self.stuck_counter = 0
        self.last_position_hash = ""
    
    def set_goal(self, position: List[float]):
        """Set navigation goal"""
        self.current_goal = position
        self.inverse_model.current_plan = []
        logger.info(f"🎯 Motor goal set: {position}")
    
    def tick(self, sensor_data: dict) -> dict:
        """
        One motor cortex tick.
        
        Input: raw sensor data from 3D world
        Output: motor command for 3D world
        
        The full loop:
        1. Parse sensor data
        2. Compute prediction error from last action
        3. Update models (forward model, Q-table)
        4. Decide next action (habit → plan → explore)
        5. Predict outcome
        6. Return command
        """
        self.tick_count += 1
        sensor = SensorData.from_dict(sensor_data)
        state_key = sensor.state_key()
        
        # Track visited positions
        pos_hash = f"{round(sensor.position[0])},{round(sensor.position[2])}"
        is_new_position = pos_hash not in self.visited_positions
        self.visited_positions.add(pos_hash)
        
        # === Step 1: Compute prediction error from last action ===
        prediction_error = 0.0
        if self.last_prediction and self.last_sensor:
            prediction_error = self.forward_model.compute_error(
                self.last_prediction, sensor
            )
            self.avg_prediction_error = (
                self.avg_prediction_error * 0.95 + prediction_error * 0.05
            )
        
        # === Step 2: Compute reward ===
        reward = sensor.reward  # External reward from world
        
        # Intrinsic rewards
        if is_new_position:
            reward += 0.1  # Curiosity reward
        
        # Stuck detection
        if pos_hash == self.last_position_hash:
            self.stuck_counter += 1
            if self.stuck_counter > 10:
                reward -= 0.1  # Penalize being stuck
        else:
            self.stuck_counter = 0
        self.last_position_hash = pos_hash
        
        # Goal reward
        if self.current_goal:
            dx = self.current_goal[0] - sensor.position[0]
            dz = self.current_goal[2] - sensor.position[2]
            goal_dist = math.sqrt(dx*dx + dz*dz)
            if goal_dist < 1.5:
                reward += 1.0  # Reached goal!
                self.current_goal = None
        
        self.total_reward += reward
        
        # === Step 3: Update Q-table from last action ===
        if self.last_sensor and self.last_action:
            old_state = self.last_sensor.state_key()
            self.basal_ganglia.update(old_state, self.last_action, reward, state_key)
            
            # Record habituation
            self.habituation.record(
                old_state, self.last_action, 
                was_good=(reward > 0 and prediction_error < 0.3)
            )
            
            # Store experience
            exp = MotorExperience(
                state_before=old_state,
                action=self.last_action,
                state_after=state_key,
                prediction_error=prediction_error,
                reward=reward,
            )
            self.experiences.append(exp)
        
        # === Step 4: Decide next action ===
        action = None
        decision_source = "explore"
        
        # Try habit first (fastest — skips planning)
        habit = self.habituation.get_habitual_action(state_key)
        if habit:
            action = habit
            decision_source = "habit"
        
        # Try inverse model plan if we have a goal
        if not action and self.current_goal:
            if self.inverse_model.needs_replan(prediction_error):
                self.inverse_model.plan(sensor, self.current_goal)
            
            planned = self.inverse_model.next_action()
            if planned:
                action = planned
                decision_source = "plan"
        
        # Basal ganglia (reinforcement) as fallback
        if not action:
            # Goal bias: prefer actions toward goal
            goal_bias = None
            if self.current_goal:
                goal_bias = self._compute_goal_bias(sensor, self.current_goal)
            
            action = self.basal_ganglia.select_action(state_key, goal_bias)
            decision_source = "basal_ganglia"
        
        # === Step 5: Predict outcome ===
        prediction = self.forward_model.predict(sensor, action)
        
        # === Step 6: Save state for next tick ===
        self.last_sensor = sensor
        self.last_action = action
        self.last_prediction = prediction
        
        return {
            "action": action,
            "source": decision_source,
            "prediction_error": prediction_error,
            "reward": reward,
            "tick": self.tick_count,
        }
    
    def get_status(self) -> dict:
        return {
            "tick_count": self.tick_count,
            "total_reward": round(self.total_reward, 2),
            "avg_prediction_error": round(self.avg_prediction_error, 4),
            "positions_visited": len(self.visited_positions),
            "q_table_size": len(self.basal_ganglia.q_table),
            "habits_formed": sum(
                1 for _, (_, c) in self.habituation.habits.items() 
                if c >= self.habituation.threshold
            ),
            "epsilon": round(self.basal_ganglia.epsilon, 4),
            "forward_model_error": round(self.forward_model.avg_error, 4),
            "stuck_counter": self.stuck_counter,
            "has_goal": self.current_goal is not None,
            "experiences_stored": len(self.experiences),
        }
    
    def get_high_error_experiences(self, min_error: float = 0.5) -> List[dict]:
        """Get experiences worth turning into motor engrams"""
        return [
            {
                "state": exp.state_before,
                "action": exp.action,
                "error": exp.prediction_error,
                "reward": exp.reward,
            }
            for exp in self.experiences
            if exp.prediction_error >= min_error
        ]
    
    def _compute_goal_bias(self, sensor: SensorData, 
                           goal: List[float]) -> Dict[str, float]:
        """Compute action bias toward goal"""
        dx = goal[0] - sensor.position[0]
        dz = goal[2] - sensor.position[2]
        desired_angle = math.degrees(math.atan2(dx, dz)) % 360
        current_angle = sensor.rotation % 360
        angle_diff = (desired_angle - current_angle + 180) % 360 - 180
        
        bias = {}
        if abs(angle_diff) < 30:
            bias["MOVE_FORWARD"] = 0.5
        elif angle_diff > 0:
            bias["TURN_RIGHT"] = 0.3
        else:
            bias["TURN_LEFT"] = 0.3
        
        return bias
