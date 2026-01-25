# HVOS Production Tool

## Overview

This is the **production-ready CLI tool** for the Hemmah Valuation Operating System (HVOS). It integrates all 6 modules of the **Valuation Intelligence Kernel (VIK)** into a single, executable pipeline that processes real estate valuation data and produces professional outputs.

## What This Tool Does

The tool executes a complete, standards-compliant valuation workflow:

1. **Reads** subject property and comparable sales data
2. **Processes** data through 6 VIK modules:
   - Market Normalization
   - Comparable Adjustments (IVS 105)
   - Weighting Engine
   - Fair Value Hierarchy (IFRS 13)
   - Uncertainty Model
   - Valuation Confidence Index (VCI)
3. **Outputs** professional results in JSON and Excel formats

## Installation

### Prerequisites

```bash
pip install numpy scipy pandas openpyxl python-dateutil
```

### Repository Structure

```
valuation-core-engine/
├── src/
│   └── core/
│       └── intelligence_kernel/    # 6 VIK modules
├── app/
│   ├── cli.py                      # Main CLI
│   ├── io.py                       # I/O handlers
│   └── pipeline.py                 # Pipeline orchestrator
├── data/
│   ├── subject.json                # Subject property input
│   └── comparables.xlsx            # Comparable sales input
└── outputs/
    ├── valuation_results.json      # JSON output
    └── valuation_results.xlsx      # Excel output
```

## Usage

### Single Command Execution

```bash
python app/cli.py
```

### Expected Output

```
================================================================================
HVOS - Hemmah Valuation Operating System
Valuation Intelligence Kernel (VIK) - Production Tool
================================================================================

[1/4] Loading input data...
  ✓ Subject: 123 Main Street, Riyadh
  ✓ Comparables: 5

[2/4] Running valuation pipeline...
  ✓ All 6 VIK modules executed

[3/4] Saving JSON results...
  ✓ outputs/valuation_results.json

[4/4] Saving Excel results...
  ✓ outputs/valuation_results.xlsx

================================================================================
VALUATION SUMMARY
================================================================================
Subject: 123 Main Street, Riyadh
FINAL VALUE: 1,934,222 SAR
VCI Score: 91.09/100
================================================================================
✓ Complete!
```

## Input Data Format

### subject.json

```json
{
  "address": "123 Main Street, Riyadh",
  "sqft": 2500,
  "bedrooms": 4,
  "bathrooms": 3,
  "year_built": 2018,
  "location_score": 0.85,
  "property_type": "residential"
}
```

### comparables.xlsx

Excel file with columns:
- `id`: Comparable ID
- `address`: Property address
- `price`: Sale price (SAR)
- `sqft`: Square footage
- `bedrooms`: Number of bedrooms
- `bathrooms`: Number of bathrooms
- `year_built`: Year built
- `location_score`: Location quality (0-1)
- `sale_date`: Sale date (YYYY-MM-DD)

## Output Files

### valuation_results.json

Complete valuation results including:
- Normalization parameters
- Comparable adjustments
- Weighting analysis
- Fair value hierarchy classification
- Uncertainty quantification
- VCI score and components
- Final value summary

### valuation_results.xlsx

Multi-sheet Excel workbook with:
- **Summary**: Key valuation metrics
- **Adjustments**: Comparable adjustment details
- **VCI Components**: Confidence score breakdown
- **Approach Values**: Multi-approach reconciliation
- **Uncertainty**: Statistical analysis

## VIK Modules Used

| Module | Purpose | Standard |
|--------|---------|----------|
| `market_normalization.py` | Statistical normalization of market data | Statistical best practices |
| `comparable_adjustments.py` | Calculate property adjustments | IVS 105 |
| `weighting_engine.py` | Multi-approach reconciliation | IVS 101 |
| `fair_value_hierarchy.py` | Input classification | IFRS 13 |
| `uncertainty_model.py` | Confidence intervals | Statistical methods |
| `confidence_index.py` | VCI calculation | Proprietary |

## Valuation Confidence Index (VCI)

The VCI is a proprietary metric (0-100) that measures valuation reliability:

```
VCI = 0.30×DQ + 0.25×CS + 0.20×MS + 0.15×ML + 0.10×DL
```

Where:
- **DQ**: Data Quality
- **CS**: Comparable Strength
- **MS**: Model Stability
- **ML**: Market Liquidity
- **DL**: Disclosure Level

### VCI Interpretation

| Score | Level | Interpretation |
|-------|-------|----------------|
| 90-100 | Exceptional | Highly reliable, minimal uncertainty |
| 80-89 | High | Reliable, low uncertainty |
| 70-79 | Good | Reasonably reliable, moderate uncertainty |
| 60-69 | Moderate | Notable uncertainty, use with caution |
| < 60 | Low | Significant uncertainty, requires review |

## Customization

### Using Your Own Data

1. Replace `data/subject.json` with your subject property
2. Replace `data/comparables.xlsx` with your comparable sales
3. Run `python app/cli.py`

### Modifying Parameters

Edit `app/pipeline.py` to adjust:
- Market appreciation rates
- Data quality thresholds
- Weighting preferences
- Confidence levels

## Standards Compliance

This tool implements:
- **IVS 101**: Scope of Work
- **IVS 104**: Bases of Value
- **IVS 105**: Valuation Approaches and Methods
- **IFRS 13**: Fair Value Measurement
- **RICS Red Book**: Professional standards

## Development Status

**Status**: Production-ready MVP  
**Version**: 1.0  
**Last Updated**: January 2026

## Next Steps

For enterprise deployment, consider:
- REST API wrapper
- Database integration
- CI/CD pipeline
- Automated testing
- Docker containerization

See the main HVOS documentation for the 30-60-90 day roadmap.

## License

Proprietary - Hemmah Valuation Systems

## Author

Manus AI - Chief Systems Architect
