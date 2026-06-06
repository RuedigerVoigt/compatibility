"""Pytest configuration for the compatibility test suite.

Ensures the binary translation catalogs (.mo) are compiled before any test
runs. The .mo files are gitignored build outputs of compile_translations.py,
so a fresh clone has none. Without this, tests that assert German messages
would fail because gettext silently falls back to English.

Compiling here makes the test suite self-contained: `pytest` works on a fresh
checkout without a manual `python compile_translations.py` step.
"""
from pathlib import Path
import sys

# Make the repo root importable so we can reuse the existing compiler.
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from compile_translations import compile_po_to_mo  # noqa: E402


def pytest_configure(config):
    """Compile every .po catalog to .mo before the test session starts."""
    locales = _REPO_ROOT / "compatibility" / "locales"
    for po_file in locales.rglob("*.po"):
        mo_file = po_file.with_suffix(".mo")
        compile_po_to_mo(str(po_file), str(mo_file))
