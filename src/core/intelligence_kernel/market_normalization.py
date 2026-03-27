"""
Market Normalization Module
============================

Normalizes heterogeneous market data from multiple sources into standardized format.

Part of Valuation Intelligence Kernel (VIK)
Author: Hemmah Valuation Systems
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np


class NormalizationMethod(Enum):
    """Supported normalization methods."""

    ZSCORE = "zscore"
    MINMAX = "minmax"
    ROBUST = "robust"


@dataclass
class NormalizationParams:
    """Parameters used for normalization."""

    method: str
    mean: Optional[float] = None
    std: Optional[float] = None
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    median: Optional[float] = None
    iqr: Optional[float] = None


@dataclass
class NormalizationResult:
    """Result of normalization operation."""

    normalized_data: List[Dict]
    params: NormalizationParams
    outliers_detected: int
    records_processed: int


class InsufficientDataError(Exception):
    """Raised when insufficient data for normalization."""

    pass


class MarketNormalizer:
    """
    Normalizes market data using statistical methods.

    Supports z-score, min-max, and robust normalization.
    """

    def __init__(self, outlier_threshold: float = 3.0):
        """
        Initialize normalizer.

        Args:
            outlier_threshold: Z-score threshold for outlier detection
        """
        self.outlier_threshold = outlier_threshold

    def normalize(
        self, raw_data: List[Dict], method: str = "zscore", price_field: str = "price", sqft_field: str = "sqft"
    ) -> NormalizationResult:
        """
        Normalize market data.

        Args:
            raw_data: List of property records
            method: Normalization method ('zscore', 'minmax', 'robust')
            price_field: Field name for price
            sqft_field: Field name for square footage

        Returns:
            NormalizationResult with normalized data and parameters

        Raises:
            InsufficientDataError: If less than 3 comparables
        """
        if len(raw_data) < 3:
            raise InsufficientDataError(f"Minimum 3 comparables required, got {len(raw_data)}")

        # Extract price per sqft
        psf_values = []
        valid_records = []

        for record in raw_data:
            if price_field in record and sqft_field in record:
                price = record[price_field]
                sqft = record[sqft_field]

                if sqft > 0:  # Avoid division by zero
                    psf = price / sqft
                    psf_values.append(psf)
                    valid_records.append(record.copy())

        if len(psf_values) < 3:
            raise InsufficientDataError(f"Minimum 3 valid records required, got {len(psf_values)}")

        # Perform normalization based on method
        if method == "zscore":
            result = self._zscore_normalize(valid_records, psf_values)
        elif method == "minmax":
            result = self._minmax_normalize(valid_records, psf_values)
        elif method == "robust":
            result = self._robust_normalize(valid_records, psf_values)
        else:
            raise ValueError(f"Unknown normalization method: {method}")

        return result

    def _zscore_normalize(self, records: List[Dict], psf_values: List[float]) -> NormalizationResult:
        """Z-score normalization."""
        μ = np.mean(psf_values)
        σ = np.std(psf_values)

        if σ == 0:
            raise ValueError("Standard deviation is zero, cannot normalize")

        normalized_data = []
        outliers_detected = 0

        for i, record in enumerate(records):
            psf = psf_values[i]
            normalized_psf = (psf - μ) / σ

            # Flag outliers
            is_outlier = abs(normalized_psf) > self.outlier_threshold
            if is_outlier:
                outliers_detected += 1

            record["price_per_sqft"] = psf
            record["normalized_psf"] = normalized_psf
            record["outlier_flag"] = is_outlier
            record["z_score"] = normalized_psf

            normalized_data.append(record)

        params = NormalizationParams(method="zscore", mean=μ, std=σ)

        return NormalizationResult(
            normalized_data=normalized_data,
            params=params,
            outliers_detected=outliers_detected,
            records_processed=len(records),
        )

    def _minmax_normalize(self, records: List[Dict], psf_values: List[float]) -> NormalizationResult:
        """Min-max normalization to [0, 1] range."""
        min_val = np.min(psf_values)
        max_val = np.max(psf_values)

        if max_val == min_val:
            raise ValueError("All values are identical, cannot normalize")

        normalized_data = []

        for i, record in enumerate(records):
            psf = psf_values[i]
            normalized_psf = (psf - min_val) / (max_val - min_val)

            record["price_per_sqft"] = psf
            record["normalized_psf"] = normalized_psf
            record["outlier_flag"] = False  # Min-max doesn't detect outliers

            normalized_data.append(record)

        params = NormalizationParams(method="minmax", min_val=min_val, max_val=max_val)

        return NormalizationResult(
            normalized_data=normalized_data, params=params, outliers_detected=0, records_processed=len(records)
        )

    def _robust_normalize(self, records: List[Dict], psf_values: List[float]) -> NormalizationResult:
        """Robust normalization using median and IQR."""
        median = np.median(psf_values)
        q1 = np.percentile(psf_values, 25)
        q3 = np.percentile(psf_values, 75)
        iqr = q3 - q1

        if iqr == 0:
            raise ValueError("IQR is zero, cannot normalize")

        normalized_data = []
        outliers_detected = 0

        for i, record in enumerate(records):
            psf = psf_values[i]
            normalized_psf = (psf - median) / iqr

            # Flag outliers (values outside 1.5 × IQR)
            is_outlier = (psf < q1 - 1.5 * iqr) or (psf > q3 + 1.5 * iqr)
            if is_outlier:
                outliers_detected += 1

            record["price_per_sqft"] = psf
            record["normalized_psf"] = normalized_psf
            record["outlier_flag"] = is_outlier

            normalized_data.append(record)

        params = NormalizationParams(method="robust", median=median, iqr=iqr)

        return NormalizationResult(
            normalized_data=normalized_data,
            params=params,
            outliers_detected=outliers_detected,
            records_processed=len(records),
        )

    def denormalize(self, normalized_value: float, params: NormalizationParams) -> float:
        """
        Convert normalized value back to original scale.

        Args:
            normalized_value: Normalized value
            params: Normalization parameters used

        Returns:
            Original scale value
        """
        if params.method == "zscore":
            return normalized_value * params.std + params.mean
        elif params.method == "minmax":
            return normalized_value * (params.max_val - params.min_val) + params.min_val
        elif params.method == "robust":
            return normalized_value * params.iqr + params.median
        else:
            raise ValueError(f"Unknown normalization method: {params.method}")
