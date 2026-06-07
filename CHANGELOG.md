# Changelog compatibility Python library

## Upcoming

## Version 2.1.0 (2026-06-07)

* New:
    * Added the `on_incompatible` parameter (`'raise'` (default), `'warn'`, or `'ignore'`) to control how an incompatible Python version or OS is handled. Defaults to the previous raise-on-incompatible behaviour.
    * Added three more languages alongside the existing English and German: French (`fr`), Dutch (`nl`), and Spanish (`es`). These three are AI-translated.
    * `language_messages` now accepts `'auto'`, which selects the language from the user's environment locale and falls back to English when no matching catalog is available.
* Bugfixes:
    * A `min_version` higher than `max_tested_version` is now rejected with a clear `ParameterContradiction` instead of misreporting it as an incompatible running environment.
    * Fixed missing translations in the published distribution. The compiled `.mo` catalogs are gitignored build outputs, so Poetry excluded them from the wheel and sdist and installed users only ever saw English (gettext fell back silently). A `[tool.poetry] include` rule now packages the `.mo` files, and the release workflow fails the build if the wheel does not contain them.
* CI/CD:
    * Added an experimental Python 3.15 beta job to the Linux, MacOS, and Windows test workflows. It uses `allow-prereleases` and runs with `continue-on-error`, so it surfaces breakage early without failing CI.
    * Bumped GitHub Actions.
    * Replaced flake8 with Ruff for linting; complexity is now enforced (max-complexity 10).
    * The CI gate now requires 100% test coverage (statements and branches).
* Testing:
    * The test suite now compiles the translation catalogs automatically via `tests/conftest.py`, so `pytest` works on a fresh checkout without first running `compile_translations.py`.
* Changed:
    * Passing a `release_date` that is neither a `datetime.date` nor a string now raises the new `compatibility.err.BadDateType` (a subclass of `TypeError`) instead of `AttributeError`.
    * `nag_over_update` is now validated strictly: a missing key raises a clear `ValueError` instead of a `KeyError`, and non-integer values (e.g. floats) are rejected rather than silently truncated.
* Packaging:
    * Modernized `pyproject.toml` to PEP 621 `[project]` metadata (requires `poetry-core>=2.0.0`).
    * Dev tooling moved to a `[project.optional-dependencies]` `dev` extra; CI installs `.[dev]` so local and CI tooling match.
* Code quality:
    * Refactored the most complex functions into smaller helpers (no behaviour change).
    * Version strings are now parsed once during validation instead of being re-parsed behind `assert` guards, so version checks behave correctly under `python -O` (which strips asserts).
* Maintenance:
    * Updated the copyright year to 2026.

## Version 2.0.0 (2025-11-02)

* Supported Python versions:
    * Dropped support for old Python versions including 3.9 due to EOL of these versions.
    * Add support for Python 3.10 to 3.14.
* Quality:
  * Ensure with an automatic workflow that coverage is 97% or higher.
  * Enabled stricter mypy type checking (`disallow_untyped_defs` and `disallow_incomplete_defs`).
  * Converted all docstrings to Google format.
* Security:
  * Publish to PyPI with a [Trusted Publisher / OIDC](https://docs.pypi.org/trusted-publishers/).
* New:
  * Use package-specific logger (`logging.getLogger('compatibility')`) instead of root logger. This allows users to selectively control compatibility's log verbosity independently from their application's logging.
  * Use custom exceptions (`ParameterContradiction` and `BadDate`).
  * Improved messages
  * Translations:
    * Translations now use the `gettext` standard module instead of a custom solution. That makes it easier to add new languages.
    * All messages are now available in English and German.
    * The `language_messages` parameter now works correctly - each Check instance uses the language specified in its parameter rather than the environment variable.
* Bugfixes:
  * Fixed inverted comparison logic in `max_tested_version` check. Previously warned when running an older Python version than tested; now correctly warns when running a newer version than tested.
  * Map `Darwin` to `MacOS` for proper macOS detection (platform.system() returns 'Darwin' on macOS).
  * Fixed version regex to properly capture release levels (alpha, beta, candidate, final). Changed from lazy `??` to greedy `?` quantifier, which now correctly parses version strings like "3.10.alpha".
  * Replaced `logger.exception()` with `logger.error()` before raising intentional exceptions to avoid noisy duplicate tracebacks in logs.




## Version 1.0.1 stable (2021-08-05)

* Marked as compatible with Python 3.10 as tests with release candidate 1 run flawlessly on Linux, MacOS, and Windows.

## Version 1.0 stable (2021-06-22)

* New feature: the parameter `system_support` allows you to state the level of compatibility between your code and different Operating System groups. This is purposefully done on a very high level: valid inputs are only 'Linux', 'MacOS', and 'Windows' and not specific versions and distributions. The dictionary allows three keys with a set as value each:
    * `full`: The set of operating systems that are tested on production level.
    * `partial`: The set of systems that should work, but are not as rigorously tested as those with full support. A system running found here logs a warning.
    * `incompatible`: The set of systems of which you know they will fail to run the code properly. If an OS in this set tries to run the code, this will yield a `RuntimeError` exception.
* Tests now also run with the third beta version of the upcoming Python 3.10.
* Although the code should be completely platform independent, tests are now also run on MacOS and Windows.

## Version 0.9.0 stable (2021-03-21)

* Change development status from `beta` to `stable`.
* The parameter `release_date` now also accepts a string in the format `YYYY-MM-DD` besides a datetime object.

## Version 0.8.0 beta (2020-01-18)

* Initial public release. Chose a high version number to indicate it is almost feature complete and has a high test coverage.
