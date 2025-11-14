"""
Scoring logic for spatial reasoning tasks.

This module handles all scoring calculations for physics-based spatial tasks,
including distance scoring and spatial constraint validation.
"""

import math
from typing import List, Tuple, Dict, Any

from .config import ScoringConfig, SCORING
from .logger import setup_logger

logger = setup_logger(__name__)


class SpatialScorer:
    """
    Handles all scoring logic for spatial tasks.

    The scorer evaluates task performance based on:
    1. Distance accuracy - how close objects are to target distance
    2. Side condition - whether spatial constraints are satisfied
    """

    def __init__(self, config: ScoringConfig = None):
        """
        Initialize scorer with configuration.

        Args:
            config: Scoring configuration (uses default if None)
        """
        self.config = config or SCORING

    def calculate_score(
        self,
        distance: float,
        target_distance: float,
        target_pos: List[float],
        reference_pos: List[float]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculates comprehensive score based on distance and spatial constraints.

        Args:
            distance: Actual distance between target and reference objects
            target_distance: Desired distance
            target_pos: Target object position [x, y, z]
            reference_pos: Reference object position [x, y, z]

        Returns:
            Tuple of (total_score, metadata_dict) where:
                - total_score is a float between 0.0 and 1.0
                - metadata contains scoring breakdown and diagnostics
        """
        # Calculate distance-based score
        distance_score = self._calculate_distance_score(distance, target_distance)

        # Check spatial constraint (side condition)
        side_condition_met = self._check_side_condition(target_pos, reference_pos)

        # Combine scores
        total_score = distance_score
        if side_condition_met:
            total_score += self.config.SCORE_SIDE_CONDITION_BONUS

        # Clamp to valid range
        total_score = min(total_score, self.config.SCORE_MAX)

        # Build metadata
        metadata = {
            "distance_score": round(distance_score, 2),
            "side_condition_met": side_condition_met,
            "side_condition_bonus": self.config.SCORE_SIDE_CONDITION_BONUS if side_condition_met else 0.0,
            "distance": round(distance, 3),
            "target_distance": target_distance,
            "distance_ratio": round(distance / target_distance, 3) if target_distance > 0 else float('inf')
        }

        logger.debug(
            f"Score calculation: distance={distance:.3f}, target={target_distance:.3f}, "
            f"distance_score={distance_score:.2f}, side_condition={side_condition_met}, "
            f"total={total_score:.2f}"
        )

        return round(total_score, 2), metadata

    def _calculate_distance_score(self, distance: float, target: float) -> float:
        """
        Scores based on how close the actual distance is to the target distance.

        Uses tiered scoring:
        - Excellent: within target distance
        - Good: within 1.25x target
        - Fair: within 1.75x target
        - Poor: within 2.5x target
        - Zero: beyond 2.5x target

        Args:
            distance: Actual measured distance
            target: Target distance

        Returns:
            Score component for distance (0.0 to SCORE_EXCELLENT)
        """
        if target <= 0:
            logger.warning(f"Invalid target distance: {target}. Using ratio=1.0")
            ratio = 1.0
        else:
            ratio = distance / target

        if ratio <= self.config.EXCELLENT_DISTANCE_THRESHOLD:
            return self.config.SCORE_EXCELLENT
        elif ratio <= self.config.GOOD_DISTANCE_THRESHOLD:
            return self.config.SCORE_GOOD
        elif ratio <= self.config.FAIR_DISTANCE_THRESHOLD:
            return self.config.SCORE_FAIR
        elif ratio <= self.config.POOR_DISTANCE_THRESHOLD:
            return self.config.SCORE_POOR
        else:
            return 0.0

    def _check_side_condition(
        self,
        target_pos: List[float],
        reference_pos: List[float]
    ) -> bool:
        """
        Checks if target is on the correct side of the YZ plane relative to reference.

        The "side condition" validates that the target object maintains the
        correct spatial relationship to the reference object across the YZ plane
        (i.e., both have the same sign for their X coordinate).

        Special case: If the reference object is very close to the YZ plane
        (X ≈ 0), then the target should also be close to the YZ plane.

        Args:
            target_pos: Target object position [x, y, z]
            reference_pos: Reference object position [x, y, z]

        Returns:
            True if side condition is satisfied, False otherwise
        """
        if len(target_pos) < 1 or len(reference_pos) < 1:
            logger.warning(
                f"Invalid position data: target={target_pos}, reference={reference_pos}"
            )
            return False

        ref_x = reference_pos[0]
        target_x = target_pos[0]

        # Special case: Reference near the YZ plane (X ≈ 0)
        if abs(ref_x) < self.config.SIDE_CONDITION_X_NEAR_ZERO:
            condition_met = abs(target_x) < self.config.SIDE_CONDITION_X_TOLERANCE
            logger.debug(
                f"Side condition (ref near YZ): ref_x={ref_x:.3f}, "
                f"target_x={target_x:.3f}, met={condition_met}"
            )
            return condition_met

        # Normal case: Both should be on same side of YZ plane
        same_sign = math.copysign(1.0, target_x) == math.copysign(1.0, ref_x)
        logger.debug(
            f"Side condition (same side): ref_x={ref_x:.3f}, "
            f"target_x={target_x:.3f}, same_sign={same_sign}"
        )
        return same_sign

    def score_trajectory(
        self,
        initial_state: List[Dict[str, Any]],
        final_state: List[Dict[str, Any]],
        target_object_id: str,
        reference_object_id: str,
        target_distance: float
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Scores a complete trajectory from initial to final state.

        Convenience method that extracts positions and calculates score.

        Args:
            initial_state: Initial scene state (list of object dicts)
            final_state: Final scene state (list of object dicts)
            target_object_id: ID of object being moved
            reference_object_id: ID of reference object
            target_distance: Desired final distance

        Returns:
            Tuple of (score, metadata)

        Raises:
            ValueError: If object IDs not found in states
        """
        # Extract final positions
        target_pos = self._extract_position(final_state, target_object_id)
        ref_pos = self._extract_position(final_state, reference_object_id)

        if target_pos is None or ref_pos is None:
            logger.error(
                f"Could not find objects in final state: "
                f"target={target_object_id}, reference={reference_object_id}"
            )
            return 0.0, {"error": "Objects not found in final state"}

        # Calculate actual distance
        distance = self._calculate_euclidean_distance(target_pos, ref_pos)

        # Get reference initial position for side condition
        ref_initial_pos = self._extract_position(initial_state, reference_object_id)
        if ref_initial_pos is None:
            logger.warning("Reference object not found in initial state, using final position")
            ref_initial_pos = ref_pos

        return self.calculate_score(distance, target_distance, target_pos, ref_initial_pos)

    @staticmethod
    def _extract_position(state: List[Dict[str, Any]], object_id: str) -> List[float]:
        """Extracts position of an object from scene state."""
        for obj in state:
            if obj.get("id") == object_id:
                return obj.get("position")
        return None

    @staticmethod
    def _calculate_euclidean_distance(pos1: List[float], pos2: List[float]) -> float:
        """Calculates Euclidean distance between two 3D positions."""
        if len(pos1) < 3 or len(pos2) < 3:
            logger.warning(f"Invalid positions for distance calc: {pos1}, {pos2}")
            return float('inf')

        return math.sqrt(
            sum((a - b) ** 2 for a, b in zip(pos1[:3], pos2[:3]))
        )
