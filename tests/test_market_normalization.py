"""
Tests for MarketNormalizer – src/core/intelligence_kernel/market_normalization.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pytest
import numpy as np
from core.intelligence_kernel.market_normalization import (
    MarketNormalizer,
    NormalizationResult,
    NormalizationParams,
    InsufficientDataError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_records():
    """Five minimal comparable records with varying price-per-sqft."""
    return [
        {'id': 'c1', 'price':   950_000, 'sqft': 1_000},   # PSF =  950
        {'id': 'c2', 'price': 1_320_000, 'sqft': 1_200},   # PSF = 1100
        {'id': 'c3', 'price':   855_000, 'sqft':   900},   # PSF =  950
        {'id': 'c4', 'price': 1_210_000, 'sqft': 1_100},   # PSF = 1100
        {'id': 'c5', 'price': 1_050_000, 'sqft': 1_000},   # PSF = 1050
    ]


@pytest.fixture
def normalizer():
    return MarketNormalizer(outlier_threshold=3.0)


# ---------------------------------------------------------------------------
# Z-score normalisation
# ---------------------------------------------------------------------------

class TestZscoreNormalization:
    def test_returns_normalization_result(self, normalizer, sample_records):
        result = normalizer.normalize(sample_records, method='zscore')
        assert isinstance(result, NormalizationResult)

    def test_correct_record_count(self, normalizer, sample_records):
        result = normalizer.normalize(sample_records, method='zscore')
        assert result.records_processed == len(sample_records)
        assert len(result.normalized_data) == len(sample_records)

    def test_params_populated(self, normalizer, sample_records):
        result = normalizer.normalize(sample_records, method='zscore')
        assert result.params.method == 'zscore'
        assert result.params.mean is not None
        assert result.params.std is not None

    def test_mean_psf_correct(self, normalizer, sample_records):
        psf_values = [r['price'] / r['sqft'] for r in sample_records]
        expected_mean = np.mean(psf_values)
        result = normalizer.normalize(sample_records, method='zscore')
        assert abs(result.params.mean - expected_mean) < 1e-6

    def test_normalized_psf_fields_added(self, normalizer, sample_records):
        result = normalizer.normalize(sample_records, method='zscore')
        for record in result.normalized_data:
            assert 'price_per_sqft' in record
            assert 'normalized_psf' in record
            assert 'z_score' in record
            assert 'outlier_flag' in record

    def test_no_outliers_in_uniform_data(self, normalizer, sample_records):
        # All PSF values are ~1000, so no z-score outliers expected
        result = normalizer.normalize(sample_records, method='zscore')
        assert result.outliers_detected == 0

    def test_outlier_detected_for_extreme_value(self, sample_records):
        # Use a lower threshold (2.0) so the extreme record is detectable
        # (mathematical limit: z_max = sqrt(n-1) ≈ 2.24 for n=6)
        sensitive_normalizer = MarketNormalizer(outlier_threshold=2.0)
        extreme = sample_records.copy()
        extreme.append({'id': 'c_extreme', 'price': 10_000_000, 'sqft': 100})
        result = sensitive_normalizer.normalize(extreme, method='zscore')
        assert result.outliers_detected >= 1


# ---------------------------------------------------------------------------
# Min-max normalisation
# ---------------------------------------------------------------------------

class TestMinMaxNormalization:
    def test_returns_normalization_result(self, normalizer, sample_records):
        result = normalizer.normalize(sample_records, method='minmax')
        assert isinstance(result, NormalizationResult)

    def test_normalized_values_in_range(self, normalizer, sample_records):
        result = normalizer.normalize(sample_records, method='minmax')
        for record in result.normalized_data:
            assert 0.0 <= record['normalized_psf'] <= 1.0

    def test_params_populated(self, normalizer, sample_records):
        result = normalizer.normalize(sample_records, method='minmax')
        assert result.params.min_val is not None
        assert result.params.max_val is not None

    def test_no_outlier_detection_in_minmax(self, normalizer, sample_records):
        result = normalizer.normalize(sample_records, method='minmax')
        assert result.outliers_detected == 0


# ---------------------------------------------------------------------------
# Robust normalisation
# ---------------------------------------------------------------------------

class TestRobustNormalization:
    def test_returns_normalization_result(self, normalizer, sample_records):
        result = normalizer.normalize(sample_records, method='robust')
        assert isinstance(result, NormalizationResult)

    def test_params_populated(self, normalizer, sample_records):
        result = normalizer.normalize(sample_records, method='robust')
        assert result.params.median is not None
        assert result.params.iqr is not None


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

class TestNormalizationErrors:
    def test_insufficient_data_raises(self, normalizer):
        with pytest.raises(InsufficientDataError):
            normalizer.normalize(
                [{'id': 'c1', 'price': 1_000_000, 'sqft': 1_000}],
                method='zscore'
            )

    def test_empty_list_raises(self, normalizer):
        with pytest.raises(InsufficientDataError):
            normalizer.normalize([], method='zscore')

    def test_unknown_method_raises(self, normalizer, sample_records):
        with pytest.raises(ValueError):
            normalizer.normalize(sample_records, method='unknown_method')

    def test_missing_sqft_field_reduces_valid_records(self, normalizer):
        records = [
            {'id': 'c1', 'price': 1_000_000, 'sqft': 1_000},
            {'id': 'c2', 'price': 1_200_000},           # no sqft
            {'id': 'c3', 'price':   900_000},            # no sqft
        ]
        with pytest.raises(InsufficientDataError):
            normalizer.normalize(records, method='zscore')


# ---------------------------------------------------------------------------
# Denormalise round-trip
# ---------------------------------------------------------------------------

class TestDenormalization:
    def test_zscore_round_trip(self, normalizer, sample_records):
        result = normalizer.normalize(sample_records, method='zscore')
        for record in result.normalized_data:
            original_psf = record['price_per_sqft']
            recovered = normalizer.denormalize(record['normalized_psf'], result.params)
            assert abs(recovered - original_psf) < 1e-4

    def test_minmax_round_trip(self, normalizer, sample_records):
        result = normalizer.normalize(sample_records, method='minmax')
        for record in result.normalized_data:
            original_psf = record['price_per_sqft']
            recovered = normalizer.denormalize(record['normalized_psf'], result.params)
            assert abs(recovered - original_psf) < 1e-4

    def test_robust_round_trip(self, normalizer, sample_records):
        result = normalizer.normalize(sample_records, method='robust')
        for record in result.normalized_data:
            original_psf = record['price_per_sqft']
            recovered = normalizer.denormalize(record['normalized_psf'], result.params)
            assert abs(recovered - original_psf) < 1e-4
