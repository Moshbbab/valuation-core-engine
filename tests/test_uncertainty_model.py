"""
Tests for UncertaintyModel – src/core/intelligence_kernel/uncertainty_model.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pytest
import numpy as np
from core.intelligence_kernel.uncertainty_model import UncertaintyModel, UncertaintyResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def model():
    return UncertaintyModel()


@pytest.fixture
def comparables_5():
    """Five comparables with adjusted prices close to 1,934,222."""
    return [
        {'adjusted_price': 1_888_341},
        {'adjusted_price': 1_892_174},
        {'adjusted_price': 1_944_596},
        {'adjusted_price': 1_986_462},
        {'adjusted_price': 1_922_317},
    ]


@pytest.fixture
def value_5(comparables_5):
    return np.mean([c['adjusted_price'] for c in comparables_5])


# ---------------------------------------------------------------------------
# UncertaintyResult type
# ---------------------------------------------------------------------------

class TestUncertaintyResultType:
    def test_returns_uncertainty_result(self, model, comparables_5, value_5):
        result = model.calculate_uncertainty(value_5, comparables_5, confidence_level=0.95)
        assert isinstance(result, UncertaintyResult)


# ---------------------------------------------------------------------------
# Confidence interval
# ---------------------------------------------------------------------------

class TestConfidenceInterval:
    def test_ci_lower_less_than_value(self, model, comparables_5, value_5):
        result = model.calculate_uncertainty(value_5, comparables_5, confidence_level=0.95)
        assert result.confidence_interval[0] < value_5

    def test_ci_upper_greater_than_value(self, model, comparables_5, value_5):
        result = model.calculate_uncertainty(value_5, comparables_5, confidence_level=0.95)
        assert result.confidence_interval[1] > value_5

    def test_tighter_ci_with_more_comparables(self, model):
        value = 1_500_000
        few_comps = [
            {'adjusted_price': 1_450_000},
            {'adjusted_price': 1_550_000},
        ]
        many_comps = [
            {'adjusted_price': 1_460_000},
            {'adjusted_price': 1_480_000},
            {'adjusted_price': 1_500_000},
            {'adjusted_price': 1_520_000},
            {'adjusted_price': 1_540_000},
            {'adjusted_price': 1_510_000},
            {'adjusted_price': 1_490_000},
            {'adjusted_price': 1_505_000},
            {'adjusted_price': 1_495_000},
            {'adjusted_price': 1_515_000},
        ]
        few_result = model.calculate_uncertainty(value, few_comps)
        many_result = model.calculate_uncertainty(value, many_comps)
        few_width = few_result.confidence_interval[1] - few_result.confidence_interval[0]
        many_width = many_result.confidence_interval[1] - many_result.confidence_interval[0]
        assert many_width < few_width

    def test_higher_confidence_level_gives_wider_ci(self, model, comparables_5, value_5):
        result_90 = model.calculate_uncertainty(value_5, comparables_5, confidence_level=0.90)
        result_99 = model.calculate_uncertainty(value_5, comparables_5, confidence_level=0.99)
        width_90 = result_90.confidence_interval[1] - result_90.confidence_interval[0]
        width_99 = result_99.confidence_interval[1] - result_99.confidence_interval[0]
        assert width_99 > width_90


# ---------------------------------------------------------------------------
# Standard error
# ---------------------------------------------------------------------------

class TestStandardError:
    def test_standard_error_positive(self, model, comparables_5, value_5):
        result = model.calculate_uncertainty(value_5, comparables_5)
        assert result.standard_error > 0

    def test_standard_error_less_than_value(self, model, comparables_5, value_5):
        result = model.calculate_uncertainty(value_5, comparables_5)
        assert result.standard_error < value_5


# ---------------------------------------------------------------------------
# Coefficient of variation
# ---------------------------------------------------------------------------

class TestCoefficientOfVariation:
    def test_cv_positive(self, model, comparables_5, value_5):
        result = model.calculate_uncertainty(value_5, comparables_5)
        assert result.coefficient_of_variation > 0

    def test_cv_less_than_one_for_normal_data(self, model, comparables_5, value_5):
        result = model.calculate_uncertainty(value_5, comparables_5)
        assert result.coefficient_of_variation < 1.0

    def test_higher_dispersion_gives_higher_cv(self, model):
        value = 1_000_000
        tight_comps = [
            {'adjusted_price': v}
            for v in [990_000, 995_000, 1_000_000, 1_005_000, 1_010_000]
        ]
        wide_comps = [
            {'adjusted_price': v}
            for v in [700_000, 850_000, 1_000_000, 1_150_000, 1_300_000]
        ]
        tight_result = model.calculate_uncertainty(value, tight_comps)
        wide_result = model.calculate_uncertainty(value, wide_comps)
        assert wide_result.coefficient_of_variation > tight_result.coefficient_of_variation


# ---------------------------------------------------------------------------
# Fallback for insufficient comparables
# ---------------------------------------------------------------------------

class TestInsufficientComparablesFallback:
    def test_single_comparable_returns_result(self, model):
        result = model.calculate_uncertainty(1_500_000, [{'adjusted_price': 1_500_000}])
        assert isinstance(result, UncertaintyResult)

    def test_empty_comparables_returns_result(self, model):
        result = model.calculate_uncertainty(1_500_000, [])
        assert isinstance(result, UncertaintyResult)

    def test_fallback_ci_width_is_40_percent_of_value(self, model):
        value = 1_000_000
        result = model.calculate_uncertainty(value, [])
        width = result.confidence_interval[1] - result.confidence_interval[0]
        assert abs(width - value * 0.40) < 1e-4


# ---------------------------------------------------------------------------
# Value range by percentiles
# ---------------------------------------------------------------------------

class TestValueRange:
    def test_value_range_returns_tuple(self, model, comparables_5):
        low, high = model.calculate_value_range(comparables_5)
        assert isinstance(low, float)
        assert isinstance(high, float)

    def test_value_range_low_less_than_high(self, model, comparables_5):
        low, high = model.calculate_value_range(comparables_5)
        assert low < high

    def test_value_range_empty_returns_zeros(self, model):
        low, high = model.calculate_value_range([])
        assert low == 0
        assert high == 0


# ---------------------------------------------------------------------------
# Model stability
# ---------------------------------------------------------------------------

class TestModelStability:
    def test_stable_for_tight_comparables(self, model):
        tight_comps = [
            {'adjusted_price': v}
            for v in [990_000, 995_000, 1_000_000, 1_005_000, 1_010_000]
        ]
        stability = model.assess_model_stability(tight_comps, 1_000_000)
        assert stability['stable']

    def test_unstable_for_dispersed_comparables(self, model):
        dispersed_comps = [
            {'adjusted_price': v}
            for v in [500_000, 800_000, 1_500_000, 2_000_000, 2_500_000]
        ]
        stability = model.assess_model_stability(dispersed_comps, 1_460_000)
        assert not stability['stable']

    def test_stability_result_contains_required_keys(self, model, comparables_5, value_5):
        stability = model.assess_model_stability(comparables_5, value_5)
        for key in ('stable', 'coefficient_of_variation', 'z_score', 'interpretation'):
            assert key in stability

    def test_insufficient_comparables_returns_not_stable(self, model):
        stability = model.assess_model_stability([{'adjusted_price': 1_000_000}], 1_000_000)
        assert not stability['stable']
