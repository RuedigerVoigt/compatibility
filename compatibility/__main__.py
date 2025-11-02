"""
Compatibility

A Python library that checks whether the running version of Python is
compatible and tested.
Remind the user to check for updates of the package.

~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/compatibility
Copyright (c) 2021-2025 Rüdiger Voigt and contributors
Released under the Apache License 2.0
"""

import datetime
import gettext
import logging
from logging import NullHandler
import platform
import random
import re
import sys
from typing import Optional, TypedDict, Union

from compatibility import err


import os

logger = logging.getLogger('compatibility')
logger.addHandler(NullHandler())


class PythonVersionSupport(TypedDict):
    """Type definition for python_version_support parameter."""
    min_version: str
    incompatible_versions: list[str]
    max_tested_version: str


class NagOverUpdate(TypedDict):
    """Type definition for nag_over_update parameter."""
    nag_days_after_release: int
    nag_in_hundred: int


class SystemSupport(TypedDict, total=False):
    """Type definition for system_support parameter.
    All keys are optional."""
    full: set[str]
    partial: set[str]
    incompatible: set[str]


class Check():
    """Main Class of the compatibility package: check Python version
       and time since release."""

    # Regular expression to parse a version string provided by the user
    # Optional release level (alpha, beta, candidate, final) after major.minor
    VERSION_REGEX = re.compile(
        r"(?P<major>\d+)\.(?P<minor>\d+)(\.(?P<releaselevel>\b(alpha|beta|candidate|final)\b))?")

    def __init__(self,
                 package_name: str,
                 package_version: str,
                 release_date: Union[datetime.date, str],
                 python_version_support: Optional[PythonVersionSupport] = None,
                 nag_over_update: Optional[NagOverUpdate] = None,
                 language_messages: str = 'en',
                 system_support: Optional[SystemSupport] = None):
        """Initialize compatibility checker and perform all validation checks.

        This constructor performs all compatibility checks immediately upon
        instantiation. It should be called in your package's main class
        constructor, not in __init__.py, to respect the user's logging
        configuration.

        Args:
            package_name: Name of the package using this library.
            package_version: Version string of the package (e.g., "1.2.3").
            release_date: Release date as datetime.date object or string in
                format "YYYY-MM-DD".
            python_version_support: Optional dict with keys 'min_version',
                'max_tested_version', and 'incompatible_versions' to check
                Python interpreter compatibility.
            nag_over_update: Optional dict with keys 'nag_days_after_release'
                and 'nag_in_hundred' to prompt users for updates.
            language_messages: Language for messages, either 'en' (default)
                or 'de' for German.
            system_support: Optional dict with optional keys 'full', 'partial',
                and 'incompatible', each containing a set of OS names
                ('Linux', 'MacOS', 'Windows').

        Raises:
            ValueError: If package_name or package_version is empty, if
                language_messages is invalid, or if parameters are malformed.
            RuntimeError: If Python version is incompatible or OS is
                incompatible.
            err.BadDate: If release_date is invalid or non-existent.
            err.ParameterContradiction: If system_support contains
                contradictory entries.
        """
        self.package_name = package_name.strip()
        self.package_version = package_version.strip()
        self.language_messages = language_messages.strip()
        # Create instance-local translation based on language_messages parameter
        # Must be done BEFORE __coerce_date and other methods that use self._()
        self._translation = gettext.translation(
            'compatibility',
            localedir=os.path.join(os.path.dirname(__file__), 'locales'),
            languages=[self.language_messages],
            fallback=True)
        self._ = self._translation.gettext
        self.release_date = self.__coerce_date(release_date)
        self.check_params()
        self.check_python_version(python_version_support)
        self.check_system(system_support)
        self.log_version_info()
        if nag_over_update:
            self.check_version_age(nag_over_update)

    def __coerce_date(
            self, date_to_coerce: Union[str, datetime.date]) -> datetime.date:
        """Convert a string to datetime.date and validate.

        Accepts either a datetime.date object (returned as-is) or a string
        in YYYY-MM-DD format. Validates that the date exists.

        Args:
            date_to_coerce: Either a datetime.date object or a string in
                format "YYYY-MM-DD".

        Returns:
            A datetime.date object.

        Raises:
            err.BadDate: If string is invalid format or non-existent date.
            AttributeError: If input is neither string nor datetime.date.
        """
        if isinstance(date_to_coerce, datetime.date):
            return date_to_coerce

        if isinstance(date_to_coerce, str):
            try:
                return datetime.datetime.strptime(date_to_coerce, '%Y-%m-%d').date()
            except ValueError as bad_date:
                # standard error message is not useful
                raise err.BadDate(
                    self._('Non-existing or incomplete date!')) from bad_date

        raise AttributeError(
            self._('date_to_coerce must be either string or datetime.date'))

    def check_params(self) -> None:
        """Validate that required parameters are non-empty and valid.

        Checks that package_name and package_version are not empty after
        stripping whitespace, and that language_messages is supported.

        Raises:
            ValueError: If package_name is empty, package_version is empty,
                or language_messages is not 'en' or 'de'.
        """
        # Parameters might be empty after applying .strip()
        if not self.package_name:
            raise ValueError(self._('Missing package name!'))
        if not self.package_version:
            raise ValueError(self._('Missing package version!'))
        # Is the message language supported?
        if self.language_messages not in ('en', 'de'):
            raise ValueError(self._('Invalid value for language_messages!'))

    def check_python_version(self,
                             python_version_support: Optional[PythonVersionSupport] = None
                             ) -> None:
        """Validate that the running Python version is supported.

        Checks that the Python interpreter version meets minimum requirements,
        is not in the incompatible list, and logs a warning if running on a
        version higher than the maximum tested version.

        Args:
            python_version_support: Optional dict with keys 'min_version',
                'max_tested_version', and 'incompatible_versions'. If None,
                no version checking is performed.

        Raises:
            ValueError: If python_version_support dict is malformed or
                contains invalid version strings.
            RuntimeError: If running Python version is below minimum or is
                in the incompatible versions list.
        """
        if not python_version_support:
            # Setting python_version_support is not required
            return None

        # Python version support: missing or additional keys
        if len(python_version_support.keys()) < 3:
            raise ValueError(self._('Parameter python_version_support incomplete!'))
        if len(python_version_support.keys()) > 3:
            raise ValueError(
                self._('Parameter python_version_support: too many keys!'))
        # Are there the right keys?
        expected_keys = ['incompatible_versions',
                         'max_tested_version',
                         'min_version']
        found_keys = list(python_version_support.keys())
        if sorted(found_keys) != expected_keys:
            raise ValueError(
                self._('Parameter python_version_support contains unknown keys.'))
        # Do the Python versions parse?
        # fullmatch instead of match, because with match something like 3.8.x
        # would be recognized.
        if not re.fullmatch(self.VERSION_REGEX,
                            python_version_support['min_version']):
            raise ValueError(self._('Value for key min_version is incorrect.'))
        if not re.fullmatch(self.VERSION_REGEX,
                            python_version_support['max_tested_version']):
            raise ValueError(self._('Value for key max_tested_version incorrect.'))
        for version_string in python_version_support['incompatible_versions']:
            if not re.fullmatch(self.VERSION_REGEX, version_string):
                raise ValueError(
                    self._('Some string in incompatible_versions cannot be parsed.')
                    )
        major = sys.version_info.major
        minor = sys.version_info.minor
        releaselevel = sys.version_info.releaselevel
        # construct strings to search for
        short_version = f"{major}.{minor}"
        full_version = f"{short_version}.{releaselevel}"
        # Is the running version equal or higher than the minimum required?
        match_min = re.match(
            self.VERSION_REGEX,
            python_version_support['min_version'])
        # The value was parsed before, so there is always a value for major_min
        # and minor_min:
        assert match_min is not None
        major_min = int(match_min.group('major'))
        minor_min = int(match_min.group('minor'))
        if major < major_min or (major_min == major and minor < minor_min):
            raise RuntimeError(
                self._("You use %(running)s, but need at least %(required)s to run %(package)s.")
                % {'required': f"Python {major_min}.{minor_min}",
                   'package': self.package_name,
                   'running': f"Python {full_version}"}
                   )
        # Check if the running version is in the list of incompatible versions
        incompatible = python_version_support['incompatible_versions']
        if short_version in incompatible or full_version in incompatible:
            raise RuntimeError(
                self._("Your version of Python is not compatible with this version of %(package)s. Please check for updates.")
                % {'package': self.package_name}
                )
        # Check if the running version is higher than the highest tested
        match_h = re.match(
            self.VERSION_REGEX,
            python_version_support['max_tested_version'])
        # Same as above. checked before, that there is always a value:
        assert match_h is not None
        major_h = int(match_h.group('major'))
        minor_h = int(match_h.group('minor'))
        if major > major_h or (major == major_h and minor > minor_h):
            logger.warning(
                self._("You are running Python %s, but your version of %s is only tested up to %s. Please check for updates."),
                full_version,
                self.package_name,
                python_version_support['max_tested_version']
                )
        return None

    def check_system(self,
                     system_support: Optional[SystemSupport]) -> None:
        """Validate operating system compatibility.

        Checks whether the current OS (Linux, MacOS, or Windows) is fully
        supported, partially supported, incompatible, or unknown. Logs
        appropriate messages and raises exceptions for incompatible systems.

        Args:
            system_support: Optional dict with optional keys 'full',
                'partial', and 'incompatible'. Each value must be a set
                containing OS names from {'Linux', 'MacOS', 'Windows'}.
                If None, no OS checking is performed.

        Raises:
            ValueError: If system_support is malformed or contains invalid
                keys/values.
            err.ParameterContradiction: If the same OS appears in both
                'full' and 'partial', or 'full' and 'incompatible'.
            RuntimeError: If the current OS is in the 'incompatible' set.
        """
        if not system_support:
            return None
        if not isinstance(system_support, dict):
            raise ValueError(self._('Parameter system_support must be a dictionary'))

        # Are there only allowed categories and allowed values?
        for key, systems in system_support.items():
            valid_keys = {'full', 'partial', 'incompatible'}
            valid_systems = {'Linux', 'Windows', 'MacOS'}
            if key not in valid_keys:
                raise ValueError(self._('Unknown key in dictionary system_support'))
            if not isinstance(systems, set):
                raise ValueError(self._("Use a set to hold values for %s.") % key)
            for system in systems:
                if system not in valid_systems:
                    raise ValueError(
                        self._("Invalid system in %s. Allowed: %s")
                        % (key, valid_systems))

        if 'full' in system_support and 'partial' in system_support:
            if system_support['full'] & system_support['partial']:
                raise err.ParameterContradiction(
                    self._("Contradiction: System cannot simultaneously be fully AND only partially supported.")
                      )

        if 'full' in system_support and 'incompatible' in system_support:
            if system_support['full'] & system_support['incompatible']:
                raise err.ParameterContradiction(
                    self._("Contradiction: System cannot have full support AND be incompatible!"))

        running = platform.system()
        # Map Darwin to MacOS for consistency with user-facing API
        if running == 'Darwin':
            running = 'MacOS'

        if 'full' in system_support and running in system_support['full']:
            logger.debug(
                self._("%s fully supports %s."), self.package_name, running)
            return None
        if 'partial' in system_support and running in system_support['partial']:
            logger.warning(
                self._("%s has only partial support on %s."),
                self.package_name, running)
            return None
        if 'incompatible' in system_support and running in system_support['incompatible']:
            msg = (self._("This version of %s is incompatible with %s!")
                   % (self.package_name, running))
            logger.error(msg)
            raise RuntimeError(msg)

        # the running system does not appear
        logger.info(self._("%s's support for %s is unknown!"),
                     self.package_name, running)
        return None

    def log_version_info(self) -> None:
        """Log informational message with package name, version, and release date.

        Logs at INFO level unless package_name is 'compatibility' itself
        (to avoid recursive logging in self-tests).
        """
        # avoid logging info about itself in every package using it:
        if self.package_name != 'compatibility':
            msg = (self._("You are using %(package)s %(version)s (released: %(date)s)")
                   % {'package': self.package_name,
                      'version': self.package_version,
                      'date': self.release_date})
            logger.info(msg)

    def check_version_age(self,
                          nag_over_update: NagOverUpdate) -> None:
        """Check package age and prompt user for updates if threshold exceeded.

        Calculates days since release and probabilistically logs an INFO
        message suggesting the user check for updates.

        Args:
            nag_over_update: Dict with keys 'nag_days_after_release' (int,
                minimum age in days before nagging) and 'nag_in_hundred'
                (int 0-100, percentage chance of showing nag message).

        Raises:
            ValueError: If nag_days_after_release is negative, if
                nag_in_hundred is not between 0-100, or if values have
                wrong type.
        """
        try:
            nag_days_after_release = int(nag_over_update['nag_days_after_release'])
            nag_in_hundred = int(nag_over_update['nag_in_hundred'])
        except ValueError as wrong_type:
            raise ValueError(
                self._('Some key in nag_over_update has wrong type!')) from wrong_type
        if nag_days_after_release < 0:
            raise ValueError(self._('nag_days_after_release must not be negative.'))
        if nag_in_hundred < 0 or nag_in_hundred > 100:
            raise ValueError(self._('nag_in_hundred must be int between 0 and 100.'))
        if nag_in_hundred == 0:
            return
        date_delta = datetime.date.today() - self.release_date
        days_since_release = date_delta.days
        if days_since_release >= nag_days_after_release:
            probability = nag_in_hundred / 100
            if probability == 1.0 or random.random() < probability:  # nosec
                logger.info(
                    self._("Your version of %s was released %s days ago. Please check for updates."),
                    self.package_name,
                    days_since_release
                    )
