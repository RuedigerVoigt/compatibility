# AGENTS.md

Instructions for AI agents working with the **compatibility** Python package.

## Project Summary

**compatibility** is a zero-dependency Python library for package authors to validate runtime compatibility. It checks Python versions, OS compatibility, warns about untested versions, and prompts for updates.

**Key Facts:**
- Language: Python 3.10+
- Build system: Poetry (pyproject.toml)
- Dependencies: None (uses only Python stdlib)
- Type hints: Full PEP 484 compliance
- Test coverage: 100% (statements and branches), enforced in CI
- Localization: English and German messages

## Architecture

**Core module:** `compatibility/__main__.py`
- Single `Check` class handles all validation in `__init__` method
- Must be called in package constructor, NOT in `__init__.py` (to respect user's logging config)
- Uses regex to parse version strings (format: "3.10" or "3.10.alpha")
- **Instance-local translations**: Each `Check` instance creates its own `gettext` translation based on `language_messages` parameter (not module-level!)
- **Package-specific logger**: Uses `logging.getLogger('compatibility')` - never use root logger

**Key files:**
- `pyproject.toml` - Version number (single source of truth, Poetry managed)
- `compatibility/err.py` - Custom exceptions (`BadDate`, `BadDateType`, `ParameterContradiction`)
- `compatibility/__init__.py` - Package entry point (exposes `Check` class and `err` module)
- `tests/test_compatibility.py` - Comprehensive test suite (100% coverage)
- `compatibility/locales/` - Translation files (.po/.mo) packaged with distribution

## Development Workflow

**Testing:**
```bash
pytest tests/                                            # Run all tests
pytest --cov=compatibility --cov-fail-under=100 tests/   # With coverage check
```

**Linting & Type Checking:**
```bash
ruff check .          # Rules + complexity (max 10) configured in pyproject.toml
mypy compatibility/
```

**Build:**
```bash
poetry install    # Install dependencies
poetry build      # Build wheel and sdist
```

## CI/CD

**Workflows:** Linux/MacOS/Windows test matrices, coverage, ruff, mypy
**Release:** Automated PyPI publish on GitHub release (main branch only)
**Python versions tested:** 3.10, 3.11, 3.12, 3.13, 3.14 (plus an experimental, non-blocking 3.15 beta job)

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
- Translations are instance-local: `self._translation` and `self._()`

## Public API Surface

**Stable API (do not break):**
- `compatibility.Check` - Main class for validation
- `compatibility.err.BadDate` - Exception for invalid/malformed dates
- `compatibility.err.BadDateType` - Exception for a wrong-typed `release_date` (subclasses `TypeError`)
- `compatibility.err.ParameterContradiction` - Exception for conflicting parameters
- `compatibility.err.CompatibilityException` - Base exception class

**Internal (may change):**
- All private methods (prefixed with `_`)
- Module-level implementation details

## Important Constraints

1. **Zero dependencies** - Do not add any external dependencies
2. **Call in constructor** - Never suggest calling `Check` in `__init__.py`
3. **Coverage** - 100% coverage required (statements and branches), enforced in CI
4. **Type hints** - All code must have proper type annotations
5. **Stdlib only** - All features must use Python standard library
6. **Package logger** - Always use `logging.getLogger('compatibility')`, never root logger
7. **Instance translations** - Translation must be created per-instance in `__init__`, not module-level
8. **No logging at import time** - All logging must happen during class instantiation or method calls
9. **Logger formatting** - Use lazy interpolation: `logger.info("Message %s", value)` not f-strings
10. **Translation strings** - Avoid concatenating translated fragments; use single complete strings with placeholders
11. **TypedDict encouraged** - For structured dict parameters when adding new features

## Don't Do This

❌ Add any external dependencies
❌ Make translations module-level
❌ Use root logger (`logging.*`)
❌ Suggest calling `Check` in `__init__.py`
❌ Skip type hints
❌ Reduce test coverage below 100%
❌ Log at module import time
❌ Concatenate translated strings
❌ Use f-strings in logger calls

## Release Checklist

Before creating a new release:

1. **Version & Changelog**
   - [ ] Update version in `pyproject.toml` (`poetry version <newversion>`)
   - [ ] Update `CHANGELOG.md` with all changes since last release
   - [ ] Ensure version classifiers in `pyproject.toml` match supported Python versions

2. **Translations**
   - [ ] Extract new translatable strings: Update `.pot` template
   - [ ] Update `.po` files with new translations
   - [ ] Compile translations: `python compile_translations.py`

3. **Quality Checks**
   - [ ] All tests pass: `pytest tests/`
   - [ ] Coverage is 100%: `pytest --cov=compatibility --cov-fail-under=100 tests/`
   - [ ] Type checking passes: `mypy compatibility/`
   - [ ] Linting passes: `ruff check .`

4. **Build & Publish**
   - [ ] Build package: `poetry build`
   - [ ] Test wheel installs correctly
   - [ ] Create GitHub release (triggers automated PyPI publish via CI/CD)

5. **Documentation**
   - [ ] README reflects new features
   - [ ] AGENTS.md updated if architecture changed
   - [ ] TODO.md reflects completed/remaining work
