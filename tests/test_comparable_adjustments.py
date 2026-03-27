"""
Tests for ComparableAdjuster – src/core/intelligence_kernel/comparable_adjustments.py
"""

import pytest
from datetime import datetime, timedelta
from core.intelligence_kernel.comparable_adjustments import (
    ComparableAdjuster,
    AdjustmentResult,
    ExcessiveAdjustmentError,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def adjuster():
    return ComparableAdjuster(
        beta_size=0.10,
        beta_bedrooms=0.05,
        beta_bathrooms=0.03,
        beta_age=0.01,
        beta_location=0.15,
        max_total_adjustment=0.25,
    )


@pytest.fixture
def subject():
    return {
        "address": "123 Main St",
        "sqft": 2_500,
        "bedrooms": 4,
        "bathrooms": 3.0,
        "year_built": 2018,
        "location_score": 0.85,
        "property_type": "residential",
    }


@pytest.fixture
def identical_comparable():
    """Comparable identical to subject – all adjustments should be zero."""
    return {
        "id": "comp_same",
        "price": 1_850_000,
        "sqft": 2_500,
        "bedrooms": 4,
        "bathrooms": 3.0,
        "year_built": 2018,
        "location_score": 0.85,
        "sale_date": datetime.now().isoformat(),
    }


@pytest.fixture
def different_comparable():
    """Comparable that differs from subject in every dimension."""
    return {
        "id": "comp_diff",
        "price": 1_600_000,
        "sqft": 2_000,
        "bedrooms": 3,
        "bathrooms": 2.0,
        "year_built": 2010,
        "location_score": 0.70,
        "sale_date": (datetime.now() - timedelta(days=365)).isoformat(),
    }


# ---------------------------------------------------------------------------
# Basic functionality
# ---------------------------------------------------------------------------


class TestCalculateAdjustments:
    def test_returns_adjustment_result(self, adjuster, subject, different_comparable):
        result = adjuster.calculate_adjustments(subject, different_comparable)
        assert isinstance(result, AdjustmentResult)

    def test_identical_comparable_zero_size_adjustment(self, adjuster, subject, identical_comparable):
        result = adjuster.calculate_adjustments(subject, identical_comparable)
        assert result.adjustments["size"] == pytest.approx(0.0)

    def test_identical_comparable_zero_bedroom_adjustment(self, adjuster, subject, identical_comparable):
        result = adjuster.calculate_adjustments(subject, identical_comparable)
        assert result.adjustments["bedrooms"] == pytest.approx(0.0)

    def test_identical_comparable_zero_bathroom_adjustment(self, adjuster, subject, identical_comparable):
        result = adjuster.calculate_adjustments(subject, identical_comparable)
        assert result.adjustments["bathrooms"] == pytest.approx(0.0)

    def test_identical_comparable_zero_age_adjustment(self, adjuster, subject, identical_comparable):
        result = adjuster.calculate_adjustments(subject, identical_comparable)
        assert result.adjustments["age"] == pytest.approx(0.0)

    def test_identical_comparable_zero_location_adjustment(self, adjuster, subject, identical_comparable):
        result = adjuster.calculate_adjustments(subject, identical_comparable)
        assert result.adjustments["location"] == pytest.approx(0.0)

    def test_adjusted_price_calculation(self, adjuster, subject, different_comparable):
        result = adjuster.calculate_adjustments(subject, different_comparable)
        expected = different_comparable["price"] * (1 + result.total_adjustment_pct)
        assert result.adjusted_price == pytest.approx(expected, rel=1e-6)

    def test_total_adjustment_is_sum_of_parts(self, adjuster, subject, different_comparable):
        result = adjuster.calculate_adjustments(subject, different_comparable)
        computed_total = sum(result.adjustments.values())
        assert result.total_adjustment_pct == pytest.approx(computed_total, rel=1e-6)


# ---------------------------------------------------------------------------
# Individual adjustment directions
# ---------------------------------------------------------------------------


class TestAdjustmentDirections:
    def test_larger_subject_positive_size_adjustment(self, adjuster, subject):
        smaller_comp = {
            "id": "c",
            "price": 1_000_000,
            "sqft": 2_000,
            "sale_date": datetime.now().isoformat(),
        }
        result = adjuster.calculate_adjustments(subject, smaller_comp)
        assert result.adjustments["size"] > 0

    def test_smaller_subject_negative_size_adjustment(self, adjuster, subject):
        larger_comp = {
            "id": "c",
            "price": 1_000_000,
            "sqft": 3_000,
            "sale_date": datetime.now().isoformat(),
        }
        result = adjuster.calculate_adjustments(subject, larger_comp)
        assert result.adjustments["size"] < 0

    def test_more_bedrooms_positive_adjustment(self, adjuster, subject):
        fewer_beds_comp = {
            "id": "c",
            "price": 1_000_000,
            "sqft": subject["sqft"],
            "bedrooms": 2,
            "sale_date": datetime.now().isoformat(),
        }
        result = adjuster.calculate_adjustments(subject, fewer_beds_comp)
        assert result.adjustments["bedrooms"] > 0

    def test_newer_subject_positive_age_adjustment(self, adjuster, subject):
        older_comp = {
            "id": "c",
            "price": 1_000_000,
            "sqft": subject["sqft"],
            "year_built": 2005,
            "sale_date": datetime.now().isoformat(),
        }
        result = adjuster.calculate_adjustments(subject, older_comp)
        # Subject is newer → upward adjustment
        assert result.adjustments["age"] > 0

    def test_time_adjustment_positive_for_older_sale(self, adjuster, subject):
        old_sale_comp = {
            "id": "c",
            "price": 1_000_000,
            "sqft": subject["sqft"],
            "sale_date": (datetime.now() - timedelta(days=730)).isoformat(),
        }
        result = adjuster.calculate_adjustments(subject, old_sale_comp, {"annual_appreciation": 0.04})
        assert result.adjustments["time"] > 0


# ---------------------------------------------------------------------------
# Excessive adjustment guard
# ---------------------------------------------------------------------------


class TestExcessiveAdjustment:
    def test_raises_when_adjustment_exceeds_threshold(self, adjuster, subject):
        # Max adjustment is 25%; create a comp that differs heavily
        extreme_comp = {
            "id": "c_extreme",
            "price": 1_000_000,
            "sqft": 500,  # Huge size difference → large positive adjustment
            "bedrooms": 1,
            "bathrooms": 1.0,
            "year_built": 1980,
            "location_score": 0.10,
            "sale_date": (datetime.now() - timedelta(days=700)).isoformat(),
        }
        with pytest.raises(ExcessiveAdjustmentError):
            adjuster.calculate_adjustments(subject, extreme_comp, {"annual_appreciation": 0.04})


# ---------------------------------------------------------------------------
# Adjustment grid
# ---------------------------------------------------------------------------


class TestAdjustmentGrid:
    def test_grid_contains_all_comparables(self, adjuster, subject, different_comparable, identical_comparable):
        grid = adjuster.generate_adjustment_grid(subject, [different_comparable, identical_comparable])
        assert len(grid["comparables"]) == 2

    def test_excessive_comp_marked_rejected(self, adjuster, subject):
        extreme_comp = {
            "id": "c_extreme",
            "price": 1_000_000,
            "sqft": 500,
            "bedrooms": 1,
            "bathrooms": 1.0,
            "year_built": 1980,
            "location_score": 0.10,
            "sale_date": (datetime.now() - timedelta(days=700)).isoformat(),
        }
        grid = adjuster.generate_adjustment_grid(subject, [extreme_comp], {"annual_appreciation": 0.04})
        assert grid["comparables"][0]["status"] == "rejected"

    def test_valid_comp_marked_valid(self, adjuster, subject, identical_comparable):
        grid = adjuster.generate_adjustment_grid(subject, [identical_comparable])
        assert grid["comparables"][0]["status"] == "valid"
