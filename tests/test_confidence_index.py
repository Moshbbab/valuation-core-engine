"""
Tests for ConfidenceIndexCalculator – src/core/intelligence_kernel/confidence_index.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pytest
from datetime import datetime, timedelta
from core.intelligence_kernel.confidence_index import (
    ConfidenceIndexCalculator,
    VCIResult,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def calculator():
    return ConfidenceIndexCalculator()


@pytest.fixture
def good_data_sources():
    return [
        {'id': 'src_mls', 'type': 'mls', 'name': 'Riyadh MLS', 'enabled': True},
        {'id': 'src_api', 'type': 'api', 'name': 'Property API', 'enabled': True},
    ]


@pytest.fixture
def good_comparables():
    recent_date = (datetime.now() - timedelta(days=30)).isoformat()
    return [
        {
            'id': f'c{i}',
            'price': 1_900_000,
            'sqft': 2_500,
            'bedrooms': 4,
            'bathrooms': 3.0,
            'sale_date': recent_date,
            'location': 'riyadh_center',
            'adjusted_price': 1_900_000 + i * 10_000,
        }
        for i in range(5)
    ]


@pytest.fixture
def good_adjustments():
    return [{'comparable_id': f'c{i}', 'total_adjustment_pct': 0.02} for i in range(5)]


@pytest.fixture
def active_market():
    return {'transaction_count': 20, 'expected_volume': 15}


@pytest.fixture
def full_disclosure():
    return {'total_inputs': 15, 'disclosed_inputs': 15}


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------

class TestVCIResultType:
    def test_returns_vci_result(
        self, calculator, good_data_sources, good_comparables,
        good_adjustments, active_market, full_disclosure
    ):
        result = calculator.calculate_vci(
            good_data_sources, good_comparables, good_adjustments,
            active_market, full_disclosure
        )
        assert isinstance(result, VCIResult)


# ---------------------------------------------------------------------------
# Score range
# ---------------------------------------------------------------------------

class TestVCIScoreRange:
    def test_score_between_0_and_100(
        self, calculator, good_data_sources, good_comparables,
        good_adjustments, active_market, full_disclosure
    ):
        result = calculator.calculate_vci(
            good_data_sources, good_comparables, good_adjustments,
            active_market, full_disclosure
        )
        assert 0.0 <= result.vci_score <= 100.0

    def test_high_quality_inputs_give_high_score(
        self, calculator, good_data_sources, good_comparables,
        good_adjustments, active_market, full_disclosure
    ):
        result = calculator.calculate_vci(
            good_data_sources, good_comparables, good_adjustments,
            active_market, full_disclosure
        )
        assert result.vci_score >= 70.0

    def test_no_data_gives_low_or_mid_score(self, calculator):
        result = calculator.calculate_vci([], [], [], {}, {})
        # No data → defaults to 50 for most components, some 0 for data quality
        assert 0.0 <= result.vci_score <= 100.0


# ---------------------------------------------------------------------------
# Component scores
# ---------------------------------------------------------------------------

class TestComponentScores:
    def test_five_components_present(
        self, calculator, good_data_sources, good_comparables,
        good_adjustments, active_market, full_disclosure
    ):
        result = calculator.calculate_vci(
            good_data_sources, good_comparables, good_adjustments,
            active_market, full_disclosure
        )
        expected_keys = {
            'data_quality', 'comparable_strength',
            'model_stability', 'market_liquidity', 'disclosure_level'
        }
        assert set(result.component_scores.keys()) == expected_keys

    def test_all_components_in_range(
        self, calculator, good_data_sources, good_comparables,
        good_adjustments, active_market, full_disclosure
    ):
        result = calculator.calculate_vci(
            good_data_sources, good_comparables, good_adjustments,
            active_market, full_disclosure
        )
        for component, score in result.component_scores.items():
            assert 0.0 <= score <= 100.0, f"{component} out of range: {score}"

    def test_full_disclosure_gives_perfect_disclosure_score(
        self, calculator, good_data_sources, good_comparables,
        good_adjustments, active_market, full_disclosure
    ):
        result = calculator.calculate_vci(
            good_data_sources, good_comparables, good_adjustments,
            active_market, full_disclosure
        )
        assert result.component_scores['disclosure_level'] == pytest.approx(100.0)

    def test_active_market_gives_high_liquidity_score(
        self, calculator, good_data_sources, good_comparables,
        good_adjustments, active_market, full_disclosure
    ):
        result = calculator.calculate_vci(
            good_data_sources, good_comparables, good_adjustments,
            active_market, full_disclosure
        )
        assert result.component_scores['market_liquidity'] >= 80.0


# ---------------------------------------------------------------------------
# Confidence level categories
# ---------------------------------------------------------------------------

class TestConfidenceLevel:
    def test_exceptional_when_score_above_90(
        self, calculator, good_data_sources, good_comparables,
        good_adjustments, active_market, full_disclosure
    ):
        result = calculator.calculate_vci(
            good_data_sources, good_comparables, good_adjustments,
            active_market, full_disclosure
        )
        if result.vci_score >= 90:
            assert result.confidence_level == 'EXCEPTIONAL'

    def test_confidence_level_not_empty(
        self, calculator, good_data_sources, good_comparables,
        good_adjustments, active_market, full_disclosure
    ):
        result = calculator.calculate_vci(
            good_data_sources, good_comparables, good_adjustments,
            active_market, full_disclosure
        )
        assert result.confidence_level in {'EXCEPTIONAL', 'HIGH', 'MODERATE', 'LOW'}


# ---------------------------------------------------------------------------
# Interpretation string
# ---------------------------------------------------------------------------

class TestInterpretation:
    def test_interpretation_is_string(
        self, calculator, good_data_sources, good_comparables,
        good_adjustments, active_market, full_disclosure
    ):
        result = calculator.calculate_vci(
            good_data_sources, good_comparables, good_adjustments,
            active_market, full_disclosure
        )
        assert isinstance(result.interpretation, str)
        assert len(result.interpretation) > 0


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

class TestRecommendations:
    def test_recommendations_list_not_empty(
        self, calculator, good_data_sources, good_comparables,
        good_adjustments, active_market, full_disclosure
    ):
        result = calculator.calculate_vci(
            good_data_sources, good_comparables, good_adjustments,
            active_market, full_disclosure
        )
        assert isinstance(result.recommendations, list)
        assert len(result.recommendations) >= 1

    def test_poor_disclosure_triggers_recommendation(self, calculator, good_data_sources,
                                                     good_comparables, good_adjustments,
                                                     active_market):
        poor_disclosure = {'total_inputs': 15, 'disclosed_inputs': 5}
        result = calculator.calculate_vci(
            good_data_sources, good_comparables, good_adjustments,
            active_market, poor_disclosure
        )
        disclosure_recs = [r for r in result.recommendations if 'disclosure' in r.lower()
                           or 'transparency' in r.lower() or 'disclosing' in r.lower()]
        assert len(disclosure_recs) >= 1

    def test_low_liquidity_triggers_recommendation(self, calculator, good_data_sources,
                                                   good_comparables, good_adjustments,
                                                   full_disclosure):
        low_market = {'transaction_count': 2, 'expected_volume': 15}
        result = calculator.calculate_vci(
            good_data_sources, good_comparables, good_adjustments,
            low_market, full_disclosure
        )
        liquidity_recs = [r for r in result.recommendations
                          if 'market' in r.lower() or 'liquidity' in r.lower()
                          or 'transaction' in r.lower() or 'area' in r.lower()]
        assert len(liquidity_recs) >= 1


# ---------------------------------------------------------------------------
# VCI formula weights sum to 1
# ---------------------------------------------------------------------------

class TestVCIWeights:
    def test_weights_sum_to_one(self):
        weights = ConfidenceIndexCalculator.WEIGHTS
        assert sum(weights.values()) == pytest.approx(1.0, rel=1e-6)
