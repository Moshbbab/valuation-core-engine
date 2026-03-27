"""
Weighting Engine Module
========================

Applies weighted average to values from different valuation approaches.

Part of Valuation Intelligence Kernel (VIK)
Author: Hemmah Valuation Systems
"""

from typing import Dict, Tuple
from dataclasses import dataclass
from enum import Enum


class PropertyType(Enum):
    """Property type classifications."""

    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    LAND = "land"
    MIXED_USE = "mixed_use"


@dataclass
class WeightingResult:
    """Result of weighting calculation."""

    final_value: float
    weights: Dict[str, float]
    value_range: Tuple[float, float]
    weighted_components: Dict[str, float]


class WeightingEngine:
    """
    Calculates weighted average value from multiple approaches.

    Implements IVS 105 reconciliation methodology.
    """

    # Base weights by property type
    BASE_WEIGHTS = {
        PropertyType.RESIDENTIAL: {"market": 0.60, "income": 0.30, "cost": 0.10},
        PropertyType.COMMERCIAL: {"market": 0.40, "income": 0.50, "cost": 0.10},
        PropertyType.INDUSTRIAL: {"market": 0.30, "income": 0.40, "cost": 0.30},
        PropertyType.LAND: {"market": 0.70, "income": 0.00, "cost": 0.30},
        PropertyType.MIXED_USE: {"market": 0.45, "income": 0.45, "cost": 0.10},
    }

    def __init__(self, confidence_interval_pct: float = 0.10):
        """
        Initialize weighting engine.

        Args:
            confidence_interval_pct: Confidence interval as percentage (default 10%)
        """
        self.confidence_interval_pct = confidence_interval_pct

    def calculate_weighted_value(
        self, approach_values: Dict[str, float], data_quality_scores: Dict[str, float], property_type: str
    ) -> WeightingResult:
        """
        Calculate weighted average value.

        Args:
            approach_values: Values from each approach (e.g., {'market': 500000, 'income': 520000})
            data_quality_scores: Quality score for each approach (0-1)
            property_type: Property type (residential, commercial, etc.)

        Returns:
            WeightingResult with final value and weights
        """
        # Convert property type string to enum
        try:
            prop_type_enum = PropertyType(property_type.lower())
        except ValueError:
            # Default to residential if unknown
            prop_type_enum = PropertyType.RESIDENTIAL

        # Get base weights
        base_weights = self._get_base_weights(prop_type_enum)

        # Adjust weights based on data quality
        adjusted_weights = self._adjust_weights_by_quality(base_weights, data_quality_scores, approach_values)

        # Calculate weighted value
        final_value = 0
        weighted_components = {}

        for approach, weight in adjusted_weights.items():
            if approach in approach_values:
                component_value = weight * approach_values[approach]
                final_value += component_value
                weighted_components[approach] = component_value

        # Calculate confidence interval
        value_range = self._calculate_confidence_interval(final_value, approach_values, adjusted_weights)

        return WeightingResult(
            final_value=final_value,
            weights=adjusted_weights,
            value_range=value_range,
            weighted_components=weighted_components,
        )

    def _get_base_weights(self, property_type: PropertyType) -> Dict[str, float]:
        """Get base weights for property type."""
        return self.BASE_WEIGHTS.get(property_type, self.BASE_WEIGHTS[PropertyType.RESIDENTIAL])

    def _adjust_weights_by_quality(
        self, base_weights: Dict[str, float], quality_scores: Dict[str, float], approach_values: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Adjust weights based on data quality scores.

        Higher quality approaches receive higher weights.
        """
        adjusted_weights = {}

        # Only consider approaches that have both values and quality scores
        for approach in base_weights:
            if approach in approach_values and approach in quality_scores:
                base_weight = base_weights[approach]
                quality = quality_scores[approach]

                # Adjust weight by quality
                adjusted_weights[approach] = base_weight * quality

        # Normalize weights to sum to 1
        total = sum(adjusted_weights.values())

        if total == 0:
            # If no valid approaches, return base weights
            return base_weights

        normalized_weights = {k: v / total for k, v in adjusted_weights.items()}

        return normalized_weights

    def _calculate_confidence_interval(
        self, final_value: float, approach_values: Dict[str, float], weights: Dict[str, float]
    ) -> Tuple[float, float]:
        """
        Calculate confidence interval based on dispersion of approach values.

        If approaches agree closely, interval is narrow.
        If approaches diverge, interval is wider.
        """
        if len(approach_values) < 2:
            # Single approach: use default interval
            margin = final_value * self.confidence_interval_pct
            return (final_value - margin, final_value + margin)

        # Calculate weighted standard deviation
        values = list(approach_values.values())
        mean_value = sum(values) / len(values)

        variance = sum((v - mean_value) ** 2 for v in values) / len(values)
        std_dev = variance**0.5

        # Coefficient of variation
        cv = std_dev / mean_value if mean_value > 0 else 0

        # Adjust interval based on dispersion
        # Higher CV = wider interval
        adjusted_interval_pct = self.confidence_interval_pct * (1 + cv)

        margin = final_value * adjusted_interval_pct

        return (final_value - margin, final_value + margin)

    def reconcile_approaches(
        self,
        market_value: float,
        income_value: float,
        cost_value: float,
        property_type: str,
        data_quality: Dict[str, float],
    ) -> WeightingResult:
        """
        Convenience method to reconcile three approaches.

        Args:
            market_value: Value from market approach
            income_value: Value from income approach
            cost_value: Value from cost approach
            property_type: Property type
            data_quality: Quality scores for each approach

        Returns:
            WeightingResult with reconciled value
        """
        approach_values = {"market": market_value, "income": income_value, "cost": cost_value}

        return self.calculate_weighted_value(approach_values, data_quality, property_type)
