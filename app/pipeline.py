"""
Valuation Pipeline
==================

Orchestrates the complete valuation workflow using VIK modules.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from core.intelligence_kernel.market_normalization import MarketNormalizer
from core.intelligence_kernel.comparable_adjustments import ComparableAdjuster
from core.intelligence_kernel.weighting_engine import WeightingEngine
from core.intelligence_kernel.fair_value_hierarchy import FairValueHierarchyClassifier
from core.intelligence_kernel.uncertainty_model import UncertaintyModel
from core.intelligence_kernel.confidence_index import ConfidenceIndexCalculator


class ValuationPipeline:
    """
    Complete valuation pipeline using VIK.
    """
    
    def __init__(self):
        """Initialize all VIK modules."""
        self.normalizer = MarketNormalizer()
        self.adjuster = ComparableAdjuster()
        self.weighting_engine = WeightingEngine()
        self.hierarchy_classifier = FairValueHierarchyClassifier()
        self.uncertainty_model = UncertaintyModel()
        self.vci_calculator = ConfidenceIndexCalculator()
    
    def run(self, subject: Dict, comparables: List[Dict]) -> Dict:
        """
        Execute complete valuation pipeline.
        
        Args:
            subject: Subject property data
            comparables: List of comparable properties
            
        Returns:
            Complete valuation results
        """
        results = {}
        
        # Market parameters (hardcoded for simplicity)
        market_params = {
            'annual_appreciation': 0.04
        }
        
        # Data sources (simulated)
        data_sources = [
            {'id': 'source_mls_001', 'type': 'mls', 'name': 'Riyadh MLS', 'enabled': True},
            {'id': 'source_api_001', 'type': 'api', 'name': 'Property Data API', 'enabled': True}
        ]
        
        # Market activity (simulated)
        market_activity = {
            'transaction_count': 18,
            'expected_volume': 15
        }
        
        # Step 1: Market Normalization
        norm_result = self.normalizer.normalize(comparables, method='zscore')
        results['normalization'] = {
            'method': norm_result.params.method,
            'mean_psf': norm_result.params.mean,
            'std_psf': norm_result.params.std,
            'outliers': norm_result.outliers_detected
        }
        
        # Step 2: Comparable Adjustments
        adjustment_results = []
        adjusted_comparables = []
        
        for comp in norm_result.normalized_data:
            try:
                adj_result = self.adjuster.calculate_adjustments(
                    subject, comp, market_params
                )
                
                adjustment_results.append({
                    'comparable_id': comp['id'],
                    'original_price': comp['price'],
                    'adjusted_price': adj_result.adjusted_price,
                    'total_adjustment_pct': adj_result.total_adjustment_pct,
                    'adjustments': adj_result.adjustments
                })
                
                comp['adjusted_price'] = adj_result.adjusted_price
                adjusted_comparables.append(comp)
                
            except Exception as e:
                print(f"Warning: Could not adjust {comp['id']}: {str(e)}")
        
        results['adjustments'] = adjustment_results
        
        # Step 3: Calculate Market Approach Value
        adjusted_prices = [c['adjusted_price'] for c in adjusted_comparables]
        market_value = sum(adjusted_prices) / len(adjusted_prices)
        
        # Step 4: Weighting (simulated multi-approach)
        approach_values = {
            'market': market_value,
            'income': market_value * 1.02,
            'cost': market_value * 0.98
        }
        
        data_quality_scores = {
            'market': 0.95,
            'income': 0.80,
            'cost': 0.70
        }
        
        weighting_result = self.weighting_engine.calculate_weighted_value(
            approach_values,
            data_quality_scores,
            subject['property_type']
        )
        
        results['weighting'] = {
            'final_value': weighting_result.final_value,
            'weights': weighting_result.weights,
            'value_range': weighting_result.value_range,
            'approach_values': approach_values
        }
        
        # Step 5: Fair Value Hierarchy Classification
        assumptions = [
            {'id': 'market_trend', 'type': 'market_rent', 'market_derived': True},
            {'id': 'appreciation', 'type': 'rent_growth', 'market_derived': False}
        ]
        
        hierarchy_result = self.hierarchy_classifier.classify(
            data_sources,
            assumptions,
            market_activity
        )
        
        results['hierarchy'] = {
            'level': hierarchy_result.hierarchy_level,
            'level_1_count': len(hierarchy_result.level_1_inputs),
            'level_2_count': len(hierarchy_result.level_2_inputs),
            'level_3_count': len(hierarchy_result.level_3_inputs),
            'disclosure_required': hierarchy_result.disclosure_required
        }
        
        # Step 6: Uncertainty Quantification
        uncertainty_result = self.uncertainty_model.calculate_uncertainty(
            weighting_result.final_value,
            adjusted_comparables,
            confidence_level=0.95
        )
        
        results['uncertainty'] = {
            'standard_error': uncertainty_result.standard_error,
            'confidence_interval': uncertainty_result.confidence_interval,
            'coefficient_of_variation': uncertainty_result.coefficient_of_variation
        }
        
        # Step 7: Calculate VCI
        disclosure_data = {
            'total_inputs': 15,
            'disclosed_inputs': 13
        }
        
        vci_result = self.vci_calculator.calculate_vci(
            data_sources,
            adjusted_comparables,
            adjustment_results,
            market_activity,
            disclosure_data
        )
        
        results['vci'] = {
            'score': vci_result.vci_score,
            'confidence_level': vci_result.confidence_level,
            'components': vci_result.component_scores,
            'interpretation': vci_result.interpretation,
            'recommendations': vci_result.recommendations
        }
        
        # Final Summary
        results['summary'] = {
            'subject_address': subject['address'],
            'property_type': subject['property_type'],
            'size_sqft': subject['sqft'],
            'final_value': weighting_result.final_value,
            'value_range': weighting_result.value_range,
            'price_per_sqft': weighting_result.final_value / subject['sqft'],
            'vci_score': vci_result.vci_score,
            'confidence_level': vci_result.confidence_level,
            'hierarchy_level': hierarchy_result.hierarchy_level,
            'date': datetime.now().isoformat()
        }
        
        return results
