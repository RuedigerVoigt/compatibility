![Supported Python Versions](https://img.shields.io/pypi/pyversions/compatibility)
![pypi version](https://img.shields.io/pypi/v/compatibility)
![Last commit](https://img.shields.io/github/last-commit/RuedigerVoigt/compatibility)

Compatibility is a simple tool designed to be used by package authors. It does four things:
* Check whether the running Python interpreter version is supported, i.e. equal or higher than the minimum version and not in a list of incompatible versions. Raises a `RuntimeError` exception if the interpreter version is marked as incompatible.
* Log a warning if the running interpreter version is higher than the highest version used in tests.
* Log an info message with package name, version, and release date.
* Log an info message asking the user to check for updates if a defined number of days has passed since release. (For privacy reason it is not checked whether a new version is actually available.)

The prepared messages are available in English and German.

For these tasks it does not need any dependencies outside the Python standard library. The code has type hints ([PEP 484](https://www.python.org/dev/peps/pep-0484/)).

# Installation

```python
sudo pip3 install compatibility
```

# Example Usage

A basic example of code placed in the `__init__.py` file:

```python
from datetime import date


```


```python
import logging

import compatibility

```

# Parameters

* `package_name` (required): the name of your package.
* `package_version` (required): the version number of your package as a string.
* `release_date` (required): requires a `datetime` object (like `date(2021,1,1)`), *not* a list nor a string. This is to avoid confusion how the date is ordered.
* `python_version_support` (optional): requires a dictionary with the three following keys:
    * `min_version`: a string with the number of the oldest supported version (like `'3.6'`).
    * `incompatible_versions`: a list of incompatible versions
    * `max_tested_version`: the latest version of the interpreter you successfully tested your code with.
* `nag_days_after_release` (optional): wait this number of days (`int`) since the release, then start reminding users to check for an update.
* `language_messages` (optional): the language (`en` for English or `de` for German) of the messages logged by this. Defaults to English log messages.

## Version strings

For compatibility checks three elements of the version string are recognized:
* The major version
* The minor version
* The release level (either alpha, beta, candidate, or final)

If you provide all three elements (for example `'3.10.alpha'`) only this very specific version will be matched. If you provide only the first two (in this case `'3.10'`), all release levels of this version will match.
So assume your code would have issues with Python 3.5.beta and you list that exact string as an incompatible version. If you are running the script under 3.5.alpha nothing will happen. If you listed it by using the string `'3.5'` running the script with 3.5.alpha (or any other release level of 3.5) will raise the `RuntimeError` exception.

However, `min_version` and `max_tested_version` ignore the release level part.
