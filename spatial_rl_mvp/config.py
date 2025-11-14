"""
Configuration constants for spatial RL environment.

This module centralizes all magic numbers and configuration values
to make the codebase more maintainable and easier to tune.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class ScoringConfig:
    """Configuration for physics-based scoring."""

    # Distance thresholds (multipliers of target_distance)
    EXCELLENT_DISTANCE_THRESHOLD: float = 1.0
    GOOD_DISTANCE_THRESHOLD: float = 1.25
    FAIR_DISTANCE_THRESHOLD: float = 1.75
    POOR_DISTANCE_THRESHOLD: float = 2.5

    # Score values
    SCORE_EXCELLENT: float = 0.8
    SCORE_GOOD: float = 0.6
    SCORE_FAIR: float = 0.4
    SCORE_POOR: float = 0.2
    SCORE_SIDE_CONDITION_BONUS: float = 0.2
    SCORE_MAX: float = 1.0

    # Physics simulation
    SIMULATION_STEPS_WITH_ACTION: int = 20
    SIMULATION_STEPS_NO_ACTION: int = 5

    # Side condition - tolerance for objects near YZ plane (X ≈ 0)
    SIDE_CONDITION_X_TOLERANCE: float = 0.5
    SIDE_CONDITION_X_NEAR_ZERO: float = 0.01


@dataclass
class LLMConfig:
    """Configuration for LLM integration."""

    TIMEOUT_SECONDS: int = 30
    MAX_RETRIES: int = 3
    FALLBACK_POSITION: List[float] = None

    # Anthropic defaults
    DEFAULT_MODEL: str = "claude-3-5-sonnet-20241022"
    DEFAULT_MAX_TOKENS: int = 1024

    def __post_init__(self):
        if self.FALLBACK_POSITION is None:
            self.FALLBACK_POSITION = [1.0, 0.5, 0.5]


@dataclass
class TaskConfig:
    """Default task configuration."""

    DEFAULT_TARGET_DISTANCE: float = 1.0
    DEFAULT_OBJECT_SCALE: List[float] = None
    DEFAULT_OBJECT_HEIGHT: float = 0.5

    # Default colors (RGBA)
    COLOR_RED: List[float] = None
    COLOR_BLUE: List[float] = None
    COLOR_GREEN: List[float] = None
    COLOR_YELLOW: List[float] = None
    COLOR_DEFAULT: List[float] = None

    def __post_init__(self):
        if self.DEFAULT_OBJECT_SCALE is None:
            self.DEFAULT_OBJECT_SCALE = [1.0, 1.0, 1.0]
        if self.COLOR_RED is None:
            self.COLOR_RED = [1.0, 0.0, 0.0, 1.0]
        if self.COLOR_BLUE is None:
            self.COLOR_BLUE = [0.0, 0.0, 1.0, 1.0]
        if self.COLOR_GREEN is None:
            self.COLOR_GREEN = [0.0, 1.0, 0.0, 1.0]
        if self.COLOR_YELLOW is None:
            self.COLOR_YELLOW = [1.0, 1.0, 0.0, 1.0]
        if self.COLOR_DEFAULT is None:
            self.COLOR_DEFAULT = [0.5, 0.5, 0.5, 1.0]


@dataclass
class PhysicsConfig:
    """Configuration for PyBullet physics simulation."""

    GRAVITY: float = -9.8
    DEFAULT_MASS: float = 1.0

    # Connection modes
    DIRECT_MODE: str = "DIRECT"
    GUI_MODE: str = "GUI"


@dataclass
class VisualizationConfig:
    """Configuration for WebSocket visualization server."""

    DEFAULT_HOST: str = "localhost"
    DEFAULT_PORT: int = 8765
    AUTO_DEMO_TURNS: int = 5
    DEMO_TURN_DELAY_SECONDS: float = 2.0


# Singleton instances - import these in your code
SCORING = ScoringConfig()
LLM = LLMConfig()
TASK = TaskConfig()
PHYSICS = PhysicsConfig()
VISUALIZATION = VisualizationConfig()
