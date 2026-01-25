"""
Valuation Confidence Index (VCI) Module
========================================

Generates a confidence score (0-100) representing valuation reliability.

Part of Valuation Intelligence Kernel (VIK)
Author: Hemmah Valuation Systems
"""

from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime
import numpy as np


@dataclass
class VCIResult:
    """Result of VCI calculation."""
    vci_score: float
    component_scores: Dict[str, float]
    interpretation: str
    confidence_level: str
    recommendations: List[str]


class ConfidenceIndexCalculator:
    """
    Calculates Valuation Confidence Index (VCI).
    
    VCI = w1×DQ + w2×CS + w3×MS + w4×ML + w5×DL
    
    where:
    DQ = Data Quality (0-100)
    CS = Comparable Strength (0-100)
    MS = Model Stability (0-100)
    ML = Market Liquidity (0-100)
    DL = Disclosure Level (0-100)
    """
    
    # Component weights
    WEIGHTS = {
        'data_quality': 0.30,
        'comparable_strength': 0.25,
        'model_stability': 0.20,
        'market_liquidity': 0.15,
        'disclosure_level': 0.10
    }
    
    def calculate_vci(
        self,
        data_sources: List[Dict],
        comparables: List[Dict],
        adjustments: List[Dict],
        market_activity: Dict,
        disclosure_data: Dict
    ) -> VCIResult:
        """
        Calculate Valuation Confidence Index.
        
        Args:
            data_sources: All data sources used
            comparables: Selected comparables
            adjustments: Adjustment calculations
            market_activity: Market activity metrics
            disclosure_data: Disclosure information
            
        Returns:
            VCIResult with score and breakdown
        """
        # Calculate component scores
        dq = self._calculate_data_quality(data_sources, comparables)
        cs = self._calculate_comparable_strength(comparables, adjustments)
        ms = self._calculate_model_stability(comparables)
        ml = self._calculate_market_liquidity(market_activity)
        dl = self._calculate_disclosure_level(disclosure_data)
        
        # Calculate weighted VCI
        vci = (
            self.WEIGHTS['data_quality'] * dq +
            self.WEIGHTS['comparable_strength'] * cs +
            self.WEIGHTS['model_stability'] * ms +
            self.WEIGHTS['market_liquidity'] * ml +
            self.WEIGHTS['disclosure_level'] * dl
        )
        
        # Round to 2 decimal places
        vci = round(vci, 2)
        
        # Component scores
        component_scores = {
            'data_quality': round(dq, 2),
            'comparable_strength': round(cs, 2),
            'model_stability': round(ms, 2),
            'market_liquidity': round(ml, 2),
            'disclosure_level': round(dl, 2)
        }
        
        # Interpretation
        interpretation = self._interpret_vci(vci)
        confidence_level = self._get_confidence_level(vci)
        recommendations = self._generate_recommendations(component_scores)
        
        return VCIResult(
            vci_score=vci,
            component_scores=component_scores,
            interpretation=interpretation,
            confidence_level=confidence_level,
            recommendations=recommendations
        )
    
    def _calculate_data_quality(
        self,
        data_sources: List[Dict],
        comparables: List[Dict]
    ) -> float:
        """
        Calculate Data Quality score (0-100).
        
        DQ = (completeness × 0.4) + (recency × 0.3) + (source_reliability × 0.3)
        """
        if not data_sources and not comparables:
            return 0.0
        
        # Completeness: percentage of required fields present
        completeness = self._assess_completeness(comparables)
        
        # Recency: how recent is the data
        recency = self._assess_recency(comparables)
        
        # Source reliability: quality of data sources
        source_reliability = self._assess_source_reliability(data_sources)
        
        dq = (completeness * 0.4) + (recency * 0.3) + (source_reliability * 0.3)
        
        return min(100, max(0, dq))
    
    def _assess_completeness(self, comparables: List[Dict]) -> float:
        """Assess data completeness."""
        if not comparables:
            return 0.0
        
        required_fields = ['price', 'sqft', 'bedrooms', 'bathrooms', 'sale_date', 'location']
        
        total_fields = len(required_fields) * len(comparables)
        present_fields = 0
        
        for comp in comparables:
            for field in required_fields:
                if field in comp and comp[field] is not None:
                    present_fields += 1
        
        return (present_fields / total_fields) * 100 if total_fields > 0 else 0
    
    def _assess_recency(self, comparables: List[Dict]) -> float:
        """Assess data recency."""
        if not comparables:
            return 0.0
        
        now = datetime.now()
        ages = []
        
        for comp in comparables:
            if 'sale_date' in comp:
                sale_date = comp['sale_date']
                if isinstance(sale_date, str):
                    try:
                        sale_date = datetime.fromisoformat(sale_date.replace('Z', '+00:00'))
                    except:
                        continue
                
                months_old = (now.year - sale_date.year) * 12 + (now.month - sale_date.month)
                ages.append(months_old)
        
        if not ages:
            return 50.0  # Default score if no dates
        
        avg_age = np.mean(ages)
        
        # Score: 100 for <3 months, 0 for >24 months
        if avg_age <= 3:
            return 100.0
        elif avg_age >= 24:
            return 0.0
        else:
            return 100 * (1 - (avg_age - 3) / 21)
    
    def _assess_source_reliability(self, data_sources: List[Dict]) -> float:
        """Assess source reliability."""
        if not data_sources:
            return 50.0  # Default score
        
        # Reliability scores by source type
        reliability_scores = {
            'mls': 95,
            'public_records': 90,
            'api': 85,
            'scraper': 70,
            'manual': 60
        }
        
        scores = []
        for source in data_sources:
            source_type = source.get('type', 'unknown')
            score = reliability_scores.get(source_type, 50)
            scores.append(score)
        
        return np.mean(scores) if scores else 50.0
    
    def _calculate_comparable_strength(
        self,
        comparables: List[Dict],
        adjustments: List[Dict]
    ) -> float:
        """
        Calculate Comparable Strength score (0-100).
        
        CS = 100 × (1 - avg_adjustment_magnitude)
        """
        if not adjustments:
            return 50.0  # Default score
        
        # Extract total adjustment percentages
        adj_magnitudes = []
        
        for adj in adjustments:
            if 'total_adjustment_pct' in adj:
                magnitude = abs(adj['total_adjustment_pct'])
                adj_magnitudes.append(magnitude)
        
        if not adj_magnitudes:
            return 50.0
        
        avg_magnitude = np.mean(adj_magnitudes)
        
        # Score: 100 for 0% adjustment, 0 for 25%+ adjustment
        cs = 100 * (1 - min(avg_magnitude, 0.25) / 0.25)
        
        return max(0, cs)
    
    def _calculate_model_stability(self, comparables: List[Dict]) -> float:
        """
        Calculate Model Stability score (0-100).
        
        MS = 100 × (1 - coefficient_of_variation)
        """
        if len(comparables) < 2:
            return 50.0
        
        prices = [c.get('adjusted_price', c.get('price', 0)) for c in comparables]
        prices = [p for p in prices if p > 0]
        
        if len(prices) < 2:
            return 50.0
        
        mean_price = np.mean(prices)
        std_price = np.std(prices, ddof=1)
        
        cv = std_price / mean_price if mean_price > 0 else 1.0
        
        # Score: 100 for CV=0, 0 for CV>=0.30
        ms = 100 * (1 - min(cv, 0.30) / 0.30)
        
        return max(0, ms)
    
    def _calculate_market_liquidity(self, market_activity: Dict) -> float:
        """
        Calculate Market Liquidity score (0-100).
        
        ML = min(100, transaction_volume / expected_volume × 100)
        """
        if not market_activity:
            return 50.0
        
        actual_volume = market_activity.get('transaction_count', 0)
        expected_volume = market_activity.get('expected_volume', 10)
        
        if expected_volume == 0:
            return 50.0
        
        ml = min(100, (actual_volume / expected_volume) * 100)
        
        return ml
    
    def _calculate_disclosure_level(self, disclosure_data: Dict) -> float:
        """
        Calculate Disclosure Level score (0-100).
        
        DL = (disclosed_inputs / total_inputs) × 100
        """
        if not disclosure_data:
            return 50.0
        
        total_inputs = disclosure_data.get('total_inputs', 0)
        disclosed_inputs = disclosure_data.get('disclosed_inputs', 0)
        
        if total_inputs == 0:
            return 50.0
        
        dl = (disclosed_inputs / total_inputs) * 100
        
        return min(100, dl)
    
    def _interpret_vci(self, vci: float) -> str:
        """Interpret VCI score."""
        if vci >= 90:
            return "Exceptional confidence. Valuation is highly reliable with minimal uncertainty."
        elif vci >= 80:
            return "High confidence. Valuation is reliable with low uncertainty."
        elif vci >= 70:
            return "Good confidence. Valuation is reasonably reliable with moderate uncertainty."
        elif vci >= 60:
            return "Moderate confidence. Valuation has notable uncertainty and should be used with caution."
        elif vci >= 50:
            return "Low confidence. Valuation has significant uncertainty and requires additional analysis."
        else:
            return "Very low confidence. Valuation is highly uncertain and should not be relied upon without further investigation."
    
    def _get_confidence_level(self, vci: float) -> str:
        """Get confidence level category."""
        if vci >= 80:
            return "HIGH"
        elif vci >= 60:
            return "MODERATE"
        else:
            return "LOW"
    
    def _generate_recommendations(self, component_scores: Dict[str, float]) -> List[str]:
        """Generate recommendations based on component scores."""
        recommendations = []
        
        if component_scores['data_quality'] < 70:
            recommendations.append("Improve data quality by obtaining more complete and recent data.")
        
        if component_scores['comparable_strength'] < 70:
            recommendations.append("Select more similar comparables to reduce adjustment magnitude.")
        
        if component_scores['model_stability'] < 70:
            recommendations.append("Increase number of comparables or reduce dispersion in comparable selection.")
        
        if component_scores['market_liquidity'] < 70:
            recommendations.append("Consider expanding geographic search area or time period to capture more market activity.")
        
        if component_scores['disclosure_level'] < 70:
            recommendations.append("Increase transparency by disclosing more inputs and assumptions.")
        
        if not recommendations:
            recommendations.append("Valuation confidence is strong. No major improvements needed.")
        
        return recommendations
