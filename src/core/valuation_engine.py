"""
Valuation Core Engine
=====================

Main orchestrator for real estate valuation implementing IVS/IFRS 13 standards.

This module provides the central ValuationEngine class that coordinates all
valuation workflows, from data cleaning to final value determination.

Author: Hemmah Valuation Systems
License: MIT
"""

from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import logging

from .ifrs13_hierarchy import IFRS13Classifier
from .ivs_compliance import IVSComplianceChecker
from ..market.data_cleaner import MarketDataCleaner
from ..market.data_validator import DataValidator
from ..comparable.selection_engine import ComparableSelector
from ..models.market_approach import MarketApproach
from ..models.income_approach import IncomeApproach
from ..models.cost_approach import CostApproach
from ..analysis.sensitivity import SensitivityAnalyzer
from ..utils.error_handling import ValuationError, DataQualityError
from ..utils.logging_config import setup_logging


@dataclass
class ValuationResult:
    """
    Comprehensive valuation result with all supporting data.
    
    Attributes:
        value: Final estimated property value
        value_range: Tuple of (low, high) confidence interval
        ifrs_level: IFRS 13 fair value hierarchy level (1, 2, or 3)
        approaches_used: List of valuation approaches applied
        comparables: Selected comparable properties
        adjustments: Summary of adjustments made
        compliance_status: IVS compliance check results
        confidence_score: Statistical confidence (0-1)
        valuation_date: Date of valuation
        assumptions: Key assumptions made
        limitations: Limitations and caveats
        metadata: Additional metadata
    """
    value: float
    value_range: tuple[float, float]
    ifrs_level: int
    approaches_used: List[str]
    comparables: List[Dict]
    adjustments: Dict
    compliance_status: Dict
    confidence_score: float
    valuation_date: datetime
    assumptions: List[str]
    limitations: List[str]
    metadata: Dict


class ValuationEngine:
    """
    Core valuation engine implementing IVS/IFRS 13 standards.
    
    This class orchestrates the entire valuation workflow, ensuring
    compliance with international standards and maintaining audit trails.
    
    Example:
        >>> engine = ValuationEngine(standards=['IVS', 'IFRS13'])
        >>> result = engine.value(subject_property, market_data)
        >>> print(f"Value: ${result.value:,.2f}")
    """
    
    def __init__(
        self,
        standards: List[str] = ['IVS', 'IFRS13'],
        compliance_level: str = 'institutional',
        log_level: str = 'INFO'
    ):
        """
        Initialize the valuation engine.
        
        Args:
            standards: List of standards to comply with (IVS, IFRS13, RICS)
            compliance_level: Compliance strictness (basic, professional, institutional)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.standards = standards
        self.compliance_level = compliance_level
        self.logger = setup_logging(__name__, log_level)
        
        # Initialize components
        self.data_cleaner = MarketDataCleaner()
        self.data_validator = DataValidator()
        self.comparable_selector = ComparableSelector()
        self.ifrs_classifier = IFRS13Classifier()
        self.compliance_checker = IVSComplianceChecker()
        
        # Initialize valuation models
        self.market_approach = MarketApproach()
        self.income_approach = IncomeApproach()
        self.cost_approach = CostApproach()
        
        self.logger.info(f"ValuationEngine initialized with standards: {standards}")
    
    def load_market_data(self, source: Union[str, Dict]) -> Dict:
        """
        Load market data from various sources.
        
        Args:
            source: File path, URL, or dictionary of market data
            
        Returns:
            Loaded market data dictionary
            
        Raises:
            DataQualityError: If data cannot be loaded or is invalid
        """
        self.logger.info(f"Loading market data from: {source}")
        
        # Implementation would handle various data sources
        # For now, return placeholder
        return {
            'sales': [],
            'listings': [],
            'metadata': {
                'source': source,
                'loaded_at': datetime.now()
            }
        }
    
    def clean_market_data(self, raw_data: Dict) -> Dict:
        """
        Clean and normalize market data.
        
        Args:
            raw_data: Raw market data dictionary
            
        Returns:
            Cleaned and normalized data
            
        Raises:
            DataQualityError: If data quality is insufficient
        """
        self.logger.info("Cleaning market data")
        
        # Clean data
        cleaned = self.data_cleaner.clean(raw_data)
        
        # Validate quality
        validation_result = self.data_validator.validate(cleaned)
        
        if not validation_result['is_valid']:
            raise DataQualityError(
                f"Data quality insufficient: {validation_result['errors']}"
            )
        
        self.logger.info(f"Data cleaning complete. Records: {len(cleaned['sales'])}")
        return cleaned
    
    def select_comparables(
        self,
        subject_property: Dict,
        market_data: Dict,
        max_comparables: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict]:
        """
        Select comparable properties using intelligent matching.
        
        Args:
            subject_property: Subject property characteristics
            market_data: Cleaned market data
            max_comparables: Maximum number of comparables to select
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of selected comparable properties with similarity scores
        """
        self.logger.info(f"Selecting comparables for subject property")
        
        comparables = self.comparable_selector.select(
            subject=subject_property,
            candidates=market_data['sales'],
            max_count=max_comparables,
            threshold=similarity_threshold
        )
        
        self.logger.info(f"Selected {len(comparables)} comparables")
        return comparables
    
    def value(
        self,
        subject: Dict,
        comparables: Optional[List[Dict]] = None,
        market_data: Optional[Dict] = None,
        approaches: List[str] = ['market', 'income', 'cost']
    ) -> ValuationResult:
        """
        Perform comprehensive property valuation.
        
        Args:
            subject: Subject property characteristics
            comparables: Pre-selected comparables (optional)
            market_data: Market data for analysis (optional)
            approaches: Valuation approaches to use
            
        Returns:
            Comprehensive ValuationResult object
            
        Raises:
            ValuationError: If valuation cannot be completed
        """
        self.logger.info(f"Starting valuation for property: {subject.get('id', 'unknown')}")
        
        # If comparables not provided, select them
        if comparables is None and market_data is not None:
            comparables = self.select_comparables(subject, market_data)
        
        # Apply valuation approaches
        approach_results = {}
        
        if 'market' in approaches and comparables:
            approach_results['market'] = self.market_approach.value(
                subject, comparables
            )
            self.logger.info(f"Market approach value: ${approach_results['market']:,.2f}")
        
        if 'income' in approaches and subject.get('income_data'):
            approach_results['income'] = self.income_approach.value(
                subject, subject['income_data']
            )
            self.logger.info(f"Income approach value: ${approach_results['income']:,.2f}")
        
        if 'cost' in approaches:
            approach_results['cost'] = self.cost_approach.value(subject)
            self.logger.info(f"Cost approach value: ${approach_results['cost']:,.2f}")
        
        # Reconcile values
        final_value = self._reconcile_values(approach_results)
        value_range = self._calculate_confidence_interval(approach_results)
        
        # Classify IFRS 13 level
        ifrs_level = self.ifrs_classifier.classify(
            approaches=list(approach_results.keys()),
            data_quality=self._assess_data_quality(comparables, market_data)
        )
        
        # Check IVS compliance
        compliance_status = self.compliance_checker.check(
            valuation_data={
                'subject': subject,
                'approaches': approach_results,
                'comparables': comparables
            }
        )
        
        # Build result
        result = ValuationResult(
            value=final_value,
            value_range=value_range,
            ifrs_level=ifrs_level,
            approaches_used=list(approach_results.keys()),
            comparables=comparables or [],
            adjustments=self._summarize_adjustments(comparables),
            compliance_status=compliance_status,
            confidence_score=self._calculate_confidence(approach_results),
            valuation_date=datetime.now(),
            assumptions=self._list_assumptions(subject, approaches),
            limitations=self._list_limitations(subject, approaches),
            metadata={
                'engine_version': '1.0.0',
                'standards': self.standards,
                'compliance_level': self.compliance_level
            }
        )
        
        self.logger.info(f"Valuation complete. Final value: ${final_value:,.2f}")
        return result
    
    def _reconcile_values(self, approach_results: Dict[str, float]) -> float:
        """Reconcile values from multiple approaches."""
        if not approach_results:
            raise ValuationError("No valuation approaches produced results")
        
        # Simple weighted average (can be made more sophisticated)
        weights = {
            'market': 0.5,
            'income': 0.3,
            'cost': 0.2
        }
        
        total_weight = sum(weights.get(k, 1.0) for k in approach_results.keys())
        weighted_sum = sum(
            v * weights.get(k, 1.0) 
            for k, v in approach_results.items()
        )
        
        return weighted_sum / total_weight
    
    def _calculate_confidence_interval(
        self, 
        approach_results: Dict[str, float]
    ) -> tuple[float, float]:
        """Calculate confidence interval for valuation."""
        values = list(approach_results.values())
        mean = sum(values) / len(values)
        
        # Simple range calculation (can be made more sophisticated)
        low = mean * 0.9
        high = mean * 1.1
        
        return (low, high)
    
    def _assess_data_quality(
        self, 
        comparables: Optional[List[Dict]], 
        market_data: Optional[Dict]
    ) -> str:
        """Assess overall data quality."""
        if comparables and len(comparables) >= 5:
            return 'high'
        elif comparables and len(comparables) >= 3:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_confidence(self, approach_results: Dict[str, float]) -> float:
        """Calculate overall confidence score."""
        # More approaches = higher confidence
        approach_count = len(approach_results)
        base_confidence = min(approach_count / 3.0, 1.0)
        
        # Consistency between approaches increases confidence
        if approach_count > 1:
            values = list(approach_results.values())
            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            cv = (variance ** 0.5) / mean if mean > 0 else 1.0
            
            consistency_factor = max(0, 1 - cv)
            return (base_confidence + consistency_factor) / 2
        
        return base_confidence
    
    def _summarize_adjustments(self, comparables: Optional[List[Dict]]) -> Dict:
        """Summarize adjustments made to comparables."""
        if not comparables:
            return {}
        
        return {
            'total_comparables': len(comparables),
            'adjustment_types': ['location', 'size', 'condition', 'age'],
            'average_adjustment': 0.0  # Placeholder
        }
    
    def _list_assumptions(self, subject: Dict, approaches: List[str]) -> List[str]:
        """List key assumptions made in valuation."""
        assumptions = [
            "Market conditions remain stable",
            "Property information is accurate and complete",
            "No hidden defects or environmental issues"
        ]
        
        if 'income' in approaches:
            assumptions.append("Income and expense projections are reasonable")
        
        return assumptions
    
    def _list_limitations(self, subject: Dict, approaches: List[str]) -> List[str]:
        """List limitations and caveats."""
        limitations = [
            "Valuation is as of the specified date only",
            "External inspection only (if applicable)",
            "Subject to verification of property information"
        ]
        
        return limitations
