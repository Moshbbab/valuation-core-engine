# Valuation Core Engine

Valuation Core Engine is a Python valuation kernel for real estate workflows. The current implementation centers on the Valuation Intelligence Kernel (VIK): market normalization, comparable adjustments, approach weighting, IFRS 13 hierarchy classification, uncertainty modeling, and a Valuation Confidence Index.

The repository also includes a small CLI pipeline that reads sample subject and comparable data, runs the VIK workflow, and writes JSON or Excel valuation outputs.

## Repository Status

This project is an active MVP. The tested production path is the `app/` pipeline and the VIK modules under `src/core/intelligence_kernel/`.

Some forward-looking files describe a broader package architecture that is not fully implemented yet. See [docs/maintenance-audit.md](docs/maintenance-audit.md) before extending the package surface.

## Current Structure

```text
valuation-core-engine/
|-- app/
|   |-- cli.py          # command-line entry point
|   |-- io.py           # JSON, Excel, and output helpers
|   `-- pipeline.py     # orchestration across VIK modules
|-- data/
|   |-- subject.json
|   `-- comparables.xlsx
|-- outputs/
|   `-- valuation_results.json
|-- src/
|   `-- core/
|       |-- valuation_engine.py
|       `-- intelligence_kernel/
|-- tests/
|-- requirements.txt
|-- setup.py
`-- pytest.ini
```

## What The Pipeline Does

1. Loads subject property data and comparable sales.
2. Normalizes market observations by price per square foot.
3. Applies comparable adjustments for size, rooms, age, location, and time.
4. Reconciles market, income, and cost approach values through the weighting engine.
5. Classifies the result under the IFRS 13 fair value hierarchy.
6. Calculates uncertainty metrics and a Valuation Confidence Index.
7. Writes valuation results to JSON and Excel.

## Requirements

- Python 3.11 or 3.12
- Dependencies from `requirements.txt`

The CI workflow validates Python 3.11 and 3.12.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

On macOS or Linux, activate with:

```bash
source .venv/bin/activate
```

## Run The CLI

```bash
python app/cli.py
```

By default, the CLI reads:

- `data/subject.json`
- `data/comparables.xlsx`

And writes:

- `outputs/valuation_results.json`
- `outputs/valuation_results.xlsx`

## Run Tests

```bash
python -m pytest
```

The test suite currently focuses on the VIK modules and the end-to-end `ValuationPipeline`.

## Developer Notes

- Keep sample inputs small and anonymized.
- Treat files under `outputs/` as generated artifacts.
- Add or update tests when changing valuation logic.
- Avoid expanding `src/core/valuation_engine.py` until its missing dependency modules are either implemented or the public package design is simplified.

## Maintenance

See [CONTRIBUTING.md](CONTRIBUTING.md) and [docs/maintenance-audit.md](docs/maintenance-audit.md) for the current maintenance inventory, known technical debt, and safe next steps.
