"""
Tests for WeightingEngine – src/core/intelligence_kernel/weighting_engine.py
"""

import pytest
from core.intelligence_kernel.weighting_engine import WeightingEngine, WeightingResult

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def engine():
    return WeightingEngine(confidence_interval_pct=0.10)


@pytest.fixture
def equal_approach_values():
    return {"market": 1_000_000.0, "income": 1_000_000.0, "cost": 1_000_000.0}


@pytest.fixture
def uniform_quality():
    return {"market": 1.0, "income": 1.0, "cost": 1.0}


@pytest.fixture
def residential_values():
    return {"market": 1_900_000.0, "income": 1_960_000.0, "cost": 1_880_000.0}


# ---------------------------------------------------------------------------
# Basic functionality
# ---------------------------------------------------------------------------


class TestCalculateWeightedValue:
    def test_returns_weighting_result(self, engine, equal_approach_values, uniform_quality):
        result = engine.calculate_weighted_value(equal_approach_values, uniform_quality, "residential")
        assert isinstance(result, WeightingResult)

    def test_equal_approaches_equal_value(self, engine, equal_approach_values, uniform_quality):
        result = engine.calculate_weighted_value(equal_approach_values, uniform_quality, "residential")
        # All approaches same value → weighted result should equal that value
        assert result.final_value == pytest.approx(1_000_000.0, rel=1e-6)

    def test_weights_sum_to_one(self, engine, residential_values, uniform_quality):
        result = engine.calculate_weighted_value(residential_values, uniform_quality, "residential")
        total = sum(result.weights.values())
        assert total == pytest.approx(1.0, rel=1e-6)

    def test_confidence_interval_tuple(self, engine, residential_values, uniform_quality):
        result = engine.calculate_weighted_value(residential_values, uniform_quality, "residential")
        low, high = result.value_range
        assert low < result.final_value < high

    def test_final_value_within_range(self, engine, residential_values, uniform_quality):
        result = engine.calculate_weighted_value(residential_values, uniform_quality, "residential")
        low, high = result.value_range
        assert low <= result.final_value <= high


# ---------------------------------------------------------------------------
# Property type weights
# ---------------------------------------------------------------------------


class TestPropertyTypeWeights:
    def test_residential_market_weight_highest(self, engine, equal_approach_values, uniform_quality):
        result = engine.calculate_weighted_value(equal_approach_values, uniform_quality, "residential")
        assert result.weights["market"] > result.weights["cost"]

    def test_commercial_income_weight_dominant(self, engine, equal_approach_values, uniform_quality):
        result = engine.calculate_weighted_value(equal_approach_values, uniform_quality, "commercial")
        # For commercial: income weight (0.50) > market weight (0.40)
        assert result.weights["income"] > result.weights["market"]

    def test_land_no_income_weight(self, engine, uniform_quality):
        # Land: income base weight is 0 → should not appear or be 0
        land_values = {"market": 1_000_000.0, "cost": 800_000.0}
        land_quality = {"market": 1.0, "cost": 1.0}
        result = engine.calculate_weighted_value(land_values, land_quality, "land")
        assert result.weights.get("income", 0.0) == pytest.approx(0.0, abs=1e-9)

    def test_unknown_type_defaults_to_residential(self, engine, equal_approach_values, uniform_quality):
        result_res = engine.calculate_weighted_value(equal_approach_values, uniform_quality, "residential")
        result_unk = engine.calculate_weighted_value(equal_approach_values, uniform_quality, "unknown_type")
        assert result_res.weights == result_unk.weights


# ---------------------------------------------------------------------------
# Data quality influence
# ---------------------------------------------------------------------------


class TestQualityAdjustedWeights:
    def test_lower_quality_income_reduces_income_weight(self, engine, residential_values):
        high_income_quality = {"market": 1.0, "income": 1.0, "cost": 1.0}
        low_income_quality = {"market": 1.0, "income": 0.3, "cost": 1.0}

        result_high = engine.calculate_weighted_value(residential_values, high_income_quality, "residential")
        result_low = engine.calculate_weighted_value(residential_values, low_income_quality, "residential")
        assert result_low.weights["income"] < result_high.weights["income"]

    def test_weights_still_sum_to_one_with_varied_quality(self, engine, residential_values):
        quality = {"market": 0.9, "income": 0.6, "cost": 0.4}
        result = engine.calculate_weighted_value(residential_values, quality, "residential")
        assert sum(result.weights.values()) == pytest.approx(1.0, rel=1e-6)


# ---------------------------------------------------------------------------
# Reconcile convenience method
# ---------------------------------------------------------------------------


class TestReconcileApproaches:
    def test_reconcile_returns_weighting_result(self, engine):
        result = engine.reconcile_approaches(
            market_value=1_900_000.0,
            income_value=1_950_000.0,
            cost_value=1_850_000.0,
            property_type="residential",
            data_quality={"market": 1.0, "income": 0.8, "cost": 0.7},
        )
        assert isinstance(result, WeightingResult)

    def test_reconcile_final_value_positive(self, engine):
        result = engine.reconcile_approaches(
            market_value=1_900_000.0,
            income_value=1_950_000.0,
            cost_value=1_850_000.0,
            property_type="residential",
            data_quality={"market": 1.0, "income": 0.8, "cost": 0.7},
        )
        assert result.final_value > 0


# ---------------------------------------------------------------------------
# Single-approach edge case
# ---------------------------------------------------------------------------


class TestSingleApproach:
    def test_single_approach_uses_default_interval(self, engine):
        result = engine.calculate_weighted_value(
            {"market": 1_500_000.0},
            {"market": 1.0},
            "residential",
        )
        low, high = result.value_range
        assert low < 1_500_000.0 < high
