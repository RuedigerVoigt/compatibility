#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Compatibility

A Python library that checks whether the running version is compatible and
tested. Remind the user to check for updates.

~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/compatibility
(c) 2021 Rüdiger Voigt
Released under the Apache License 2.0
"""

from datetime import date
import logging
from logging import NullHandler
import random
import re
import sys
from typing import Optional

from compatibility import messages

logging.getLogger('compatibility').addHandler(NullHandler())


class Check():

    # Regular expression to parse a version string provided by the user
    VERSION_REGEX = re.compile(
        r"(?P<major>\d+)\.(?P<minor>\d+)(\.(?P<releaselevel>\b(alpha|beta|candidate|final)\b))??")

    # Messages to log in different languages
    MSG = messages.messages

    def __init__(self,
                 package_name: str,
                 package_version: str,
                 release_date: date,
                 python_version_support: Optional[dict] = None,
                 nag_over_update: Optional[dict] = None,
                 language_messages: str = 'en'):
        self.package_name = package_name.strip()
        self.package_version = package_version.strip()
        self.release_date = release_date
        self.python_version_support = python_version_support
        self.language_messages = language_messages.strip()
        self.check_params()
        self.check_python_version()
        self.log_version_info()
        if nag_over_update:
            self.check_version_age(nag_over_update)

    def check_params(self):
        "Check parameters used to initialize this class for completeness"
        # Parameters might be empty after applying .strip()
        if not self.package_name:
            raise ValueError('Missing package name!')
        if not self.package_version:
            raise ValueError('Missing package version!')
        if not self.release_date:
            raise ValueError('Missing release date!')
        if not isinstance(self.release_date, date):
            raise ValueError('Parameter release_date must be a date object!')
        # Is the message language supported?
        if self.language_messages not in ('en', 'de'):
            raise ValueError('Invalid value for language_messages!')

    def check_python_version(self):
        """Check whether the running interpreter version is supported, i.e.
           equal or higher than the minimum version and not in the list of
           incompatible versions. Warn if the running version is higher than
           the highest version used in tests."""
        if not self.python_version_support:
            # Setting python_version_support is not required
            return

        # Python version support: missing or additional keys
        if len(self.python_version_support.keys()) < 3:
            raise ValueError('Parameter python_version_support incomplete!')
        if len(self.python_version_support.keys()) > 3:
            raise ValueError('Parameter python_version_support: too many keys!')
        expected_keys = ['incompatible_versions', 'max_tested_version',
                         'min_version']
        found_keys = list(self.python_version_support.keys())
        if sorted(found_keys) != expected_keys:
            raise ValueError('Parameter python_version_support contains ' +
                             'unknown keys.')
        # Do the Python versions parse?
        # fullmatch instead of match, because with match somethin like 3.8.x
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
        major_min = int(match_min.group('major'))
        minor_min = int(match_min.group('minor'))
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
        major_h = int(match_h.group('major'))
        minor_h = int(match_h.group('minor'))
        if major_h > major or (major == major_h and minor > minor_h):
            logging.warning(
                self.MSG['untested_interpreter'][self.language_messages],
                self.package_name)

    def log_version_info(self):
        "Log a message with package name, version, and release date."
        # avoid logging info about itself in every package using it:
        if self.package_name != 'compatibility':
            logging.info(
                self.MSG['version_info'][self.language_messages],
                self.package_name,
                self.package_version,
                self.release_date)

    def check_version_age(self,
                          nag_over_update: dict):
        """Check how many days have passed since the release of this package
           version. If the number of those days is above the defined treshold,
           nag the user to check for an update."""
        if nag_over_update is None:
            return

        try:
            nag_days_after_release = int(nag_over_update['nag_days_after_release'])
            nag_in_hundred = int(nag_over_update['nag_in_hundred'])
        except ValueError:
            raise ValueError('Some key im nag_over_update has wrong type!')
        if nag_days_after_release < 0:
            raise ValueError('nag_days_after_release must not be negative.')
        if nag_in_hundred < 0 or nag_in_hundred > 100:
            raise ValueError('nag_in_hundred must be int between 0 and 100.')
        if nag_in_hundred == 0:
            return
        date_delta = date.today() - self.release_date
        days_since_release = date_delta.days
        if (days_since_release >= nag_days_after_release):
            probability = nag_in_hundred / 100
            if probability == 1.0 or random.random() < probability:
                logging.info(
                    self.MSG['check_for_updates'][self.language_messages],
                    self.package_name,
                    days_since_release)
