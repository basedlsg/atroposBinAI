"""
Basic test suite for refactored modules.

Run with: pytest spatial_rl_mvp/tests/test_refactored_modules.py -v
"""

import pytest
import asyncio
import math
from typing import List

# Import refactored modules
from spatial_rl_mvp.config import SCORING, LLM, TASK, PHYSICS
from spatial_rl_mvp.exceptions import (
    TaskNotInitializedError,
    InvalidActionError,
    SimulationError
)
from spatial_rl_mvp.logger import setup_logger, get_logger
from spatial_rl_mvp.scoring import SpatialScorer
from spatial_rl_mvp.spatial_env_refactored import (
    ObjectState,
    SpatialTask,
    SpatialEnvironmentMVP,
    MVPPhysicsSimulator,
    MVPDemoRunner
)


# ============================================================================
# Config Tests
# ============================================================================

class TestConfig:
    """Tests for configuration module."""

    def test_scoring_config_values(self):
        """Test that scoring config has expected values."""
        assert SCORING.EXCELLENT_DISTANCE_THRESHOLD == 1.0
        assert SCORING.SCORE_EXCELLENT == 0.8
        assert SCORING.SCORE_SIDE_CONDITION_BONUS == 0.2
        assert SCORING.SIMULATION_STEPS_WITH_ACTION == 20

    def test_llm_config_values(self):
        """Test that LLM config has expected values."""
        assert LLM.TIMEOUT_SECONDS == 30
        assert LLM.MAX_RETRIES == 3
        assert LLM.FALLBACK_POSITION == [1.0, 0.5, 0.5]

    def test_task_config_defaults(self):
        """Test that task config has expected defaults."""
        assert TASK.DEFAULT_TARGET_DISTANCE == 1.0
        assert TASK.DEFAULT_OBJECT_SCALE == [1.0, 1.0, 1.0]
        assert len(TASK.COLOR_RED) == 4  # RGBA


# ============================================================================
# Exception Tests
# ============================================================================

class TestExceptions:
    """Tests for custom exceptions."""

    def test_exception_hierarchy(self):
        """Test that custom exceptions inherit correctly."""
        from spatial_rl_mvp.exceptions import SpatialEnvError

        assert issubclass(TaskNotInitializedError, SpatialEnvError)
        assert issubclass(InvalidActionError, SpatialEnvError)
        assert issubclass(SimulationError, SpatialEnvError)

    def test_exception_raising(self):
        """Test that exceptions can be raised and caught."""
        with pytest.raises(TaskNotInitializedError):
            raise TaskNotInitializedError("Test error")

        with pytest.raises(SimulationError):
            raise SimulationError("Simulation failed")


# ============================================================================
# Logger Tests
# ============================================================================

class TestLogger:
    """Tests for logging utilities."""

    def test_setup_logger(self):
        """Test that logger setup works."""
        logger = setup_logger("test_logger")
        assert logger is not None
        assert logger.name == "test_logger"

    def test_get_logger(self):
        """Test get_logger function."""
        logger = get_logger("another_test_logger")
        assert logger is not None


# ============================================================================
# Scoring Tests
# ============================================================================

class TestSpatialScorer:
    """Tests for spatial scoring logic."""

    def setup_method(self):
        """Setup for each test."""
        self.scorer = SpatialScorer()

    def test_perfect_score(self):
        """Test perfect positioning score."""
        score, metadata = self.scorer.calculate_score(
            distance=1.0,
            target_distance=1.0,
            target_pos=[1.0, 0, 0],
            reference_pos=[0, 0, 0]
        )

        expected_score = SCORING.SCORE_EXCELLENT + SCORING.SCORE_SIDE_CONDITION_BONUS
        assert score == expected_score
        assert metadata['side_condition_met'] is True

    def test_good_score(self):
        """Test good positioning score."""
        score, metadata = self.scorer.calculate_score(
            distance=1.2,
            target_distance=1.0,
            target_pos=[1.2, 0, 0],
            reference_pos=[0, 0, 0]
        )

        expected_score = SCORING.SCORE_GOOD + SCORING.SCORE_SIDE_CONDITION_BONUS
        assert score == expected_score

    def test_poor_positioning(self):
        """Test poor positioning (far from target)."""
        score, metadata = self.scorer.calculate_score(
            distance=3.0,
            target_distance=1.0,
            target_pos=[3.0, 0, 0],
            reference_pos=[0, 0, 0]
        )

        assert score == 0.0  # Beyond all thresholds

    def test_side_condition_failure(self):
        """Test side condition violation (wrong side of YZ plane)."""
        score, metadata = self.scorer.calculate_score(
            distance=1.0,
            target_distance=1.0,
            target_pos=[-1.0, 0, 0],  # Negative X
            reference_pos=[1.0, 0, 0]  # Positive X
        )

        # Good distance but wrong side
        assert score == SCORING.SCORE_EXCELLENT  # No side bonus
        assert metadata['side_condition_met'] is False

    def test_euclidean_distance_calculation(self):
        """Test distance calculation."""
        distance = self.scorer._calculate_euclidean_distance(
            [0, 0, 0],
            [3, 4, 0]
        )
        assert distance == 5.0  # 3-4-5 triangle


# ============================================================================
# Spatial Environment Tests
# ============================================================================

class TestObjectState:
    """Tests for ObjectState dataclass."""

    def test_object_state_creation(self):
        """Test creating object state."""
        obj = ObjectState(
            id="test_cube",
            type="cube",
            position=[1.0, 2.0, 3.0]
        )

        assert obj.id == "test_cube"
        assert obj.type == "cube"
        assert obj.position == [1.0, 2.0, 3.0]
        assert len(obj.orientation_quaternion) == 4
        assert len(obj.scale) == 3


class TestSpatialTask:
    """Tests for SpatialTask dataclass."""

    def test_task_creation(self):
        """Test creating spatial task."""
        objects = [
            ObjectState(id="obj1", type="cube", position=[0, 0, 0]),
            ObjectState(id="obj2", type="sphere", position=[1, 0, 0])
        ]

        task = SpatialTask(
            task_id="test_task",
            description="Test description",
            initial_objects=objects,
            goal_description="Test goal",
            target_object_id="obj1",
            reference_object_id="obj2",
            target_distance=0.5
        )

        assert task.task_id == "test_task"
        assert len(task.initial_objects) == 2
        assert task.target_distance == 0.5


@pytest.mark.asyncio
class TestSpatialEnvironmentMVP:
    """Tests for SpatialEnvironmentMVP."""

    async def test_environment_initialization(self):
        """Test environment can be created."""
        env = SpatialEnvironmentMVP(enable_visualization=False)
        assert env is not None
        assert env.enable_visualization is False
        assert env.simulator is not None

    async def test_task_initialization(self):
        """Test task initialization."""
        env = SpatialEnvironmentMVP(enable_visualization=False)

        objects = [
            ObjectState(id="obj1", type="cube", position=[0, 0, 0.5]),
            ObjectState(id="obj2", type="sphere", position=[1, 0, 0.5])
        ]

        task = SpatialTask(
            task_id="test_task",
            description="Test",
            initial_objects=objects,
            goal_description="Move obj1 near obj2",
            target_object_id="obj1",
            reference_object_id="obj2",
            target_distance=0.5
        )

        await env.initialize_task(task)

        assert env.current_task == task
        assert len(env.simulator.objects_pb_ids) == 2

        # Cleanup
        env.simulator.cleanup()

    async def test_action_without_task_raises_error(self):
        """Test that applying action without task raises error."""
        env = SpatialEnvironmentMVP(enable_visualization=False)

        action = {
            "action_type": "move_object",
            "object_id": "obj1",
            "target_position": [0.5, 0, 0]
        }

        with pytest.raises(TaskNotInitializedError):
            await env.apply_action_and_get_outcome(action)

    async def test_action_execution(self):
        """Test action execution returns proper outcome."""
        env = SpatialEnvironmentMVP(enable_visualization=False)

        objects = [
            ObjectState(id="obj1", type="cube", position=[0, 0, 0.5]),
            ObjectState(id="obj2", type="sphere", position=[1, 0, 0.5])
        ]

        task = SpatialTask(
            task_id="test_task",
            description="Test",
            initial_objects=objects,
            goal_description="Move obj1 near obj2",
            target_object_id="obj1",
            reference_object_id="obj2",
            target_distance=0.5
        )

        await env.initialize_task(task)

        action = {
            "action_type": "move_object",
            "object_id": "obj1",
            "target_position": [0.5, 0, 0.5]
        }

        outcome = await env.apply_action_and_get_outcome(action)

        assert "reward" in outcome
        assert "done" in outcome
        assert "observation" in outcome
        assert isinstance(outcome["reward"], (int, float))

        # Cleanup
        env.simulator.cleanup()

    async def test_llm_prompt_creation(self):
        """Test LLM prompt generation."""
        env = SpatialEnvironmentMVP(enable_visualization=False)

        objects = [
            ObjectState(id="red_cube", type="cube", position=[1, 0, 0.5]),
            ObjectState(id="blue_sphere", type="sphere", position=[-1, 0, 0.5])
        ]

        task = SpatialTask(
            task_id="test",
            description="Test task",
            initial_objects=objects,
            goal_description="Test goal",
            target_object_id="red_cube",
            reference_object_id="blue_sphere",
            target_distance=1.0
        )

        prompt = env._create_llm_prompt(task, objects)

        assert "red_cube" in prompt
        assert "blue_sphere" in prompt
        assert "move_object" in prompt
        assert "JSON" in prompt

    async def test_action_parsing(self):
        """Test action parsing logic."""
        env = SpatialEnvironmentMVP(enable_visualization=False)

        objects = [
            ObjectState(id="obj1", type="cube", position=[0, 0, 0.5])
        ]

        task = SpatialTask(
            task_id="test",
            description="Test",
            initial_objects=objects,
            goal_description="Test",
            target_object_id="obj1",
            reference_object_id="obj1",
            target_distance=1.0
        )

        env.current_task = task

        # Test valid JSON
        valid_json = '{"action_type": "move_object", "object_id": "obj1", "target_position": [1, 0, 0]}'
        action = env._parse_llm_action(valid_json)
        assert action["action_type"] == "move_object"

        # Test JSON with code fences
        fenced_json = '```json\n{"action_type": "move_object", "object_id": "obj1", "target_position": [1, 0, 0]}\n```'
        action = env._parse_llm_action(fenced_json)
        assert action["action_type"] == "move_object"

        # Test invalid JSON
        invalid_json = 'not valid json'
        action = env._parse_llm_action(invalid_json)
        assert action == env._get_fallback_action()


@pytest.mark.asyncio
class TestMVPDemoRunner:
    """Tests for MVPDemoRunner."""

    async def test_demo_runner_creation(self):
        """Test demo runner can be created."""
        runner = MVPDemoRunner(enable_visualization=False)
        assert runner is not None
        assert runner.env is not None


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
class TestIntegration:
    """Integration tests combining multiple components."""

    async def test_full_trajectory_collection(self):
        """Test complete trajectory collection flow."""
        env = SpatialEnvironmentMVP(enable_visualization=False)

        # Create task
        next_item = await env.get_next_item()

        assert "task_id" in next_item
        assert "llm_prompt" in next_item

        # Simulate LLM response
        mock_llm_response = '{"action_type": "move_object", "object_id": "red_cube", "target_position": [-1.5, 0.5, 0.5]}'

        # Collect trajectory
        result = await env.collect_trajectories(next_item, mock_llm_response)

        assert "request_id" in result
        assert "score" in result
        assert "parsed_action" in result
        assert "metadata" in result

        # Cleanup
        env.simulator.cleanup()


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
