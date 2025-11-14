"""
Custom exceptions for spatial RL environment.

These exceptions provide better error handling and make it easier
to distinguish between different failure modes.
"""


class SpatialEnvError(Exception):
    """Base exception for all spatial environment errors."""
    pass


class TaskNotInitializedError(SpatialEnvError):
    """
    Raised when an operation requires an initialized task but none exists.

    Example:
        env.apply_action_and_get_outcome(action)  # Before calling initialize_task()
    """
    pass


class InvalidActionError(SpatialEnvError):
    """
    Raised when action validation fails.

    This can happen when:
    - Action type is not supported
    - Required fields are missing
    - Field values are invalid
    """
    pass


class SimulationError(SpatialEnvError):
    """
    Raised when physics simulation operations fail.

    This can happen when:
    - PyBullet operations fail
    - Object IDs don't exist
    - Physics client is not connected
    """
    pass


class LLMError(SpatialEnvError):
    """
    Raised when LLM API calls fail.

    This can happen when:
    - API key is missing/invalid
    - Request times out
    - Response parsing fails
    - API rate limits exceeded
    """
    pass


class VisualizationError(SpatialEnvError):
    """
    Raised when visualization/WebSocket operations fail.

    This can happen when:
    - WebSocket connection fails
    - Message serialization fails
    - Client disconnects unexpectedly
    """
    pass


class ConfigurationError(SpatialEnvError):
    """
    Raised when configuration is invalid or missing.

    This can happen when:
    - Required environment variables are missing
    - Configuration values are out of valid range
    - Incompatible configuration combinations
    """
    pass
