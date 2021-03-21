#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Compatibility

A Python library that checks whether the running version of Python is
compatible and tested.
Remind the user to check for updates of the package.

~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/compatibility
(c) 2021 Rüdiger Voigt
Released under the Apache License 2.0
"""

import datetime
import logging
from logging import NullHandler
import random
import re
import sys
from typing import Optional, Union

from compatibility import messages

logging.getLogger('compatibility').addHandler(NullHandler())


class Check():
    """Main Class of the compatibility package: check Python version
       and time since release."""
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-locals

    # Regular expression to parse a version string provided by the user
    # ?? is the non-greedy version of ?
    VERSION_REGEX = re.compile(
        r"(?P<major>\d+)\.(?P<minor>\d+)(\.(?P<releaselevel>\b(alpha|beta|candidate|final)\b))??")

    # Messages to log in different languages
    MSG = messages.messages

    def __init__(self,
                 package_name: str,
                 package_version: str,
                 release_date: Union[datetime.date, str],
                 python_version_support: Optional[dict] = None,
                 nag_over_update: Optional[dict] = None,
                 language_messages: str = 'en'):
        self.package_name = package_name.strip()
        self.package_version = package_version.strip()
        self.release_date = self.__coerce_date(release_date)
        self.python_version_support = python_version_support
        self.language_messages = language_messages.strip()
        self.check_params()
        self.check_python_version()
        self.log_version_info()
        if nag_over_update:
            self.check_version_age(nag_over_update)

    @staticmethod
    def __coerce_date(date_to_coerce: Union[str, datetime.date]) -> datetime.date:
        """Convert a string in the format YYYY-MM-DD to datetime.date.
           This doubles as a check if the date is valid.
           If the object is already of type datetime.date, just return it.
           Raise ValueError if invalid string or non-existent date.
           Raise AtributeError if neither string nor datetime.date"""
        if type(date_to_coerce) == datetime.date:  # pylint: disable=unidiomatic-typecheck
            # Mypy does not recognize the type check directly before:
            return date_to_coerce  # type: ignore

        if type(date_to_coerce) == str:  # pylint: disable=unidiomatic-typecheck
            try:
                # Mypy does not recognize the type check directly before:
                return datetime.datetime.strptime(date_to_coerce, '%Y-%m-%d').date()  # type: ignore
            except ValueError as bad_date:
                # standard error message is not useful
                raise ValueError(
                    'Non-existing or incomplete date!') from bad_date

        raise AttributeError(
            'date_to_coerce must be either string or datetime.date')

    def check_params(self) -> None:
        "Check parameters used to initialize this class for completeness"
        # Parameters might be empty after applying .strip()
        if not self.package_name:
            raise ValueError('Missing package name!')
        if not self.package_version:
            raise ValueError('Missing package version!')
        # Is the message language supported?
        if self.language_messages not in ('en', 'de'):
            raise ValueError('Invalid value for language_messages!')

    def check_python_version(self) -> None:
        """Check whether the running interpreter version is supported, i.e.
           equal or higher than the minimum version and not in the list of
           incompatible versions. Warn with logging.warn if the running
           version is higher than the highest version used in tests."""
        if not self.python_version_support:
            # Setting python_version_support is not required
            return None

        # Python version support: missing or additional keys
        if len(self.python_version_support.keys()) < 3:
            raise ValueError('Parameter python_version_support incomplete!')
        if len(self.python_version_support.keys()) > 3:
            raise ValueError('Parameter python_version_support: too many keys!')
        # Are there the right keys?
        expected_keys = ['incompatible_versions',
                         'max_tested_version',
                         'min_version']
        found_keys = list(self.python_version_support.keys())
        if sorted(found_keys) != expected_keys:
            raise ValueError(
                'Parameter python_version_support contains unknown keys.')
        # Do the Python versions parse?
        # fullmatch instead of match, because with match something like 3.8.x
        # would be recognized.
        if not re.fullmatch(self.VERSION_REGEX, self.python_version_support['min_version']):
            raise ValueError('Value for key min_version incorrect.')
        if not re.fullmatch(self.VERSION_REGEX, self.python_version_support['max_tested_version']):
            raise ValueError('Value for key max_tested_version incorrect.')
        for version_string in self.python_version_support['incompatible_versions']:
            if not re.fullmatch(self.VERSION_REGEX, version_string):
                raise ValueError(
                    'Some string in incompatible_versions cannot be parsed.')
        major = sys.version_info.major
        minor = sys.version_info.minor
        releaselevel = sys.version_info.releaselevel
        # construct strings to search for
        short_version = f"{major}.{minor}"
        full_version = f"{short_version}.{releaselevel}"
        # Is the running version equal or higher than the minimum required?
        match_min = re.match(
            self.VERSION_REGEX,
            self.python_version_support['min_version'])
        # The value was parsed before, so there is always a value for major_min
        # and minor_min. So silence mypy for the next two lines:
        major_min = int(match_min.group('major'))  # type: ignore[union-attr]
        minor_min = int(match_min.group('minor'))  # type: ignore[union-attr]
        if major < major_min or (major_min == major and minor < minor_min):
            raise RuntimeError(
                f"You need at least Python {major_min}.{minor_min} to run " +
                f"{self.package_name}, but you are using {full_version}.")
        # Check if the running version is in the list of incompatible versions
        incompatible = self.python_version_support['incompatible_versions']
        if short_version in incompatible or full_version in incompatible:
            raise RuntimeError(
                self.MSG['incompatible_version'][self.language_messages],
                self.package_name)
        # Check if the running version is higher than the highest tested
        match_h = re.match(
            self.VERSION_REGEX,
            self.python_version_support['max_tested_version'])
        # Same as above. checked before, that there is always a value.
        # Silence mypy for the next two lines:
        major_h = int(match_h.group('major'))  # type: ignore[union-attr]
        minor_h = int(match_h.group('minor'))  # type: ignore[union-attr]
        if major_h > major or (major == major_h and minor > minor_h):
            logging.warning(
                self.MSG['untested_interpreter'][self.language_messages],
                self.package_name)
        return None

    def log_version_info(self) -> None:
        "Log a message with package name, version, and release date."
        # avoid logging info about itself in every package using it:
        if self.package_name != 'compatibility':
            logging.info(
                self.MSG['version_info'][self.language_messages],
                self.package_name,
                self.package_version,
                self.release_date)

    def check_version_age(self,
                          nag_over_update: dict) -> None:
        """Check how many days have passed since the release of this package
           version. If the number of those days is above the defined treshold,
           nag the user to check for an update."""
        try:
            nag_days_after_release = int(nag_over_update['nag_days_after_release'])
            nag_in_hundred = int(nag_over_update['nag_in_hundred'])
        except ValueError as wrong_type:
            raise ValueError(
                'Some key im nag_over_update has wrong type!') from wrong_type
        if nag_days_after_release < 0:
            raise ValueError('nag_days_after_release must not be negative.')
        if nag_in_hundred < 0 or nag_in_hundred > 100:
            raise ValueError('nag_in_hundred must be int between 0 and 100.')
        if nag_in_hundred == 0:
            return
        date_delta = datetime.date.today() - self.release_date
        days_since_release = date_delta.days
        if days_since_release >= nag_days_after_release:
            probability = nag_in_hundred / 100
            if probability == 1.0 or random.random() < probability:
                logging.info(
                    self.MSG['check_for_updates'][self.language_messages],
                    self.package_name,
                    days_since_release)
