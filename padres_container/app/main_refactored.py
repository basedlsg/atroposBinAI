"""
Refactored Padres API Service

Key improvements:
- No monkey-patching!
- Uses proper dependency injection
- Cleaner code with better error handling
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid
import sys
import os

# Path handling for importing from spatial_rl_mvp
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spatial_rl_mvp.spatial_env_refactored import (
    SpatialEnvironmentMVP,
    SpatialTask,
    ObjectState
)
from spatial_rl_mvp.logger import setup_logger

logger = setup_logger(__name__)

app = FastAPI(title="Padres Simulation Service API (Refactored)")

# Global instance (initialized in startup with visualization disabled)
spatial_env_instance: Optional[SpatialEnvironmentMVP] = None


@app.on_event("startup")
async def startup_event():
    """Initialize environment on startup with visualization disabled."""
    global spatial_env_instance

    try:
        # Simply pass enable_visualization=False - no monkey-patching needed!
        spatial_env_instance = SpatialEnvironmentMVP(enable_visualization=False)
        logger.info("SpatialEnvironmentMVP instance created with visualization disabled")
    except Exception as e:
        logger.error(f"Failed to create SpatialEnvironmentMVP instance: {e}", exc_info=True)
        spatial_env_instance = None


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown."""
    if spatial_env_instance and hasattr(spatial_env_instance, 'simulator'):
        spatial_env_instance.simulator.cleanup()
        logger.info("PyBullet simulation cleaned up")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Padres API is alive! (Refactored version)"}


@app.get("/status")
async def get_status():
    """Get API and simulation status."""
    global spatial_env_instance

    env_status = "Not initialized"
    task_id = "N/A"
    pybullet_client_id = "N/A"

    if spatial_env_instance:
        env_status = "Instance created"

        if hasattr(spatial_env_instance, 'simulator') and spatial_env_instance.simulator:
            pybullet_client_id = str(spatial_env_instance.simulator.client_id)
            if spatial_env_instance.simulator.client_id != -1:
                env_status += ", PyBullet Client Connected"
            else:
                env_status += ", PyBullet Client NOT Connected"
        else:
            env_status += ", Simulator object not found"

        if hasattr(spatial_env_instance, 'current_task') and spatial_env_instance.current_task:
            task_id = spatial_env_instance.current_task.task_id
            env_status += f", Task '{task_id}' loaded"
        else:
            env_status += ", No task loaded"

    return {
        "api_status": "OPERATIONAL",
        "simulation_status_summary": env_status,
        "pybullet_direct_client_id": pybullet_client_id,
        "current_task_id": task_id,
        "notes": "Refactored API with no monkey-patching, using dependency injection"
    }


@app.post("/setup_environment", status_code=201)
async def setup_environment():
    """Initialize environment with a task."""
    global spatial_env_instance

    if not spatial_env_instance:
        logger.error("/setup_environment called but spatial_env_instance is None")
        raise HTTPException(
            status_code=500,
            detail="Spatial environment not available. Check server logs."
        )

    # Define task
    objects = [
        ObjectState(
            id="red_cube",
            type="cube",
            position=[0.5, 0.0, 0.2],
            scale=[0.2, 0.2, 0.2],
            color_rgba=[1, 0, 0, 1]
        ),
        ObjectState(
            id="blue_sphere",
            type="sphere",
            position=[-0.5, 0.0, 0.2],
            scale=[0.2, 0.2, 0.2],
            color_rgba=[0, 0, 1, 1]
        )
    ]

    task_id = f"hardcoded_task_day1_{uuid.uuid4().hex[:4]}"
    current_default_task = SpatialTask(
        task_id=task_id,
        description="Move red cube near blue sphere.",
        initial_objects=objects,
        goal_description="Red cube within 0.3 units of blue sphere.",
        target_object_id="red_cube",
        reference_object_id="blue_sphere",
        target_distance=0.3
    )

    try:
        logger.info(f"/setup_environment - Initializing task: {task_id}")
        await spatial_env_instance.initialize_task(current_default_task)
        logger.info(f"/setup_environment - Task '{task_id}' initialized")

        return {
            "message": "Environment initialized with hardcoded task.",
            "task_id": task_id,
            "status": "SUCCESS"
        }
    except Exception as e:
        logger.error(f"Error in /setup_environment: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize environment: {str(e)}"
        )


@app.post("/execute_action")
async def execute_action():
    """Execute an action in the environment."""
    global spatial_env_instance

    if not spatial_env_instance:
        logger.error("/execute_action called but spatial_env_instance is None")
        raise HTTPException(
            status_code=500,
            detail="Spatial environment not available."
        )

    if not hasattr(spatial_env_instance, 'current_task') or not spatial_env_instance.current_task:
        raise HTTPException(
            status_code=400,
            detail="Environment not initialized with a task. Call /setup_environment first."
        )

    target_obj_id = spatial_env_instance.current_task.target_object_id
    ref_obj_initial_pos = [0.0, 0.0, 0.0]

    # Find reference object's initial position
    for obj_state in spatial_env_instance.current_task.initial_objects:
        if obj_state.id == spatial_env_instance.current_task.reference_object_id:
            ref_obj_initial_pos = obj_state.position
            break

    # Hardcoded action: move target towards reference
    action_to_apply = {
        "action_type": "move_object",
        "object_id": target_obj_id,
        "target_position": [
            ref_obj_initial_pos[0] + (0.1 if target_obj_id == "red_cube" else -0.1),
            ref_obj_initial_pos[1],
            ref_obj_initial_pos[2]
        ]
    }

    try:
        task_id = spatial_env_instance.current_task.task_id
        logger.info(f"/execute_action for task '{task_id}' - Applying: {action_to_apply}")

        outcome = await spatial_env_instance.apply_action_and_get_outcome(action_to_apply)
        obs_msg = outcome.get("observation", "No observation string")

        logger.info(f"/execute_action for task '{task_id}' - Observation: {obs_msg}")

        return {
            "message": "Action executed.",
            "task_id": task_id,
            "action_applied": action_to_apply,
            "observation": obs_msg,
            "reward": outcome.get("reward"),
            "done": outcome.get("done"),
            "full_outcome_debug": outcome
        }
    except Exception as e:
        logger.error(f"Error in /execute_action: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute action: {str(e)}"
        )
