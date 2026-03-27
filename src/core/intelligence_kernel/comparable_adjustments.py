"""
Comparable Adjustments Module
==============================

Calculates quantitative adjustments to comparable properties.

Part of Valuation Intelligence Kernel (VIK)
Author: Hemmah Valuation Systems
"""

from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AdjustmentResult:
    """Result of adjustment calculation."""

    adjustments: Dict[str, float]
    adjusted_price: float
    total_adjustment_pct: float
    adjustment_details: Dict[str, Dict]


class ExcessiveAdjustmentError(Exception):
    """Raised when total adjustment exceeds threshold."""

    pass


class ComparableAdjuster:
    """
    Calculates adjustments for comparable properties.

    Implements IVS 105 comparable adjustment methodology.
    """

    def __init__(
        self,
        beta_size: float = 0.10,
        beta_bedrooms: float = 0.05,
        beta_bathrooms: float = 0.03,
        beta_age: float = 0.01,
        beta_location: float = 0.15,
        max_total_adjustment: float = 0.25,
    ):
        """
        Initialize adjuster with adjustment coefficients.

        Args:
            beta_size: Size adjustment coefficient
            beta_bedrooms: Bedroom adjustment coefficient
            beta_bathrooms: Bathroom adjustment coefficient
            beta_age: Age adjustment coefficient (per year)
            beta_location: Location adjustment coefficient
            max_total_adjustment: Maximum allowed total adjustment
        """
        self.beta_size = beta_size
        self.beta_bedrooms = beta_bedrooms
        self.beta_bathrooms = beta_bathrooms
        self.beta_age = beta_age
        self.beta_location = beta_location
        self.max_total_adjustment = max_total_adjustment

    def calculate_adjustments(
        self, subject: Dict, comparable: Dict, market_params: Optional[Dict] = None
    ) -> AdjustmentResult:
        """
        Calculate all adjustments for a comparable.

        Args:
            subject: Subject property characteristics
            comparable: Comparable property characteristics
            market_params: Market parameters (trend, appreciation, etc.)

        Returns:
            AdjustmentResult with breakdown and adjusted price

        Raises:
            ExcessiveAdjustmentError: If total adjustment > threshold
        """
        if market_params is None:
            market_params = {}

        adjustments = {}
        adjustment_details = {}

        # Size adjustment
        if "sqft" in subject and "sqft" in comparable:
            adj_size, details = self._calculate_size_adjustment(subject["sqft"], comparable["sqft"])
            adjustments["size"] = adj_size
            adjustment_details["size"] = details

        # Bedroom adjustment
        if "bedrooms" in subject and "bedrooms" in comparable:
            adj_bed, details = self._calculate_bedroom_adjustment(subject["bedrooms"], comparable["bedrooms"])
            adjustments["bedrooms"] = adj_bed
            adjustment_details["bedrooms"] = details

        # Bathroom adjustment
        if "bathrooms" in subject and "bathrooms" in comparable:
            adj_bath, details = self._calculate_bathroom_adjustment(subject["bathrooms"], comparable["bathrooms"])
            adjustments["bathrooms"] = adj_bath
            adjustment_details["bathrooms"] = details

        # Age adjustment
        if "year_built" in subject and "year_built" in comparable:
            adj_age, details = self._calculate_age_adjustment(subject["year_built"], comparable["year_built"])
            adjustments["age"] = adj_age
            adjustment_details["age"] = details

        # Location adjustment
        if "location_score" in subject and "location_score" in comparable:
            adj_loc, details = self._calculate_location_adjustment(
                subject["location_score"], comparable["location_score"]
            )
            adjustments["location"] = adj_loc
            adjustment_details["location"] = details

        # Time adjustment
        if "sale_date" in comparable:
            adj_time, details = self._calculate_time_adjustment(
                comparable["sale_date"], market_params.get("annual_appreciation", 0.03)
            )
            adjustments["time"] = adj_time
            adjustment_details["time"] = details

        # Calculate total adjustment
        total_adj = sum(adjustments.values())

        # Check if adjustment is too large
        if abs(total_adj) > self.max_total_adjustment:
            raise ExcessiveAdjustmentError(
                f"Total adjustment {total_adj:.1%} exceeds {self.max_total_adjustment:.1%} threshold"
            )

        # Calculate adjusted price
        base_price = comparable.get("price", 0)
        adjusted_price = base_price * (1 + total_adj)

        return AdjustmentResult(
            adjustments=adjustments,
            adjusted_price=adjusted_price,
            total_adjustment_pct=total_adj,
            adjustment_details=adjustment_details,
        )

    def _calculate_size_adjustment(self, subject_sqft: float, comp_sqft: float) -> tuple:
        """Calculate size adjustment."""
        delta_sqft = subject_sqft - comp_sqft
        adj = self.beta_size * (delta_sqft / comp_sqft)

        details = {
            "subject_sqft": subject_sqft,
            "comp_sqft": comp_sqft,
            "delta_sqft": delta_sqft,
            "adjustment_pct": adj,
            "formula": f"{self.beta_size} × ({delta_sqft} / {comp_sqft})",
        }

        return adj, details

    def _calculate_bedroom_adjustment(self, subject_beds: int, comp_beds: int) -> tuple:
        """Calculate bedroom adjustment."""
        delta_beds = subject_beds - comp_beds
        adj = self.beta_bedrooms * delta_beds

        details = {
            "subject_bedrooms": subject_beds,
            "comp_bedrooms": comp_beds,
            "delta_bedrooms": delta_beds,
            "adjustment_pct": adj,
            "formula": f"{self.beta_bedrooms} × {delta_beds}",
        }

        return adj, details

    def _calculate_bathroom_adjustment(self, subject_baths: float, comp_baths: float) -> tuple:
        """Calculate bathroom adjustment."""
        delta_baths = subject_baths - comp_baths
        adj = self.beta_bathrooms * delta_baths

        details = {
            "subject_bathrooms": subject_baths,
            "comp_bathrooms": comp_baths,
            "delta_bathrooms": delta_baths,
            "adjustment_pct": adj,
            "formula": f"{self.beta_bathrooms} × {delta_baths}",
        }

        return adj, details

    def _calculate_age_adjustment(self, subject_year: int, comp_year: int) -> tuple:
        """Calculate age adjustment."""
        current_year = datetime.now().year
        subject_age = current_year - subject_year
        comp_age = current_year - comp_year
        delta_age = subject_age - comp_age

        # Negative delta_age means subject is newer, so positive adjustment
        adj = -self.beta_age * delta_age

        details = {
            "subject_year_built": subject_year,
            "comp_year_built": comp_year,
            "subject_age": subject_age,
            "comp_age": comp_age,
            "delta_age": delta_age,
            "adjustment_pct": adj,
            "formula": f"-{self.beta_age} × {delta_age}",
        }

        return adj, details

    def _calculate_location_adjustment(self, subject_score: float, comp_score: float) -> tuple:
        """Calculate location adjustment."""
        delta_score = subject_score - comp_score
        adj = self.beta_location * delta_score

        details = {
            "subject_location_score": subject_score,
            "comp_location_score": comp_score,
            "delta_score": delta_score,
            "adjustment_pct": adj,
            "formula": f"{self.beta_location} × {delta_score}",
        }

        return adj, details

    def _calculate_time_adjustment(self, sale_date: str, annual_appreciation: float) -> tuple:
        """Calculate time adjustment based on market appreciation."""
        if isinstance(sale_date, str):
            sale_date = datetime.fromisoformat(sale_date.replace("Z", "+00:00"))

        current_date = datetime.now()
        months_diff = (current_date.year - sale_date.year) * 12 + (current_date.month - sale_date.month)

        # Calculate appreciation
        adj = (1 + annual_appreciation) ** (months_diff / 12) - 1

        details = {
            "sale_date": sale_date.isoformat(),
            "current_date": current_date.isoformat(),
            "months_diff": months_diff,
            "annual_appreciation": annual_appreciation,
            "adjustment_pct": adj,
            "formula": f"(1 + {annual_appreciation})^({months_diff}/12) - 1",
        }

        return adj, details

    def generate_adjustment_grid(self, subject: Dict, comparables: list, market_params: Optional[Dict] = None) -> Dict:
        """
        Generate adjustment grid for multiple comparables.

        Args:
            subject: Subject property
            comparables: List of comparable properties
            market_params: Market parameters

        Returns:
            Adjustment grid with all comparables
        """
        grid = {"subject": subject, "comparables": []}

        for comp in comparables:
            try:
                result = self.calculate_adjustments(subject, comp, market_params)

                comp_data = {
                    "comparable": comp,
                    "adjustments": result.adjustments,
                    "adjustment_details": result.adjustment_details,
                    "total_adjustment_pct": result.total_adjustment_pct,
                    "original_price": comp.get("price", 0),
                    "adjusted_price": result.adjusted_price,
                    "status": "valid",
                }

            except ExcessiveAdjustmentError as e:
                comp_data = {"comparable": comp, "status": "rejected", "reason": str(e)}

            grid["comparables"].append(comp_data)

        return grid
