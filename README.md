![Supported Python Versions](https://img.shields.io/pypi/pyversions/compatibility)
![pypi version](https://img.shields.io/pypi/v/compatibility)
![Last commit](https://img.shields.io/github/last-commit/RuedigerVoigt/compatibility)
[![Coverage](https://img.shields.io/badge/coverage-99%25-brightgreen)](https://www.ruediger-voigt.eu/coverage/compatibility/index.html)
[![Downloads](https://pepy.tech/badge/compatibility/month)](https://pepy.tech/project/compatibility)

Compatibility is a simple tool designed to be used by package authors. It does five things:
* Check whether the running Python interpreter version is supported, i.e. equal or higher than the minimum version and not in a list of incompatible versions. Raises a `RuntimeError` exception if the interpreter version is marked as incompatible.
* Log a warning if the running interpreter version is higher than the highest version used in tests.
* Log an info message with package name, version, and release date.
* Log an info message asking the user to check for updates if a defined number of days has passed since release. (For privacy reason it is not checked whether a new version is actually available.)
* Check whether the operating system group (i.e. Linux, MacOS, or Windows) is fully supported, partially supported or marked as incompatible. Partial supports logs an info message, while incompatibility yields an exception.

The prepared messages are available in English and German.

For these tasks it does not need any dependencies outside the Python standard library. The code has type hints ([PEP 484](https://www.python.org/dev/peps/pep-0484/)).

# Installation

```bash
sudo pip3 install compatibility
```

# Usage

It is important, that you **do NOT call `compatibility` in the `__init__.py` file of your package, but in the constructor (`def __init__()`) of your class instead.** If you start the check in the `__init__.py` file, then it will run once you *import* the package. This goes well *if* the user already set the level for `logging`. If that is not the case, the user will see all messages including those on the `DEBUG` level. This is not a problem if the check is done in the constructor.

As an example the relevant parts of the constructor of the [salted](https://github.com/RuedigerVoigt/salted) package:

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
            release_date=date(2021, 1, 17),
            python_version_support={
                'min_version': '3.8',
                'incompatible_versions': ['3.7'],
                'max_tested_version': '3.9'},
            nag_over_update={
                    'nag_days_after_release': 30,
                    'nag_in_hundred': 50},
            language_messages='en',
            system_support={
                'full': {'Linux', 'MacOS', 'Windows'}
            })
```
The salted package has an actual problem with 3.7 and must not be run with this version. So these settings throw a `RuntimeError` in case someone tries.
Salted in that specific version is a relatively young package that will receive frequent updates. So beginning a month after the release this will nag the user over looking for an update every second time - provided the user activated logging.

# Parameters

* `package_name` (required): the name of your package.
* `package_version` (required): the version number of your package as a string.
* `release_date` (required): requires a `datetime` object (like `date(2021,1,1)`), or a string in the exact format `YYYY-MM-DD`.
* `python_version_support` (optional): requires a dictionary with the three following keys:
    * `min_version`: a string with the number of the oldest supported version (like `'3.6'`).
    * `incompatible_versions`: a list of incompatible versions that will raise the `RuntimeError`exception if they try to run your package.
    * `max_tested_version`: the latest version of the interpreter you successfully tested your code with.
* `nag_over_update` (optional): requires a dictionary with the three following keys:
    * `nag_days_after_release`: wait this number of days (`int`) since the release before reminding users to check for an update.
    * `nag_in_hundred`: Whether to nag over a possible update is random, but this sets the probability in the form how many times (int) out of hundred starts the message is logged. Accordingly 100 means every time.
* `language_messages` (optional): the language (`en` for English or `de` for German) of the messages logged by this. Defaults to English log messages.
* `system_support` (optional): allows you to state the level of compatibility between your code and different Operating System groups. This is purposefully done on a very high level: valid inputs are only 'Linux', 'MacOS', and 'Windows' and not specific versions and distributions. The dictionary allows three keys with a set as value each:
    * `full`: The set of operating systems that are tested on production level.
    * `partial`: The set of systems that should work, but are not as rigorously tested as those with full support. A system running found here logs a warning.
    * `incompatible`: The set of systems of which you know they will fail to run the code properly. If an OS in this set tries to run the code, this will yield a `RuntimeError` exception.

## Version strings

For compatibility checks three elements of the version string are recognized:
* The major version
* The minor version
* The release level (either alpha, beta, candidate, or final)

If you provide all three elements (for example `'3.10.alpha'`) only this very specific version will be matched. If you provide only the first two (in this case `'3.10'`), all release levels of this version will match.
So assume your code would have issues with Python 3.5.beta and you list that exact string as an incompatible version. If you are running the script under 3.5.alpha nothing will happen. If you listed it by using the string `'3.5'` running the script with 3.5.alpha (or any other release level of 3.5) will raise the `RuntimeError` exception.

However, `min_version` and `max_tested_version` ignore the release level part.

# Avoid running your package with an incompatible version of Python

In the `setup.py` file of your package you can use the [python_requires](https://packaging.python.org/guides/distributing-packages-using-setuptools/#python-requires) parameter to tell `pip` about incompatible versions of the interpreter. This should block installation on incompatible systems. However, users can circumvent this by setting the flag `--python-version`. More likely is a system upgrade, that installs an incompatible version with the systems package manager.

If you define incompatible versions while initializing the `compatibility` package, you add another layer of control. Even if your user ended up with an incompatible interpreter, that will trigger a `RuntimeError` exception once the user tries to run your package.
 
