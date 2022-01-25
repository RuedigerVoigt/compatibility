# Changelog compatibility Python library


## UPCOMING

* Messages were improved.
* Translations now use the `gettext` standard module instead of a custom solution. That makes it easier to add new languages.
* All messages are now available in English and German.
* Use custom exceptions (`ParameterContradition` and `BadDate`).
* Tests run with Python 3.10.


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
