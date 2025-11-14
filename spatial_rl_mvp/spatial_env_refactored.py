"""
Refactored Spatial RL Environment - MVP Version

Key improvements:
- Removed global state
- Added proper dependency injection
- Better error handling with custom exceptions
- Structured logging instead of print statements
- Cleaner separation of concerns
- Configuration management
"""

import pybullet as p
import pybullet_data
import numpy as np
import asyncio
import websockets
import json
import math
import uuid
import argparse
import sys
import wandb
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any, Optional, Set

# Internal imports
from .llm_services import get_anthropic_completion
from .config import SCORING, LLM, TASK, PHYSICS, VISUALIZATION
from .exceptions import (
    TaskNotInitializedError,
    InvalidActionError,
    SimulationError,
    LLMError
)
from .logger import setup_logger
from .scoring import SpatialScorer

logger = setup_logger(__name__)


@dataclass
class ObjectState:
    """Represents the state of a physics object."""
    id: str
    type: str  # 'cube', 'sphere'
    position: List[float]
    orientation_quaternion: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0, 1.0])
    scale: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0])
    color_rgba: List[float] = field(default_factory=lambda: [0.5, 0.5, 0.5, 1.0])


@dataclass
class SpatialTask:
    """Defines a spatial reasoning task."""
    task_id: str
    description: str
    initial_objects: List[ObjectState]
    goal_description: str
    target_object_id: str
    reference_object_id: str
    target_distance: float = 1.0


class MVPPhysicsSimulator:
    """Handles PyBullet physics simulation."""

    def __init__(self):
        self.client_id = -1
        self.objects_pb_ids: Dict[str, int] = {}
        self.object_configs: Dict[str, ObjectState] = {}
        self.logger = setup_logger(f"{__name__}.MVPPhysicsSimulator")

    def initialize(self, objects: List[ObjectState]):
        """Initialize physics world with objects."""
        if self.client_id != -1:
            p.disconnect(physicsClientId=self.client_id)

        try:
            self.client_id = p.connect(p.DIRECT)
            p.setAdditionalSearchPath(pybullet_data.getDataPath())
            p.setGravity(0, 0, PHYSICS.GRAVITY, physicsClientId=self.client_id)
            p.loadURDF("plane.urdf", physicsClientId=self.client_id)

            self.objects_pb_ids = {}
            self.object_configs = {}

            for obj_state in objects:
                self._add_object(obj_state)

            self.logger.info(f"Physics initialized with {len(self.objects_pb_ids)} objects")
        except Exception as e:
            raise SimulationError(f"Failed to initialize physics: {e}") from e

    def _add_object(self, obj_state: ObjectState):
        """Add a single object to the simulation."""
        try:
            half_extents = [s / 2.0 for s in obj_state.scale]

            # Create collision shape
            if obj_state.type == "cube":
                shape_id = p.createCollisionShape(
                    p.GEOM_BOX,
                    halfExtents=half_extents,
                    physicsClientId=self.client_id
                )
            elif obj_state.type == "sphere":
                shape_id = p.createCollisionShape(
                    p.GEOM_SPHERE,
                    radius=half_extents[0],
                    physicsClientId=self.client_id
                )
            else:
                self.logger.warning(
                    f"Unsupported object type '{obj_state.type}' for object '{obj_state.id}'"
                )
                return

            # Create visual shape
            if obj_state.type == "cube":
                visual_shape_id = p.createVisualShape(
                    shapeType=p.GEOM_BOX,
                    halfExtents=half_extents,
                    rgbaColor=obj_state.color_rgba,
                    physicsClientId=self.client_id
                )
            elif obj_state.type == "sphere":
                visual_shape_id = p.createVisualShape(
                    shapeType=p.GEOM_SPHERE,
                    radius=half_extents[0],
                    rgbaColor=obj_state.color_rgba,
                    physicsClientId=self.client_id
                )

            # Create multi-body
            body_id = p.createMultiBody(
                baseMass=PHYSICS.DEFAULT_MASS,
                baseCollisionShapeIndex=shape_id,
                baseVisualShapeIndex=visual_shape_id,
                basePosition=obj_state.position,
                baseOrientation=obj_state.orientation_quaternion,
                physicsClientId=self.client_id
            )

            self.objects_pb_ids[obj_state.id] = body_id
            self.object_configs[obj_state.id] = obj_state
            self.logger.debug(f"Added object '{obj_state.id}' with body_id={body_id}")

        except Exception as e:
            raise SimulationError(f"Failed to add object '{obj_state.id}': {e}") from e

    def move_object(
        self,
        object_id: str,
        target_position: List[float],
        target_orientation_quaternion: Optional[List[float]] = None
    ):
        """Move an object to a new position."""
        if object_id not in self.objects_pb_ids:
            raise SimulationError(f"Unknown object ID: '{object_id}'")

        try:
            body_id = self.objects_pb_ids[object_id]

            if target_orientation_quaternion is None:
                _, current_orientation = p.getBasePositionAndOrientation(
                    body_id,
                    physicsClientId=self.client_id
                )
                target_orientation_quaternion = list(current_orientation)

            p.resetBasePositionAndOrientation(
                body_id,
                target_position,
                target_orientation_quaternion,
                physicsClientId=self.client_id
            )
            self.logger.debug(f"Moved object '{object_id}' to {target_position}")
        except Exception as e:
            raise SimulationError(f"Failed to move object '{object_id}': {e}") from e

    def simulate_steps(self, steps: int = 10):
        """Run physics simulation for specified steps."""
        try:
            for _ in range(steps):
                p.stepSimulation(physicsClientId=self.client_id)
            self.logger.debug(f"Simulated {steps} physics steps")
        except Exception as e:
            raise SimulationError(f"Simulation step failed: {e}") from e

    def get_current_state_for_visualization(self) -> List[Dict[str, Any]]:
        """Get current state of all objects for visualization."""
        viz_state = []
        for obj_id, body_id in self.objects_pb_ids.items():
            try:
                pos, orn_quat = p.getBasePositionAndOrientation(
                    body_id,
                    physicsClientId=self.client_id
                )
                original_config = self.object_configs.get(obj_id)
                if original_config:
                    viz_state.append({
                        "id": obj_id,
                        "type": original_config.type,
                        "position": list(pos),
                        "orientation_quaternion": list(orn_quat),
                        "scale": original_config.scale,
                        "color_rgba": original_config.color_rgba
                    })
            except Exception as e:
                self.logger.warning(f"Failed to get state for object '{obj_id}': {e}")
        return viz_state

    def calculate_distance(self, obj1_id: str, obj2_id: str) -> float:
        """Calculate distance between two objects."""
        pos1, pos2 = None, None
        current_state = self.get_current_state_for_visualization()

        for obj_data in current_state:
            if obj_data["id"] == obj1_id:
                pos1 = obj_data["position"]
            if obj_data["id"] == obj2_id:
                pos2 = obj_data["position"]

        if pos1 and pos2:
            return math.sqrt(sum((a - b) ** 2 for a, b in zip(pos1, pos2)))

        self.logger.warning(
            f"Could not calculate distance between '{obj1_id}' and '{obj2_id}'"
        )
        return float('inf')

    def cleanup(self):
        """Clean up physics simulation resources."""
        if self.client_id != -1:
            try:
                p.disconnect(physicsClientId=self.client_id)
                self.client_id = -1
                self.logger.info("Physics simulation cleaned up")
            except Exception as e:
                self.logger.error(f"Error during cleanup: {e}")


class SpatialEnvironmentMVP:
    """
    Main spatial reasoning environment.

    Improvements over original:
    - No global state
    - Configurable visualization
    - Better error handling
    - Structured logging
    - Modular design
    """

    def __init__(self, enable_visualization: bool = True):
        """
        Initialize spatial environment.

        Args:
            enable_visualization: Whether to enable WebSocket visualization updates
        """
        self.simulator = MVPPhysicsSimulator()
        self.current_task: Optional[SpatialTask] = None
        self.task_id_counter = 0
        self.enable_visualization = enable_visualization
        self.visualization_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.scorer = SpatialScorer()
        self.logger = setup_logger(f"{__name__}.SpatialEnvironmentMVP")

    async def initialize_task(self, task: SpatialTask):
        """Initialize the environment with a specific task."""
        if not isinstance(task, SpatialTask):
            raise ValueError("Invalid task object provided to initialize_task")

        self.current_task = task
        self.logger.info(
            f"Initializing task '{task.task_id}': {task.description[:50]}..."
        )

        self.simulator.initialize(task.initial_objects)

        if self.enable_visualization:
            await self.notify_visualization_clients(
                self.simulator.get_current_state_for_visualization()
            )

        self.logger.info(f"Task '{task.task_id}' initialized successfully")

    async def notify_visualization_clients(self, scene_state: List[Dict[str, Any]]):
        """Notify all connected visualization clients of state updates."""
        if not self.enable_visualization or not self.visualization_clients:
            return

        message = json.dumps({"type": "scene_update", "payload": scene_state})

        # Send to all clients, handling failures gracefully
        results = await asyncio.gather(
            *[client.send(message) for client in self.visualization_clients],
            return_exceptions=True
        )

        # Log any failures
        failures = [r for r in results if isinstance(r, Exception)]
        if failures:
            self.logger.warning(f"Failed to notify {len(failures)} visualization clients")

    async def apply_action_and_get_outcome(
        self,
        parsed_action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply a parsed action and return the outcome.

        Args:
            parsed_action: Action dictionary with type and parameters

        Returns:
            Dictionary with reward, done status, observation, etc.
        """
        if not self.current_task:
            raise TaskNotInitializedError(
                "No current task set. Call initialize_task first."
            )

        self.logger.info(
            f"Task '{self.current_task.task_id}': Applying action {parsed_action.get('action_type')}"
        )

        action_executed = False

        # Execute action if valid
        if parsed_action and parsed_action.get("action_type") == "move_object":
            object_id = parsed_action.get("object_id", self.current_task.target_object_id)
            target_position = parsed_action.get("target_position")
            target_orientation = parsed_action.get("target_orientation_quaternion")

            if object_id and target_position:
                try:
                    self.simulator.move_object(object_id, target_position, target_orientation)
                    action_executed = True
                    self.logger.debug(f"Moved '{object_id}' to {target_position}")
                except SimulationError as e:
                    self.logger.error(f"Failed to execute action: {e}")
            else:
                self.logger.warning("move_object action missing required fields")
        else:
            action_type = parsed_action.get("action_type", "unknown")
            self.logger.warning(f"Unhandled action type: '{action_type}'")

        # Simulate physics
        sim_steps = (
            SCORING.SIMULATION_STEPS_WITH_ACTION if action_executed
            else SCORING.SIMULATION_STEPS_NO_ACTION
        )
        self.simulator.simulate_steps(sim_steps)

        # Get new state
        new_state_viz = self.simulator.get_current_state_for_visualization()

        if self.enable_visualization:
            await self.notify_visualization_clients(new_state_viz)

        # Calculate score using the new scoring module
        distance = self.simulator.calculate_distance(
            self.current_task.target_object_id,
            self.current_task.reference_object_id
        )

        # Get positions for scoring
        final_target_pos = self._extract_position(
            new_state_viz,
            self.current_task.target_object_id
        )
        initial_ref_pos = self._extract_position(
            self.current_task.initial_objects,
            self.current_task.reference_object_id
        )

        # Use scorer
        score, score_metadata = self.scorer.calculate_score(
            distance=distance,
            target_distance=self.current_task.target_distance,
            target_pos=final_target_pos or [0, 0, 0],
            reference_pos=initial_ref_pos or [0, 0, 0]
        )

        is_done = True  # Single-step tasks for now

        observation = (
            f"Action '{parsed_action.get('action_type')}' applied. "
            f"Distance: {distance:.2f}. Score: {score}. "
            f"Side condition: {score_metadata.get('side_condition_met')}"
        )

        return {
            "new_state_viz": new_state_viz,
            "reward": score,
            "done": is_done,
            "observation": observation,
            "score_metadata": score_metadata,
            "message": "Action applied and outcome calculated"
        }

    @staticmethod
    def _extract_position(
        objects: Any,
        object_id: str
    ) -> Optional[List[float]]:
        """Extract position from objects list (works with ObjectState or dict)."""
        if not objects:
            return None

        for obj in objects:
            # Handle ObjectState dataclass
            if hasattr(obj, 'id') and obj.id == object_id:
                return obj.position
            # Handle dict
            elif isinstance(obj, dict) and obj.get('id') == object_id:
                return obj.get('position')

        return None

    async def get_next_item(self) -> Dict[str, Any]:
        """Generate a default task for testing/demo purposes."""
        self.task_id_counter += 1
        task_id = f"default_task_type_{self.task_id_counter}_{uuid.uuid4().hex[:4]}"

        objects = [
            ObjectState(
                id="red_cube",
                type="cube",
                position=[2.0, 0.5, 0.5],
                scale=[1, 1, 1],
                color_rgba=TASK.COLOR_RED
            ),
            ObjectState(
                id="blue_sphere",
                type="sphere",
                position=[-2.0, 0.5, 0.5],
                scale=[1, 1, 1],
                color_rgba=TASK.COLOR_BLUE
            )
        ]

        task_description = (
            "The red cube and blue sphere are on opposite sides of the YZ plane. "
            "Move the red cube to remain on the opposite side but position it "
            "approximately 1.0 unit away from the blue sphere."
        )

        goal_description = (
            "The red_cube's x-coordinate should have opposite sign to blue_sphere's x. "
            "Distance between centers should be approximately 1.0 unit."
        )

        current_default_task = SpatialTask(
            task_id=task_id,
            description=task_description,
            initial_objects=objects,
            goal_description=goal_description,
            target_object_id="red_cube",
            reference_object_id="blue_sphere",
            target_distance=TASK.DEFAULT_TARGET_DISTANCE
        )

        await self.initialize_task(current_default_task)

        return {
            "task_id": current_default_task.task_id,
            "llm_prompt": self._create_llm_prompt(
                current_default_task,
                current_default_task.initial_objects
            )
        }

    def _create_llm_prompt(
        self,
        task: SpatialTask,
        initial_objects_state: List[ObjectState]
    ) -> str:
        """Create LLM prompt for the task."""
        objects_desc_parts = []
        for obj_state in initial_objects_state:
            objects_desc_parts.append(
                f"- ID: {obj_state.id}, Type: {obj_state.type}, "
                f"Position: [{obj_state.position[0]:.2f}, {obj_state.position[1]:.2f}, {obj_state.position[2]:.2f}]"
            )
        objects_desc = "\n".join(objects_desc_parts)

        ref_obj_pos_str = "N/A"
        for obj_state in initial_objects_state:
            if obj_state.id == task.reference_object_id:
                ref_obj_pos_str = (
                    f"[{obj_state.position[0]:.2f}, {obj_state.position[1]:.2f}, "
                    f"{obj_state.position[2]:.2f}]"
                )
                break

        hint = (
            f"Hint: The {task.reference_object_id} is at {ref_obj_pos_str}. "
            f"To keep {task.target_object_id} on the opposite side of the YZ plane, "
            f"its x-coordinate should have opposite sign. "
            f"Position it about {task.target_distance:.1f} unit away."
        )

        return f"""Task: {task.description}
Goal: {task.goal_description}

Available Objects (initial state):
{objects_desc}

{hint}

You control: '{task.target_object_id}'.
Your action MUST be a JSON object like:
{{
    "action_type": "move_object",
    "object_id": "{task.target_object_id}",
    "target_position": [x_float, y_float, z_float]
}}
Only provide the JSON. No other text.
Your JSON action:"""

    async def collect_trajectories(
        self,
        item_from_get_next: Dict[str, Any],
        llm_completion_raw: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Orchestrate a single trajectory collection.

        Refactored to be more modular and easier to understand.
        """
        if not self.current_task:
            raise TaskNotInitializedError(
                "No current task set. Call get_next_item or initialize_task first."
            )

        # Get LLM action
        llm_response = await self._get_llm_action(item_from_get_next, llm_completion_raw)

        # Parse action
        parsed_action = self._parse_llm_action(llm_response)

        # Apply action
        outcome = await self.apply_action_and_get_outcome(parsed_action)

        # Build result
        return self._build_trajectory_result(llm_response, parsed_action, outcome)

    async def _get_llm_action(
        self,
        item: Dict[str, Any],
        provided_response: Optional[str]
    ) -> str:
        """Get LLM action, either from provided response or by calling LLM."""
        if provided_response:
            return provided_response

        prompt = item.get(
            "llm_prompt",
            self._create_llm_prompt(self.current_task, self.current_task.initial_objects)
        )

        try:
            self.logger.debug(f"Calling LLM with timeout={LLM.TIMEOUT_SECONDS}s")
            response = await asyncio.wait_for(
                get_anthropic_completion(prompt),
                timeout=LLM.TIMEOUT_SECONDS
            )
            return response
        except asyncio.TimeoutError:
            self.logger.warning(f"LLM call timed out after {LLM.TIMEOUT_SECONDS}s")
            return '{"error": "LLM Timeout"}'
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            return f'{{"error": "LLM Exception: {str(e)}"}}'

    def _parse_llm_action(self, llm_response: str) -> Dict[str, Any]:
        """Parse LLM response into action dict, with fallback."""
        if not llm_response or not isinstance(llm_response, str):
            return self._get_fallback_action()

        try:
            json_str = self._clean_json_string(llm_response)
            action_data = json.loads(json_str)

            if self._is_valid_action(action_data):
                return action_data
            else:
                self.logger.warning(f"Invalid action structure: {action_data}")
                return self._get_fallback_action()

        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON decode error: {e}")
            return self._get_fallback_action()

    @staticmethod
    def _clean_json_string(json_str: str) -> str:
        """Remove markdown code fences from JSON strings."""
        json_str = json_str.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        elif json_str.startswith("```"):
            json_str = json_str[3:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        return json_str.strip()

    def _is_valid_action(self, action: Dict[str, Any]) -> bool:
        """Validate action structure."""
        return (
            action.get("action_type") == "move_object" and
            action.get("object_id") == self.current_task.target_object_id and
            isinstance(action.get("target_position"), list) and
            len(action.get("target_position")) == 3
        )

    def _get_fallback_action(self) -> Dict[str, Any]:
        """Return a default action when LLM fails."""
        return {
            "action_type": "move_object",
            "object_id": self.current_task.target_object_id,
            "target_position": LLM.FALLBACK_POSITION
        }

    def _build_trajectory_result(
        self,
        llm_response: str,
        action: Dict[str, Any],
        outcome: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build the final trajectory result dictionary."""
        return {
            "request_id": self.current_task.task_id,
            "prompt_used": self._create_llm_prompt(
                self.current_task,
                self.current_task.initial_objects
            ),
            "llm_completion_raw": llm_response,
            "parsed_action": action,
            "score": outcome.get("reward"),
            "metadata": {
                "task_description": self.current_task.description,
                "final_distance": self.simulator.calculate_distance(
                    self.current_task.target_object_id,
                    self.current_task.reference_object_id
                ),
                "target_distance": self.current_task.target_distance,
                "score_breakdown": outcome.get("score_metadata"),
                "final_sim_state_viz": outcome.get("new_state_viz"),
                "observation_from_action": outcome.get("observation"),
                "action_done_status": outcome.get("done")
            }
        }


class MVPDemoRunner:
    """Runs demo turns for testing."""

    def __init__(self, enable_visualization: bool = True):
        self.env = SpatialEnvironmentMVP(enable_visualization=enable_visualization)
        self.logger = setup_logger(f"{__name__}.MVPDemoRunner")

    async def run_single_turn_demo(self, use_real_llm: bool = True) -> Dict[str, Any]:
        """Run a single demo turn."""
        self.logger.info("--- Running MVP Demo Turn ---")

        next_item_data = await self.env.get_next_item()
        task_id = next_item_data["task_id"]
        self.logger.info(f"Task ID: {task_id}")

        result = await self.env.collect_trajectories(
            next_item_data,
            llm_completion_raw=None
        )

        self.logger.info(f"--- Result for Task {task_id} ---")
        self.logger.info(f"Final Score: {result['score']:.2f}")
        self.logger.info(
            f"Distance: {result['metadata']['final_distance']:.2f} "
            f"(Target: {result['metadata']['target_distance']:.2f})"
        )

        return result


async def visualization_websocket_handler(
    websocket: websockets.WebSocketServerProtocol,
    env_instance: SpatialEnvironmentMVP,
    demo_runner: MVPDemoRunner
):
    """
    Handles WebSocket connections for visualization.

    Refactored to use dependency injection instead of globals.
    """
    env_instance.visualization_clients.add(websocket)
    logger.info(
        f"Visualization client connected: {websocket.remote_address} "
        f"(Total: {len(env_instance.visualization_clients)})"
    )

    try:
        # Send initial state
        if env_instance.simulator.client_id != -1:
            initial_state = env_instance.simulator.get_current_state_for_visualization()
            await websocket.send(
                json.dumps({"type": "initial_scene", "payload": initial_state})
            )

        # Handle messages
        async for message_str in websocket:
            logger.debug(f"Message from viz client: {message_str}")

            try:
                data = json.loads(message_str)
                command = data.get("command")

                if command == "next_llm_task":
                    logger.info("Received 'next_llm_task' command from client")
                    asyncio.create_task(demo_runner.run_single_turn_demo(use_real_llm=True))
                else:
                    logger.warning(f"Unknown command received: {command}")

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client: {message_str}")
            except Exception as e:
                logger.error(f"Error processing client command: {e}", exc_info=True)

    except websockets.exceptions.ConnectionClosed:
        logger.info(
            f"Visualization client disconnected "
            f"(Total: {len(env_instance.visualization_clients) - 1})"
        )
    except Exception as e:
        logger.error(f"Error in websocket handler: {e}", exc_info=True)
    finally:
        env_instance.visualization_clients.discard(websocket)


async def process_mode(args):
    """Run in process mode to generate trajectory data."""
    logger.info(
        f"Running in 'process' mode: generating {args.num_turns} trajectories "
        f"to {args.output_file}"
    )

    run_name = f"padres_process_{args.num_turns}turns_{uuid.uuid4().hex[:4]}"
    wandb_is_initialized = False

    try:
        wandb.init(
            project="nous_hackathon_padres",
            name=run_name,
            config=vars(args)
        )
        logger.info(f"W&B Run initialized: {run_name}. View at: {wandb.run.get_url()}")
        wandb_is_initialized = True
    except Exception as e:
        logger.warning(f"W&B initialization failed: {e}. Proceeding without W&B logging.")

    # Create demo runner with visualization disabled for process mode
    demo_runner = MVPDemoRunner(enable_visualization=False)
    results_to_write = []

    try:
        for i in range(args.num_turns):
            turn_num = i + 1
            logger.info(f"--- Generating Trajectory Turn {turn_num}/{args.num_turns} ---")

            turn_result = await demo_runner.run_single_turn_demo()
            results_to_write.append(turn_result)

            if wandb_is_initialized and wandb.run:
                wandb_log_data = {
                    "turn": turn_num,
                    "task_id": turn_result.get("request_id", "N/A"),
                    "score": turn_result.get("score", 0.0),
                    "final_distance": turn_result.get("metadata", {}).get("final_distance", float('inf')),
                    "target_distance": turn_result.get("metadata", {}).get("target_distance", 0.0),
                }

                # Extract score metadata
                score_breakdown = turn_result.get("metadata", {}).get("score_breakdown", {})
                wandb_log_data["side_condition_met"] = int(
                    score_breakdown.get("side_condition_met", False)
                )

                # Log action details
                if turn_result.get("parsed_action"):
                    parsed_action = turn_result["parsed_action"]
                    wandb_log_data["action_object_id"] = parsed_action.get("object_id")
                    target_pos = parsed_action.get("target_position", [None, None, None])
                    wandb_log_data["action_target_x"] = target_pos[0] if len(target_pos) > 0 else None
                    wandb_log_data["action_target_y"] = target_pos[1] if len(target_pos) > 1 else None
                    wandb_log_data["action_target_z"] = target_pos[2] if len(target_pos) > 2 else None

                wandb.log(wandb_log_data)
                logger.info(f"Logged to W&B: Turn {turn_num}, Score: {turn_result.get('score')}")

            await asyncio.sleep(0.1)

        # Write results to file
        with open(args.output_file, 'w') as f:
            for result_item in results_to_write:
                f.write(json.dumps(result_item) + '\n')
        logger.info(f"Successfully wrote {len(results_to_write)} trajectories to {args.output_file}")

    finally:
        if demo_runner.env.simulator:
            demo_runner.env.simulator.cleanup()
        if wandb_is_initialized and wandb.run:
            wandb.finish()
            logger.info("Processing complete. W&B run finished.")
        else:
            logger.info("Processing complete.")


async def server_mode():
    """Run in server mode with WebSocket visualization."""
    demo_runner = MVPDemoRunner(enable_visualization=True)

    # Create WebSocket handler with proper dependency injection
    async def handler(websocket):
        await visualization_websocket_handler(websocket, demo_runner.env, demo_runner)

    websocket_server = await websockets.serve(
        handler,
        VISUALIZATION.DEFAULT_HOST,
        VISUALIZATION.DEFAULT_PORT
    )

    logger.info(
        f"Visualization WebSocket Server started on "
        f"ws://{VISUALIZATION.DEFAULT_HOST}:{VISUALIZATION.DEFAULT_PORT}"
    )
    logger.info("Open visualization/index.html in your browser.")
    logger.info("Press Ctrl+C to stop.")

    try:
        # Run auto demo turns
        for i in range(VISUALIZATION.AUTO_DEMO_TURNS):
            logger.info(f"--- Auto Demo Turn {i + 1} ---")
            await demo_runner.run_single_turn_demo(use_real_llm=True)
            await asyncio.sleep(VISUALIZATION.DEMO_TURN_DELAY_SECONDS)

        logger.info(
            "Automatic demo turns complete. "
            "Server is still running for manual interaction."
        )
        await websocket_server.wait_closed()

    except KeyboardInterrupt:
        logger.info("Shutting down servers...")
    finally:
        websocket_server.close()
        await websocket_server.wait_closed()
        if demo_runner.env.simulator:
            demo_runner.env.simulator.cleanup()
        logger.info("Servers and physics simulation stopped.")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Spatial RL Environment MVP (Refactored)")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    process_parser = subparsers.add_parser('process', help='Generate trajectory data')
    process_parser.add_argument(
        '--num_turns',
        type=int,
        default=5,
        help='Number of trajectory turns to generate'
    )
    process_parser.add_argument(
        '--output_file',
        type=str,
        default='trajectories.jsonl',
        help='File to save trajectory data'
    )

    args, unknown = parser.parse_known_args()

    if args.command == 'process':
        await process_mode(args)
    elif args.command is None and not unknown:
        logger.info("No command specified, running in default server mode.")
        await server_mode()
    elif unknown:
        logger.error(f"Unknown arguments or command: {unknown}")
        parser.print_help()
        sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
