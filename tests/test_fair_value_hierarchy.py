"""
Tests for FairValueHierarchyClassifier – src/core/intelligence_kernel/fair_value_hierarchy.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pytest
from datetime import datetime, timedelta
from core.intelligence_kernel.fair_value_hierarchy import (
    FairValueHierarchyClassifier,
    ClassificationResult,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def classifier():
    return FairValueHierarchyClassifier(
        level_2_threshold_months=12,
        active_market_threshold=10,
    )


def _recent_mls_source(source_id: str) -> dict:
    """A data source that would normally be classified as Level 2."""
    return {
        'id': source_id,
        'type': 'comparable_sale',
        'sale_date': datetime.now().isoformat(),
        'location': 'riyadh_center',
    }


def _old_mls_source(source_id: str) -> dict:
    """A data source older than 12 months → Level 3."""
    return {
        'id': source_id,
        'type': 'comparable_sale',
        'sale_date': (datetime.now() - timedelta(days=400)).isoformat(),
        'location': 'riyadh_center',
    }


def _active_market() -> dict:
    return {'riyadh_center': {'transactions': 20}}


def _inactive_market() -> dict:
    return {'riyadh_center': {'transactions': 3}}


def _level_3_assumption() -> dict:
    return {'id': 'assum_001', 'type': 'rent_growth', 'market_derived': False}


def _level_2_assumption() -> dict:
    return {'id': 'assum_002', 'type': 'market_rent', 'market_derived': True}


# ---------------------------------------------------------------------------
# Basic tests
# ---------------------------------------------------------------------------

class TestClassificationResult:
    def test_returns_classification_result(self, classifier):
        result = classifier.classify([], [], {})
        assert isinstance(result, ClassificationResult)

    def test_empty_inputs_defaults_to_level_3(self, classifier):
        result = classifier.classify([], [], {})
        assert result.hierarchy_level == 3

    def test_disclosure_required_when_level_3(self, classifier):
        result = classifier.classify([], [], {})
        assert result.disclosure_required is True


# ---------------------------------------------------------------------------
# Data source classification
# ---------------------------------------------------------------------------

class TestDataSourceClassification:
    def test_quoted_price_source_is_level_1(self, classifier):
        sources = [{'id': 'src_1', 'type': 'quoted_price'}]
        result = classifier.classify(sources, [], {})
        assert 'src_1' in result.level_1_inputs

    def test_recent_comparable_in_active_market_is_level_2(self, classifier):
        sources = [_recent_mls_source('src_recent')]
        result = classifier.classify(sources, [], _active_market())
        assert 'src_recent' in result.level_2_inputs

    def test_recent_comparable_in_inactive_market_is_level_3(self, classifier):
        sources = [_recent_mls_source('src_inactive')]
        result = classifier.classify(sources, [], _inactive_market())
        assert 'src_inactive' in result.level_3_inputs

    def test_old_comparable_is_level_3(self, classifier):
        sources = [_old_mls_source('src_old')]
        result = classifier.classify(sources, [], _active_market())
        assert 'src_old' in result.level_3_inputs

    def test_unknown_source_type_defaults_to_level_3(self, classifier):
        sources = [{'id': 'src_unk', 'type': 'unknown'}]
        result = classifier.classify(sources, [], {})
        assert 'src_unk' in result.level_3_inputs


# ---------------------------------------------------------------------------
# Assumption classification
# ---------------------------------------------------------------------------

class TestAssumptionClassification:
    def test_rent_growth_assumption_is_level_3(self, classifier):
        result = classifier.classify([], [_level_3_assumption()], {})
        assert 'assum_001' in result.level_3_inputs

    def test_market_derived_cap_rate_is_level_2(self, classifier):
        assumption = {'id': 'assum_cap', 'type': 'cap_rate', 'market_derived': True}
        result = classifier.classify([], [assumption], {})
        assert 'assum_cap' in result.level_2_inputs

    def test_non_market_derived_cap_rate_is_level_3(self, classifier):
        assumption = {'id': 'assum_cap', 'type': 'cap_rate', 'market_derived': False}
        result = classifier.classify([], [assumption], {})
        assert 'assum_cap' in result.level_3_inputs

    def test_market_rent_market_derived_is_level_2(self, classifier):
        result = classifier.classify([], [_level_2_assumption()], {})
        assert 'assum_002' in result.level_2_inputs


# ---------------------------------------------------------------------------
# Overall hierarchy level (highest level used)
# ---------------------------------------------------------------------------

class TestHierarchyLevel:
    def test_all_level_1_means_overall_level_1(self, classifier):
        sources = [{'id': 's1', 'type': 'quoted_price'}]
        result = classifier.classify(sources, [], {})
        assert result.hierarchy_level == 1

    def test_mix_of_level_2_and_3_gives_level_3(self, classifier):
        sources = [_recent_mls_source('s2')]
        assumptions = [_level_3_assumption()]
        result = classifier.classify(sources, assumptions, _active_market())
        assert result.hierarchy_level == 3

    def test_disclosure_not_required_for_level_1_only(self, classifier):
        sources = [{'id': 's1', 'type': 'quoted_price'}]
        result = classifier.classify(sources, [], {})
        assert result.disclosure_required is False


# ---------------------------------------------------------------------------
# Disclosure generation
# ---------------------------------------------------------------------------

class TestDisclosureGeneration:
    def test_generate_disclosure_contains_level(self, classifier):
        result = classifier.classify([], [], {})
        disclosure = classifier.generate_disclosure(result, {'market': 1_000_000})
        assert 'fair_value_hierarchy_level' in disclosure

    def test_level_3_disclosure_contains_extra_keys(self, classifier):
        result = classifier.classify([], [_level_3_assumption()], {})
        disclosure = classifier.generate_disclosure(result, {'market': 1_000_000})
        assert 'level_3_disclosure' in disclosure

    def test_level_1_disclosure_no_extra_keys(self, classifier):
        sources = [{'id': 's1', 'type': 'quoted_price'}]
        result = classifier.classify(sources, [], {})
        disclosure = classifier.generate_disclosure(result, {'market': 1_000_000})
        assert 'level_3_disclosure' not in disclosure
