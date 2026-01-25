"""
Uncertainty Model Module
=========================

Quantifies valuation uncertainty using statistical methods.

Part of Valuation Intelligence Kernel (VIK)
Author: Hemmah Valuation Systems
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass
import numpy as np
from scipy import stats


@dataclass
class UncertaintyResult:
    """Result of uncertainty quantification."""
    standard_error: float
    confidence_interval: Tuple[float, float]
    confidence_level: float
    coefficient_of_variation: float
    prediction_interval: Tuple[float, float]


class UncertaintyModel:
    """
    Quantifies valuation uncertainty.
    
    Uses statistical methods to estimate confidence and prediction intervals.
    """
    
    def calculate_uncertainty(
        self,
        value: float,
        comparables: List[Dict],
        confidence_level: float = 0.95
    ) -> UncertaintyResult:
        """
        Calculate valuation uncertainty.
        
        Args:
            value: Estimated property value
            comparables: List of comparable properties with adjusted prices
            confidence_level: Desired confidence level (default 0.95 = 95%)
            
        Returns:
            UncertaintyResult with intervals and metrics
        """
        if len(comparables) < 2:
            # Insufficient data: use default wide interval
            margin = value * 0.20  # ±20%
            return UncertaintyResult(
                standard_error=margin / 1.96,  # Approximate SE
                confidence_interval=(value - margin, value + margin),
                confidence_level=confidence_level,
                coefficient_of_variation=0.20,
                prediction_interval=(value - margin * 1.5, value + margin * 1.5)
            )
        
        # Extract adjusted prices
        prices = [c.get('adjusted_price', c.get('price', 0)) for c in comparables]
        prices = [p for p in prices if p > 0]  # Filter out invalid prices
        
        if len(prices) < 2:
            # Fallback to default interval
            margin = value * 0.20
            return UncertaintyResult(
                standard_error=margin / 1.96,
                confidence_interval=(value - margin, value + margin),
                confidence_level=confidence_level,
                coefficient_of_variation=0.20,
                prediction_interval=(value - margin * 1.5, value + margin * 1.5)
            )
        
        # Calculate statistics
        σ = np.std(prices, ddof=1)  # Sample standard deviation
        n = len(prices)
        mean_price = np.mean(prices)
        
        # Standard error of the mean
        SE = σ / np.sqrt(n)
        
        # Coefficient of variation
        CV = σ / mean_price if mean_price > 0 else 0
        
        # Degrees of freedom
        df = n - 1
        
        # t-statistic for confidence level
        alpha = 1 - confidence_level
        t_stat = stats.t.ppf(1 - alpha/2, df)
        
        # Confidence interval (for the mean)
        ci_margin = t_stat * SE
        ci_low = value - ci_margin
        ci_high = value + ci_margin
        
        # Prediction interval (for a new observation)
        # Wider than confidence interval
        pi_margin = t_stat * σ * np.sqrt(1 + 1/n)
        pi_low = value - pi_margin
        pi_high = value + pi_margin
        
        return UncertaintyResult(
            standard_error=SE,
            confidence_interval=(ci_low, ci_high),
            confidence_level=confidence_level,
            coefficient_of_variation=CV,
            prediction_interval=(pi_low, pi_high)
        )
    
    def calculate_value_range(
        self,
        comparables: List[Dict],
        percentile_low: float = 0.25,
        percentile_high: float = 0.75
    ) -> Tuple[float, float]:
        """
        Calculate value range using percentiles.
        
        Args:
            comparables: List of comparables with adjusted prices
            percentile_low: Lower percentile (default 25th)
            percentile_high: Upper percentile (default 75th)
            
        Returns:
            Tuple of (low_value, high_value)
        """
        prices = [c.get('adjusted_price', c.get('price', 0)) for c in comparables]
        prices = [p for p in prices if p > 0]
        
        if len(prices) < 2:
            return (0, 0)
        
        low_value = np.percentile(prices, percentile_low * 100)
        high_value = np.percentile(prices, percentile_high * 100)
        
        return (low_value, high_value)
    
    def assess_model_stability(
        self,
        comparables: List[Dict],
        value: float
    ) -> Dict:
        """
        Assess stability of the valuation model.
        
        Returns metrics indicating how stable the model is.
        """
        prices = [c.get('adjusted_price', c.get('price', 0)) for c in comparables]
        prices = [p for p in prices if p > 0]
        
        if len(prices) < 2:
            return {
                'stable': False,
                'reason': 'Insufficient comparables'
            }
        
        mean_price = np.mean(prices)
        σ = np.std(prices, ddof=1)
        CV = σ / mean_price if mean_price > 0 else float('inf')
        
        # Calculate how far the value is from the mean
        z_score = abs(value - mean_price) / σ if σ > 0 else 0
        
        # Model is stable if:
        # 1. CV < 0.15 (low dispersion)
        # 2. Value is within 2 standard deviations of mean
        stable = CV < 0.15 and z_score < 2
        
        return {
            'stable': stable,
            'coefficient_of_variation': CV,
            'z_score': z_score,
            'mean_comparable_price': mean_price,
            'std_dev': σ,
            'interpretation': self._interpret_stability(CV, z_score)
        }
    
    def _interpret_stability(self, cv: float, z_score: float) -> str:
        """Interpret stability metrics."""
        if cv < 0.10:
            dispersion = "very low dispersion"
        elif cv < 0.15:
            dispersion = "low dispersion"
        elif cv < 0.25:
            dispersion = "moderate dispersion"
        else:
            dispersion = "high dispersion"
        
        if z_score < 1:
            position = "very close to comparable mean"
        elif z_score < 2:
            position = "close to comparable mean"
        elif z_score < 3:
            position = "somewhat distant from comparable mean"
        else:
            position = "far from comparable mean"
        
        return f"Model shows {dispersion}, value is {position}"
