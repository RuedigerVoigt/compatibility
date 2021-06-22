# Changelog compatibility Python library

## Upcoming

* New feature: the parameter `system_support` can be used to signal which operating systems groups ('Linux', 'MacOS', or 'Windows') are supported. It accepts a dictionary with three possible keys:
  * `working`: tested systems ready for production
  * `problems`: operating systems that may cause problems. Yields a `logging.warning`
  * `incompatible`: operating systems of which you now your application will fail to run on. Yields a `RuntimeError` exception.
* Tests now also run with the third beta version of Python 3.10.

## Version 0.9.0 stable (2021-03-21)

* Change development status from `beta` to `stable`.
* The parameter `release_date` now also accepts a string in the format `YYYY-MM-DD` besides a datetime object.

## Version 0.8.0 beta (2020-01-18)

* Initial public release. Chose a high version number to indicate it is almost feature complete and has a high test coverage.
