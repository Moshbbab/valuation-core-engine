"""
Integration tests for ValuationPipeline – app/pipeline.py
"""

import sys
from pathlib import Path

# Ensure app and src are on the path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))

import pytest
from app.pipeline import ValuationPipeline


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def subject():
    return {
        'address': '123 Test Street, Riyadh',
        'sqft': 2_500,
        'bedrooms': 4,
        'bathrooms': 3.0,
        'year_built': 2018,
        'location_score': 0.85,
        'property_type': 'residential',
    }


@pytest.fixture
def comparables():
    from datetime import datetime, timedelta

    def _comp(i, price, sqft, beds, baths, year, loc, days_ago):
        return {
            'id': f'comp_{i:03d}',
            'address': f'{i} Test Ave, Riyadh',
            'price': price,
            'sqft': sqft,
            'bedrooms': beds,
            'bathrooms': baths,
            'year_built': year,
            'location_score': loc,
            'sale_date': (datetime.now() - timedelta(days=days_ago)).isoformat(),
        }

    return [
        _comp(1, 1_850_000, 2_400, 4, 3.0, 2016, 0.82, 90),
        _comp(2, 1_920_000, 2_600, 4, 3.5, 2019, 0.88, 120),
        _comp(3, 1_780_000, 2_300, 3, 2.5, 2015, 0.80, 60),
        _comp(4, 1_950_000, 2_550, 4, 3.0, 2020, 0.90, 150),
        _comp(5, 1_890_000, 2_450, 4, 3.0, 2017, 0.84, 75),
    ]


@pytest.fixture
def pipeline():
    return ValuationPipeline()


# ---------------------------------------------------------------------------
# Pipeline instantiation
# ---------------------------------------------------------------------------

class TestPipelineInit:
    def test_pipeline_creates_all_modules(self, pipeline):
        assert pipeline.normalizer is not None
        assert pipeline.adjuster is not None
        assert pipeline.weighting_engine is not None
        assert pipeline.hierarchy_classifier is not None
        assert pipeline.uncertainty_model is not None
        assert pipeline.vci_calculator is not None


# ---------------------------------------------------------------------------
# Full pipeline run
# ---------------------------------------------------------------------------

class TestPipelineRun:
    def test_run_returns_dict(self, pipeline, subject, comparables):
        results = pipeline.run(subject, comparables)
        assert isinstance(results, dict)

    def test_run_contains_all_sections(self, pipeline, subject, comparables):
        results = pipeline.run(subject, comparables)
        expected_sections = [
            'normalization', 'adjustments', 'weighting',
            'hierarchy', 'uncertainty', 'vci', 'summary',
        ]
        for section in expected_sections:
            assert section in results, f"Missing section: {section}"

    def test_final_value_positive(self, pipeline, subject, comparables):
        results = pipeline.run(subject, comparables)
        assert results['summary']['final_value'] > 0

    def test_vci_score_in_valid_range(self, pipeline, subject, comparables):
        results = pipeline.run(subject, comparables)
        assert 0 <= results['vci']['score'] <= 100

    def test_hierarchy_level_valid(self, pipeline, subject, comparables):
        results = pipeline.run(subject, comparables)
        assert results['hierarchy']['level'] in {1, 2, 3}

    def test_confidence_interval_brackets_value(self, pipeline, subject, comparables):
        results = pipeline.run(subject, comparables)
        final_value = results['summary']['final_value']
        low, high = results['uncertainty']['confidence_interval']
        assert low < final_value < high

    def test_summary_contains_expected_keys(self, pipeline, subject, comparables):
        results = pipeline.run(subject, comparables)
        summary = results['summary']
        for key in (
            'subject_address', 'property_type', 'size_sqft',
            'final_value', 'value_range', 'price_per_sqft',
            'vci_score', 'confidence_level', 'hierarchy_level', 'date',
        ):
            assert key in summary, f"Missing summary key: {key}"

    def test_price_per_sqft_matches_final_value(self, pipeline, subject, comparables):
        results = pipeline.run(subject, comparables)
        expected_psf = results['summary']['final_value'] / subject['sqft']
        assert results['summary']['price_per_sqft'] == pytest.approx(expected_psf, rel=1e-6)

    def test_normalization_outlier_count_non_negative(self, pipeline, subject, comparables):
        results = pipeline.run(subject, comparables)
        assert results['normalization']['outliers'] >= 0

    def test_adjustments_count_matches_valid_comparables(self, pipeline, subject, comparables):
        results = pipeline.run(subject, comparables)
        # All 5 comparables should produce adjustments (none are extreme)
        assert len(results['adjustments']) == len(comparables)

    def test_weighting_weights_sum_to_one(self, pipeline, subject, comparables):
        results = pipeline.run(subject, comparables)
        total = sum(results['weighting']['weights'].values())
        assert total == pytest.approx(1.0, rel=1e-4)

    def test_value_range_lower_less_than_upper(self, pipeline, subject, comparables):
        results = pipeline.run(subject, comparables)
        low, high = results['summary']['value_range']
        assert low < high


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------

class TestPipelineReproducibility:
    def test_same_input_same_output(self, pipeline, subject, comparables):
        result_1 = pipeline.run(subject, comparables)
        result_2 = pipeline.run(subject, comparables)
        # Final value should be identical for deterministic pipeline
        assert result_1['summary']['final_value'] == pytest.approx(
            result_2['summary']['final_value'], rel=1e-6
        )
