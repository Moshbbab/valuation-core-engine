"""
Fair Value Hierarchy Classifier Module
=======================================

Classifies valuation inputs according to IFRS 13 Fair Value Hierarchy.

Part of Valuation Intelligence Kernel (VIK)
Author: Hemmah Valuation Systems
"""

from typing import List, Dict
from dataclasses import dataclass
from datetime import datetime
from dateutil.relativedelta import relativedelta


@dataclass
class ClassificationResult:
    """Result of IFRS 13 classification."""
    hierarchy_level: int
    input_classification: Dict[str, int]
    level_1_inputs: List[str]
    level_2_inputs: List[str]
    level_3_inputs: List[str]
    disclosure_required: bool


class FairValueHierarchyClassifier:
    """
    Classifies inputs according to IFRS 13 Fair Value Hierarchy.
    
    Level 1: Quoted prices in active markets for identical assets
    Level 2: Observable inputs other than Level 1
    Level 3: Unobservable inputs
    """
    
    def __init__(
        self,
        level_2_threshold_months: int = 12,
        active_market_threshold: int = 10
    ):
        """
        Initialize classifier.
        
        Args:
            level_2_threshold_months: Max age for Level 2 comparables (months)
            active_market_threshold: Min transactions for active market
        """
        self.level_2_threshold_months = level_2_threshold_months
        self.active_market_threshold = active_market_threshold
    
    def classify(
        self,
        data_sources: List[Dict],
        assumptions: List[Dict],
        market_activity: Dict
    ) -> ClassificationResult:
        """
        Classify all inputs according to IFRS 13 hierarchy.
        
        Args:
            data_sources: All data sources used (comparables, etc.)
            assumptions: All assumptions made
            market_activity: Market activity metrics
            
        Returns:
            ClassificationResult with hierarchy level and breakdown
        """
        classifications = {}
        level_1_inputs = []
        level_2_inputs = []
        level_3_inputs = []
        
        # Classify data sources (comparables)
        for source in data_sources:
            input_id = source.get('id', f"source_{len(classifications)}")
            level = self._classify_data_source(source, market_activity)
            
            classifications[input_id] = level
            
            if level == 1:
                level_1_inputs.append(input_id)
            elif level == 2:
                level_2_inputs.append(input_id)
            else:
                level_3_inputs.append(input_id)
        
        # Classify assumptions
        for assumption in assumptions:
            input_id = assumption.get('id', f"assumption_{len(classifications)}")
            level = self._classify_assumption(assumption)
            
            classifications[input_id] = level
            
            if level == 1:
                level_1_inputs.append(input_id)
            elif level == 2:
                level_2_inputs.append(input_id)
            else:
                level_3_inputs.append(input_id)
        
        # Overall hierarchy level is the highest (least observable) level used
        hierarchy_level = max(classifications.values()) if classifications else 3
        
        # Disclosure required for Level 3
        disclosure_required = hierarchy_level == 3
        
        return ClassificationResult(
            hierarchy_level=hierarchy_level,
            input_classification=classifications,
            level_1_inputs=level_1_inputs,
            level_2_inputs=level_2_inputs,
            level_3_inputs=level_3_inputs,
            disclosure_required=disclosure_required
        )
    
    def _classify_data_source(
        self,
        source: Dict,
        market_activity: Dict
    ) -> int:
        """
        Classify a data source (comparable sale).
        
        Returns:
            1, 2, or 3 (hierarchy level)
        """
        source_type = source.get('type', 'unknown')
        
        # Level 1: Quoted prices in active markets for identical assets
        # (Rare in real estate, but could apply to REITs or liquid securities)
        if source_type == 'quoted_price':
            return 1
        
        # Level 2: Observable market data
        if source_type == 'comparable_sale':
            # Check age of comparable
            sale_date = source.get('sale_date')
            if sale_date:
                if isinstance(sale_date, str):
                    sale_date = datetime.fromisoformat(sale_date.replace('Z', '+00:00'))
                
                months_old = self._months_since(sale_date)
                
                # Recent comparables in active markets = Level 2
                if months_old <= self.level_2_threshold_months:
                    # Check market activity
                    location = source.get('location', 'unknown')
                    transactions = market_activity.get(location, {}).get('transactions', 0)
                    
                    if transactions >= self.active_market_threshold:
                        return 2
                    else:
                        # Inactive market = Level 3
                        return 3
                else:
                    # Old comparables = Level 3
                    return 3
        
        # Default to Level 3 (unobservable)
        return 3
    
    def _classify_assumption(self, assumption: Dict) -> int:
        """
        Classify an assumption.
        
        Returns:
            1, 2, or 3 (hierarchy level)
        """
        assumption_type = assumption.get('type', 'unknown')
        
        # Unobservable assumptions = Level 3
        unobservable_types = [
            'rent_growth',
            'occupancy_forecast',
            'expense_growth',
            'terminal_value',
            'development_cost'
        ]
        
        if assumption_type in unobservable_types:
            return 3
        
        # Market-derived assumptions = Level 2
        market_derived_types = [
            'discount_rate',
            'cap_rate',
            'market_rent'
        ]
        
        if assumption_type in market_derived_types:
            # Check if market-derived
            if assumption.get('market_derived', False):
                return 2
            else:
                return 3
        
        # Default to Level 3
        return 3
    
    def _months_since(self, date: datetime) -> int:
        """Calculate months since a date."""
        now = datetime.now()
        delta = relativedelta(now, date)
        return delta.years * 12 + delta.months
    
    def generate_disclosure(
        self,
        result: ClassificationResult,
        approach_values: Dict[str, float]
    ) -> Dict:
        """
        Generate IFRS 13 disclosure requirements.
        
        Args:
            result: Classification result
            approach_values: Values from different approaches
            
        Returns:
            Disclosure dictionary
        """
        disclosure = {
            'fair_value_hierarchy_level': result.hierarchy_level,
            'valuation_techniques': list(approach_values.keys()),
            'level_1_inputs': result.level_1_inputs,
            'level_2_inputs': result.level_2_inputs,
            'level_3_inputs': result.level_3_inputs,
            'disclosure_required': result.disclosure_required
        }
        
        # Additional disclosures for Level 3
        if result.hierarchy_level == 3:
            disclosure['level_3_disclosure'] = {
                'unobservable_inputs': result.level_3_inputs,
                'quantitative_information': 'See detailed assumptions',
                'sensitivity_analysis_required': True,
                'inter_relationships': 'To be documented'
            }
        
        return disclosure
