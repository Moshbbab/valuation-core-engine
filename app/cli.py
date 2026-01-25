#!/usr/bin/env python3
"""
HVOS Command Line Interface
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import io as io_module
from app.pipeline import ValuationPipeline

def main():
    print("=" * 80)
    print("HVOS - Hemmah Valuation Operating System")
    print("Valuation Intelligence Kernel (VIK) - Production Tool")
    print("=" * 80)
    print()
    
    print("[1/4] Loading input data...")
    try:
        subject = io_module.load_subject()
        comparables = io_module.load_comparables()
        print(f"  ✓ Subject: {subject['address']}")
        print(f"  ✓ Comparables: {len(comparables)}")
        print()
    except Exception as e:
        print(f"  ✗ Error: {e}")
        sys.exit(1)
    
    print("[2/4] Running valuation pipeline...")
    try:
        pipeline = ValuationPipeline()
        results = pipeline.run(subject, comparables)
        print("  ✓ All 6 VIK modules executed")
        print()
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("[3/4] Saving JSON results...")
    try:
        io_module.save_json_results(results)
        print("  ✓ outputs/valuation_results.json")
        print()
    except Exception as e:
        print(f"  ✗ Error: {e}")
        sys.exit(1)
    
    print("[4/4] Saving Excel results...")
    try:
        io_module.save_excel_results(results)
        print("  ✓ outputs/valuation_results.xlsx")
        print()
    except Exception as e:
        print(f"  ✗ Error: {e}")
        sys.exit(1)
    
    print("=" * 80)
    print("VALUATION SUMMARY")
    print("=" * 80)
    print(f"Subject: {results['summary']['subject_address']}")
    print(f"FINAL VALUE: {results['summary']['final_value']:,.0f} SAR")
    print(f"VCI Score: {results['summary']['vci_score']:.2f}/100")
    print("=" * 80)
    print("✓ Complete!")

if __name__ == '__main__':
    main()
