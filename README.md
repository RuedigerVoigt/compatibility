![Supported Python Versions](https://img.shields.io/pypi/pyversions/compatibility)
![pypi version](https://img.shields.io/pypi/v/compatibility)
![Last commit](https://img.shields.io/github/last-commit/RuedigerVoigt/compatibility)
[![Coverage](https://img.shields.io/badge/coverage-98%25-brightgreen)](https://www.ruediger-voigt.eu/coverage/compatibility/index.html)
[![Downloads](https://pepy.tech/badge/compatibility/month)](https://pepy.tech/project/compatibility)

# Python Compatibility Checker for Package Authors

**Version guard your Python package • Check OS compatibility • Prevent runtime errors**

Ensure your Python package runs on the right versions, warn users about untested versions, and gracefully handle incompatible environments.

Compatibility is a lightweight, zero-dependency library that helps Python package authors and library developers provide a better user experience by checking Python version compatibility, operating system compatibility (Linux, macOS, Windows), and gently reminding users to update. Uses Python's standard `gettext` for translations and follows PEP 561 (typed package). Perfect for PyPI package maintainers who want to prevent cryptic errors and provide helpful guidance to users.

## Why Use This Library?

✅ **Prevent cryptic runtime errors** - Catch incompatible Python versions before they cause problems
✅ **Zero dependencies** - Uses only Python's standard library
✅ **Fully typed** - Complete type hints (PEP 484) for better IDE support
✅ **Multilingual** - Built-in English and German messages
✅ **User-friendly warnings** - Inform users about untested Python versions
✅ **OS compatibility checks** - Validate Linux, macOS, and Windows support
✅ **Update reminders** - Gently encourage users to check for package updates
✅ **High test coverage** - 99%+ coverage for reliability

## Table of Contents

- [What It Does](#what-it-does)
- [Key Features](#key-features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Detailed Usage](#detailed-usage)
  - [⚠️ Important: Where to Call Compatibility](#️-important-where-to-call-compatibility)
  - [Complete Example](#complete-example)
- [Parameters](#parameters)
  - [Required Parameters](#required-parameters)
  - [Optional Parameters](#optional-parameters)
- [Version Strings](#version-strings)
- [Avoid Running Your Package with an Incompatible Version of Python](#avoid-running-your-package-with-an-incompatible-version-of-python)
- [Logging](#logging)
- [Exceptions](#exceptions)
- [Use Cases](#use-cases)

## What It Does

1. **Python Version Validation** - Check if the running Python interpreter meets minimum requirements and isn't in your list of incompatible versions. Raises `RuntimeError` for incompatible versions.
2. **Untested Version Warnings** - Warn users when running your package on Python versions newer than you've tested.
3. **Package Version Logging** - Log package name, version, and release date for better debugging.
4. **Privacy-Friendly Update Reminders** - Optionally remind users to check for updates after N days (without phoning home or checking if updates exist).
5. **Operating System Compatibility** - Validate whether the OS (Linux, macOS, Windows) is fully supported, partially supported, or incompatible.

All messages are available in English and German, selectable per-instance.

## Key Features

- **Zero Dependencies**: Pure Python stdlib - no external packages required
- **Type Safe**: Full type hints ([PEP 484](https://www.python.org/dev/peps/pep-0484/)) for excellent IDE integration
- **Well Tested**: 97% minimum coverage enforced; typically 98-99%
- **Python 3.10+**: Supports Python 3.10 through 3.14

## Installation

```bash
pip install compatibility
```

That's it! No other dependencies to manage.

## Quick Start

**Note:** To see compatibility's informational messages and warnings, configure logging first:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

Here's a minimal example to get started:

```python
from datetime import date
import logging
import compatibility

# Configure logging to see messages
logging.basicConfig(level=logging.INFO)

class MyPackage:
    def __init__(self):
        compatibility.Check(
            package_name='my_package',
            package_version='1.0.0',
            release_date=date(2025, 1, 1),
            python_version_support={
                'min_version': '3.10',
                'incompatible_versions': [],
                'max_tested_version': '3.14'
            }
        )
```

### Extended Example

Here's a more complete example using all optional features:

```python
from datetime import date
import logging
import compatibility

logging.basicConfig(level=logging.INFO)

class MyAdvancedPackage:
    def __init__(self):
        compatibility.Check(
            package_name='my_advanced_package',
            package_version='2.0.0',
            release_date=date(2025, 1, 15),
            python_version_support={
                'min_version': '3.10',
                'incompatible_versions': ['3.9'],
                'max_tested_version': '3.14'
            },
            nag_over_update={
                'nag_days_after_release': 90,  # Start reminding after 90 days
                'nag_in_hundred': 25            # Show reminder 25% of the time
            },
            language_messages='en',  # or 'de' for German
            system_support={
                'full': {'Linux', 'MacOS'},     # Fully tested
                'partial': {'Windows'},          # Should work, less tested
                'incompatible': set()            # No known incompatibilities
            }
        )
```

## Detailed Usage

### ⚠️ Important: Where to Call Compatibility

**Call `compatibility.Check()` in your class constructor, NOT in `__init__.py`**

```python
# ❌ DON'T DO THIS (in __init__.py)
import compatibility
compatibility.Check(...)  # Runs at import time, before user configures logging

# ✅ DO THIS (in your class __init__)
class MyClass:
    def __init__(self):
        compatibility.Check(...)  # Runs when instantiated, after logging is configured
```

**Why?** If you call it in `__init__.py`, it runs immediately on import before users can configure their logging levels. This means users might see unwanted DEBUG messages. Calling it in the class constructor lets users set up logging first.

### Complete Example

Here's a real-world example from the [salted](https://github.com/RuedigerVoigt/salted) package:

```python
# [...]
from datetime import date
import logging
# [...]

import compatibility
# [...]


class Salted:
    """Main class. Creates the other Objects, starts workers,
       collects results and starts the report of results. """

    VERSION = '0.6.1'

    def __init__(self,
                 [...]) -> None:

        compatibility.Check(
            package_name='salted',
            package_version=self.VERSION,
            release_date=date(2025, 6, 18),
            python_version_support={
                'min_version': '3.10',
                'incompatible_versions': [],
                'max_tested_version': '3.14'},
            nag_over_update={
                    'nag_days_after_release': 30,
                    'nag_in_hundred': 50},
            language_messages='en',
            system_support={
                'full': {'Linux', 'MacOS', 'Windows'}
            })
```
These settings ensure the package runs on Python 3.10 or higher, with testing confirmed through Python 3.14.
Salted in that specific version is a relatively young package that will receive frequent updates. So beginning a month after the release this will nag the user over looking for an update every second time - provided the user activated logging.

## Parameters

### Required Parameters

* `package_name`: the name of your package.
* `package_version`: the version number of your package as a string.
* `release_date`: requires a `datetime` object (like `date(2021,1,1)`), or a string in the exact format `YYYY-MM-DD`.

### Optional Parameters

* `python_version_support`: requires a dictionary with the three following keys:
    * `min_version`: a string with the number of the oldest supported version (like `'3.10'`).
    * `incompatible_versions`: a list of incompatible versions that will raise the `RuntimeError` exception if they try to run your package.
    * `max_tested_version`: the latest version of the interpreter you successfully tested your code with.
* `nag_over_update` (optional): requires a dictionary with the two following keys:
    * `nag_days_after_release`: wait this number of days (`int`) since the release before reminding users to check for an update.
    * `nag_in_hundred`: Whether to nag over a possible update is random, but this sets the probability in the form how many times (int) out of a hundred starts the message is logged. Accordingly 100 means every time.
* `language_messages` (optional): the language (`en` for English or `de` for German) of the messages logged by this. Defaults to English log messages.
* `system_support` (optional): allows you to state the level of compatibility between your code and different Operating System groups. This is purposefully done on a very high level: valid inputs are only 'Linux', 'MacOS', and 'Windows' and not specific versions and distributions. The dictionary allows three keys with a set as value each:
    * `full`: The set of operating systems that are tested on production level.
    * `partial`: The set of systems that should work, but are not as rigorously tested as those with full support. A system found running here logs a warning.
    * `incompatible`: The set of systems of which you know they will fail to run the code properly. If an OS in this set tries to run the code, this will yield a `RuntimeError` exception.

**System Support Behavior:**

| System in... | Log Level | Exception Raised? | Description |
|-------------|-----------|-------------------|-------------|
| `full` | DEBUG | No | Production-tested, fully supported |
| `partial` | WARNING | No | Should work, but less rigorously tested |
| `incompatible` | ERROR | Yes (`RuntimeError`) | Known to fail |
| Not listed | INFO | No | Support status unknown |

## Version strings

For compatibility checks three elements of the version string are recognized:
* The major version
* The minor version
* The release level (either alpha, beta, candidate, or final)

If you provide all three elements (for example `'3.10.alpha'`) only this very specific version will be matched. If you provide only the first two (in this case `'3.10'`), all release levels of this version will match.
So assume your code would have issues with Python 3.5.beta and you list that exact string as an incompatible version. If you are running the script under 3.5.alpha nothing will happen. If you listed it by using the string `'3.5'` running the script with 3.5.alpha (or any other release level of 3.5) will raise the `RuntimeError` exception.

However, `min_version` and `max_tested_version` ignore the release level part.

## Avoid running your package with an incompatible version of Python

In the `pyproject.toml` file of your package you can use the [python_requires](https://packaging.python.org/guides/distributing-packages-using-setuptools/#python-requires) parameter (or the `python` field in Poetry's `[tool.poetry.dependencies]`) to tell `pip` about incompatible versions of the interpreter. This should block installation on incompatible systems. However, users can circumvent this by setting the flag `--python-version`. More likely is a system upgrade that installs an incompatible version with the system's package manager.

If you define incompatible versions while initializing the `compatibility` package, you add another layer of control. Even if your user ended up with an incompatible interpreter, that will trigger a `RuntimeError` exception once the user tries to run your package.

## Logging

The `compatibility` package uses Python's standard logging module with a dedicated logger named `'compatibility'`. This allows you to control the verbosity of compatibility messages independently from your application's logging.

### Basic Usage

By default, compatibility messages propagate to the root logger, so they will appear if you have configured logging in your application:

```python
import logging
logging.basicConfig(level=logging.INFO)

# You will see compatibility's INFO, WARNING, and ERROR messages
```

### Fine-Grained Control

You can selectively control compatibility's log level:

```python
import logging

# Configure your application's logging
logging.basicConfig(level=logging.INFO)

# Silence compatibility warnings (only show errors)
logging.getLogger('compatibility').setLevel(logging.ERROR)

# Or make compatibility more verbose (show debug messages)
logging.getLogger('compatibility').setLevel(logging.DEBUG)
```

### Message Levels

The compatibility package logs at different levels:
* **DEBUG**: Informational messages about full platform support
* **INFO**: Package version information and update reminders
* **WARNING**: Running newer Python than tested, or partial platform support
* **ERROR**: Incompatible Python version or operating system (also raises exceptions)

## Exceptions

The `compatibility` package may raise the following exceptions:

* `RuntimeError`: Raised when the Python version or operating system is incompatible with your package.
* `ValueError`: Raised when invalid parameters are provided to the `Check` class.
* `compatibility.err.BadDate`: Raised when the `release_date` parameter contains an invalid or malformed date.
* `compatibility.err.ParameterContradiction`: Raised when conflicting parameters are provided (e.g., a system marked as both fully supported and incompatible).

## Use Cases

### When Your Package Requires Specific Python Versions
Use `min_version` to prevent your package from running on older Python versions that lack required features (like match statements, structural pattern matching, or newer typing features).

### When You Know Specific Python Versions Are Broken
Use `incompatible_versions` to block specific Python versions where your package has known issues (e.g., bugs in Python itself, or dependencies that break on certain versions).

### When Users Report Bugs on Untested Python Versions
Use `max_tested_version` to warn users when they're running your package on newer Python versions you haven't tested yet. This helps manage expectations and reduces false bug reports.

### When You Drop Support for Old Python Versions
After dropping Python 3.9 support, use this library to give users a clear error message instead of cryptic import errors or runtime failures.

### When Your Package Only Works on Certain Operating Systems
Use `system_support` to declare which operating systems (Linux, macOS, Windows) are fully supported, partially supported, or incompatible. For example, if your package uses Linux-specific system calls.

### When You Want Users to Update Old Package Versions
Use `nag_over_update` to gently remind users to check for updates after your package has been out for a while, without any privacy concerns (no network calls, no tracking).
