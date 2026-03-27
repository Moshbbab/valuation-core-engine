"""
pytest configuration – adds src/ and the repo root to sys.path so all
test modules can import from `src/` and `app/` without per-file path
manipulation.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
