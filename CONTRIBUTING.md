# Contributing

Thank you for improving Valuation Core Engine. This project is valuation-domain software, so changes should favor traceability, test coverage, and small reversible steps.

## Local Development

1. Create a virtual environment.
2. Install runtime dependencies with `python -m pip install -r requirements.txt`.
3. Install the package in editable mode with `python -m pip install -e .`.
4. Run `python -m pytest` before opening a pull request.

## Change Guidelines

- Keep valuation logic changes small and covered by tests.
- Document changes to assumptions, thresholds, formulas, and standards interpretation.
- Do not commit private client data, production extracts, or non-anonymized property records.
- Treat `outputs/` as generated output unless a fixture is explicitly needed for a test.
- Prefer focused documentation and configuration improvements over broad refactors.

## Pull Request Checklist

- [ ] Tests pass locally or the reason they could not be run is documented.
- [ ] New valuation behavior includes tests.
- [ ] Public documentation matches the actual code paths.
- [ ] Generated or private files are excluded.
- [ ] Known follow-up work is captured in the PR body or maintenance audit.
