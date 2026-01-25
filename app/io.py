"""
Input/Output Module
===================

Handles reading input data and writing output results.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List


def load_subject(file_path: str = "data/subject.json") -> Dict:
    """
    Load subject property data from JSON file.
    
    Args:
        file_path: Path to subject JSON file
        
    Returns:
        Subject property dictionary
    """
    with open(file_path, 'r') as f:
        return json.load(f)


def load_comparables(file_path: str = "data/comparables.xlsx") -> List[Dict]:
    """
    Load comparable properties from Excel file.
    
    Args:
        file_path: Path to comparables Excel file
        
    Returns:
        List of comparable property dictionaries
    """
    df = pd.read_excel(file_path, engine='openpyxl')
    return df.to_dict('records')


def save_json_results(results: Dict, file_path: str = "outputs/valuation_results.json"):
    """
    Save valuation results to JSON file.
    
    Args:
        results: Results dictionary
        file_path: Output file path
    """
    # Ensure outputs directory exists
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)


def save_excel_results(results: Dict, file_path: str = "outputs/valuation_results.xlsx"):
    """
    Save valuation results to Excel file with multiple sheets.
    
    Args:
        results: Results dictionary
        file_path: Output file path
    """
    # Ensure outputs directory exists
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        # Sheet 1: Summary
        summary_data = {
            'Metric': [
                'Subject Address',
                'Property Type',
                'Size (sqft)',
                'Final Value (SAR)',
                'Price per Sqft (SAR)',
                'VCI Score',
                'Confidence Level',
                'IFRS 13 Level',
                'Valuation Date'
            ],
            'Value': [
                results['summary']['subject_address'],
                results['summary']['property_type'],
                results['summary']['size_sqft'],
                f"{results['summary']['final_value']:,.0f}",
                f"{results['summary']['price_per_sqft']:,.0f}",
                f"{results['summary']['vci_score']:.2f}",
                results['summary']['confidence_level'],
                results['summary']['hierarchy_level'],
                results['summary']['date']
            ]
        }
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name='Summary', index=False)
        
        # Sheet 2: Comparable Adjustments
        if 'adjustments' in results and results['adjustments']:
            df_adjustments = pd.DataFrame(results['adjustments'])
            df_adjustments.to_excel(writer, sheet_name='Adjustments', index=False)
        
        # Sheet 3: VCI Components
        if 'vci' in results and 'components' in results['vci']:
            vci_data = {
                'Component': list(results['vci']['components'].keys()),
                'Score': [f"{v:.2f}" for v in results['vci']['components'].values()]
            }
            df_vci = pd.DataFrame(vci_data)
            df_vci.to_excel(writer, sheet_name='VCI Components', index=False)
        
        # Sheet 4: Approach Values
        if 'weighting' in results and 'approach_values' in results['weighting']:
            approach_data = {
                'Approach': list(results['weighting']['approach_values'].keys()),
                'Value (SAR)': [f"{v:,.0f}" for v in results['weighting']['approach_values'].values()],
                'Weight': [f"{results['weighting']['weights'].get(k, 0):.1%}" 
                          for k in results['weighting']['approach_values'].keys()]
            }
            df_approach = pd.DataFrame(approach_data)
            df_approach.to_excel(writer, sheet_name='Approach Values', index=False)
        
        # Sheet 5: Uncertainty Analysis
        if 'uncertainty' in results:
            uncertainty_data = {
                'Metric': [
                    'Standard Error (SAR)',
                    'Confidence Interval Lower (SAR)',
                    'Confidence Interval Upper (SAR)',
                    'Coefficient of Variation'
                ],
                'Value': [
                    f"{results['uncertainty']['standard_error']:,.0f}",
                    f"{results['uncertainty']['confidence_interval'][0]:,.0f}",
                    f"{results['uncertainty']['confidence_interval'][1]:,.0f}",
                    f"{results['uncertainty']['coefficient_of_variation']:.2%}"
                ]
            }
            df_uncertainty = pd.DataFrame(uncertainty_data)
            df_uncertainty.to_excel(writer, sheet_name='Uncertainty', index=False)
