# Changelog compatibility Python library

## Version 1.0 stable (2021-06-22)

* New feature: the parameter `system_support` allows you to state the level of compatibility between your code and different Operating System groups. This is purposefully done on a very high level: valid inputs are only 'Linux', 'MacOS', and 'Windows' and not specific versions and distributions. The dictionary allows three keys with a set as value each:
    * `full`: The set of operating systems that are tested on production level.
    * `partial`: The set of systems that should work, but are not as rigorously tested as those with full support. A system running found here logs a warning.
    * `incompatible`: The set of systems of which you know they will fail to run the code properly. If an OS in this set tries to run the code, this will yield a `RuntimeError` exception.
* Tests now also run with the third beta version of Python 3.10.

## Version 0.9.0 stable (2021-03-21)

* Change development status from `beta` to `stable`.
* The parameter `release_date` now also accepts a string in the format `YYYY-MM-DD` besides a datetime object.

## Version 0.8.0 beta (2020-01-18)

* Initial public release. Chose a high version number to indicate it is almost feature complete and has a high test coverage.
