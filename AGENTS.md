# AGENTS.md

Instructions for AI agents working with the **compatibility** Python package.

## Project Summary

**compatibility** is a zero-dependency Python library for package authors to validate runtime compatibility. It checks Python versions, OS compatibility, warns about untested versions, and prompts for updates.

**Key Facts:**
- Language: Python 3.10+
- Build system: Poetry (pyproject.toml)
- Dependencies: None (uses only Python stdlib)
- Type hints: Full PEP 484 compliance
- Test coverage: 97% minimum (enforced in CI)
- Localization: English and German messages

## Architecture

**Core module:** `compatibility/__main__.py`
- Single `Check` class handles all validation
- Must be called in package constructor, NOT in `__init__.py` (to respect user's logging config)
- Uses regex to parse version strings (format: "3.10" or "3.10.alpha")

**Key files:**
- `pyproject.toml` - Version number (single source of truth, Poetry managed)
- `compatibility/err.py` - Custom exceptions
- `tests/test_compatibility.py` - Comprehensive test suite (99% coverage target)

## Development Workflow

**Testing:**
```bash
pytest tests/                                           # Run all tests
pytest --cov=compatibility --cov-fail-under=97 tests/   # With coverage check
```

**Linting & Type Checking:**
```bash
flake8 . --count --max-complexity=10 --max-line-length=127 --statistics
mypy compatibility/
```

**Build:**
```bash
poetry install    # Install dependencies
poetry build      # Build wheel and sdist
```

## CI/CD

**Workflows:** Linux/MacOS/Windows test matrices, coverage, flake8, mypy
**Release:** Automated PyPI publish on GitHub release (main branch only)
**Python versions tested:** 3.10, 3.11, 3.12, 3.13, 3.14

## Translation Workflow

**Supported languages:** English (default), German (de)

**Files:**
- `locales/compatibility.pot` - Translation template with all translatable strings
- `locales/de/LC_MESSAGES/compatibility.po` - German translations (human-editable)
- `locales/de/LC_MESSAGES/compatibility.mo` - Compiled German translations (binary)
- `compile_translations.py` - Script to compile .po to .mo files

**Adding/updating translations:**
1. Extract strings: Update `locales/compatibility.pot` with any new `_("...")` strings from code
2. Update .po file: Edit `locales/de/LC_MESSAGES/compatibility.po` with German translations
3. Compile: Run `python compile_translations.py` to generate .mo file
4. **Important**: All German translations must be reviewed by a native speaker

**Translation notes:**
- Maintain formal "Sie" form in German
- Technical terms (e.g., "Dictionary", "Set") may remain in English within error messages
- Format placeholders (%s, %(name)s) must be preserved exactly

## Important Constraints

1. **Zero dependencies** - Do not add any external dependencies
2. **Call in constructor** - Never suggest calling `Check` in `__init__.py`
3. **Coverage minimum** - 97% coverage required, 99% target
4. **Type hints** - All code must have proper type annotations
5. **Stdlib only** - All features must use Python standard library
