"""
Compatibility

A Python library that checks whether the running version of Python is
compatible and tested.
Remind the user to check for updates of the package.

~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/compatibility
Copyright (c) 2021-2026 Rüdiger Voigt and contributors
Released under the Apache License 2.0
"""

import datetime
import gettext
import logging
from logging import NullHandler
import os
import platform
import random
import re
import sys
from typing import Literal, Optional, TypedDict, Union

from compatibility import err

logger = logging.getLogger('compatibility')
logger.addHandler(NullHandler())

# Languages that ship a message catalog. 'en' is the source language; 'de' is
# reviewed by a native speaker; the others are AI-translated (see their .po
# headers) pending native review.
SUPPORTED_LANGUAGES = ('en', 'de', 'fr', 'nl', 'es')


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
                 system_support: Optional[SystemSupport] = None,
                 on_incompatible: Literal['raise', 'warn', 'ignore'] = 'raise'):
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
            on_incompatible: What to do when the Python version or OS is
                incompatible: 'raise' (default, raise RuntimeError), 'warn'
                (log a warning and continue), or 'ignore' (continue silently).

        Raises:
            ValueError: If package_name or package_version is empty, if
                language_messages or on_incompatible is invalid, or if
                parameters are malformed.
            RuntimeError: If Python version or OS is incompatible and
                on_incompatible is 'raise' (the default).
            err.BadDate: If release_date is invalid or non-existent.
            err.ParameterContradiction: If system_support contains
                contradictory entries.
        """
        self.package_name = package_name.strip()
        self.package_version = package_version.strip()
        self.language_messages = language_messages.strip()
        self.on_incompatible = on_incompatible
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
            err.BadDateType: If input is neither string nor datetime.date.
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

        raise err.BadDateType(
            self._('date_to_coerce must be either string or datetime.date'))

    def check_params(self) -> None:
        """Validate that required parameters are non-empty and valid.

        Checks that package_name and package_version are not empty after
        stripping whitespace, and that language_messages is supported.

        Raises:
            ValueError: If package_name is empty, package_version is empty,
                language_messages is not 'en' or 'de', or on_incompatible is
                not 'raise', 'warn', or 'ignore'.
        """
        # Parameters might be empty after applying .strip()
        if not self.package_name:
            raise ValueError(self._('Missing package name!'))
        if not self.package_version:
            raise ValueError(self._('Missing package version!'))
        # Is the message language supported?
        if self.language_messages not in SUPPORTED_LANGUAGES:
            raise ValueError(self._('Invalid value for language_messages!'))
        # Is the incompatibility handling mode valid?
        if self.on_incompatible not in ('raise', 'warn', 'ignore'):
            raise ValueError(self._('Invalid value for on_incompatible!'))

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

        min_version, max_version = self.__validate_python_version_support(
            python_version_support)

        major = sys.version_info.major
        minor = sys.version_info.minor
        releaselevel = sys.version_info.releaselevel
        # construct strings to search for
        short_version = f"{major}.{minor}"
        full_version = f"{short_version}.{releaselevel}"

        self.__enforce_version_compatibility(
            python_version_support, major, minor, short_version, full_version,
            min_version)
        self.__warn_if_untested_version(
            python_version_support, major, minor, full_version, max_version)
        return None

    def __validate_python_version_support(
            self, python_version_support: PythonVersionSupport
            ) -> tuple[tuple[int, int], tuple[int, int]]:
        """Validate the structure and version strings of python_version_support.

        Args:
            python_version_support: The dict to validate.

        Returns:
            Two (major, minor) tuples: the parsed ``min_version`` and
            ``max_tested_version``. Parsing here once removes the need to
            re-parse (and assert-guard) the strings in the comparison helpers.

        Raises:
            ValueError: If the dict has the wrong keys, or any of the version
                strings ('min_version', 'max_tested_version', or any entry of
                'incompatible_versions') cannot be parsed.
        """
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
        min_match = re.fullmatch(self.VERSION_REGEX,
                                 python_version_support['min_version'])
        if not min_match:
            raise ValueError(self._('Value for key min_version is incorrect.'))
        max_match = re.fullmatch(self.VERSION_REGEX,
                                 python_version_support['max_tested_version'])
        if not max_match:
            raise ValueError(self._('Value for key max_tested_version incorrect.'))
        for version_string in python_version_support['incompatible_versions']:
            if not re.fullmatch(self.VERSION_REGEX, version_string):
                raise ValueError(
                    self._('Some string in incompatible_versions cannot be parsed.')
                    )
        min_version = (int(min_match.group('major')), int(min_match.group('minor')))
        max_version = (int(max_match.group('major')), int(max_match.group('minor')))
        return min_version, max_version

    def __enforce_version_compatibility(
            self,
            python_version_support: PythonVersionSupport,
            major: int,
            minor: int,
            short_version: str,
            full_version: str,
            min_version: tuple[int, int]) -> None:
        """Raise if the running Python is below minimum or incompatible.

        Args:
            python_version_support: The validated version support dict.
            major: Major version of the running interpreter.
            minor: Minor version of the running interpreter.
            short_version: Running version as "major.minor".
            full_version: Running version as "major.minor.releaselevel".
            min_version: Parsed (major, minor) of the minimum supported version.

        Raises:
            RuntimeError: If the running version is below 'min_version' or
                listed in 'incompatible_versions'.
        """
        # Is the running version equal or higher than the minimum required?
        major_min, minor_min = min_version
        if major < major_min or (major_min == major and minor < minor_min):
            self.__handle_incompatible(
                self._("You use %(running)s, but need at least %(required)s to run %(package)s.")
                % {'required': f"Python {major_min}.{minor_min}",
                   'package': self.package_name,
                   'running': f"Python {full_version}"}
                   )
        # Check if the running version is in the list of incompatible versions
        incompatible = python_version_support['incompatible_versions']
        if short_version in incompatible or full_version in incompatible:
            self.__handle_incompatible(
                self._("Your version of Python is not compatible with this version of %(package)s. Please check for updates.")
                % {'package': self.package_name}
                )

    def __warn_if_untested_version(
            self,
            python_version_support: PythonVersionSupport,
            major: int,
            minor: int,
            full_version: str,
            max_version: tuple[int, int]) -> None:
        """Warn if the running Python is newer than the highest tested version.

        Args:
            python_version_support: The validated version support dict.
            major: Major version of the running interpreter.
            minor: Minor version of the running interpreter.
            full_version: Running version as "major.minor.releaselevel".
            max_version: Parsed (major, minor) of the highest tested version.
        """
        major_h, minor_h = max_version
        if major > major_h or (major == major_h and minor > minor_h):
            logger.warning(
                self._("You are running Python %s, but your version of %s is only tested up to %s. Please check for updates."),
                full_version,
                self.package_name,
                python_version_support['max_tested_version']
                )

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

        self.__validate_system_support(system_support)
        self.__check_system_contradictions(system_support)

        running = platform.system()
        # Map Darwin to MacOS for consistency with user-facing API
        if running == 'Darwin':
            running = 'MacOS'
        self.__classify_running_system(system_support, running)
        return None

    def __validate_system_support(self,
                                  system_support: SystemSupport) -> None:
        """Validate that system_support uses only allowed keys and values.

        Args:
            system_support: The system support dictionary to validate.

        Raises:
            ValueError: If a key is unknown, a value is not a set, or a set
                contains an OS name outside {'Linux', 'MacOS', 'Windows'}.
        """
        valid_keys = {'full', 'partial', 'incompatible'}
        valid_systems = {'Linux', 'Windows', 'MacOS'}
        for key, systems in system_support.items():
            if key not in valid_keys:
                raise ValueError(self._('Unknown key in dictionary system_support'))
            if not isinstance(systems, set):
                raise ValueError(self._("Use a set to hold values for %s.") % key)
            for system in systems:
                if system not in valid_systems:
                    raise ValueError(
                        self._("Invalid system in %s. Allowed: %s")
                        % (key, valid_systems))

    def __check_system_contradictions(self,
                                      system_support: SystemSupport) -> None:
        """Detect systems listed in mutually exclusive support categories.

        Args:
            system_support: The system support dictionary to check.

        Raises:
            err.ParameterContradiction: If an OS appears in both 'full' and
                'partial', or in both 'full' and 'incompatible'.
        """
        if 'full' in system_support and 'partial' in system_support:
            if system_support['full'] & system_support['partial']:
                raise err.ParameterContradiction(
                    self._("Contradiction: System cannot simultaneously be fully AND only partially supported.")
                      )

        if 'full' in system_support and 'incompatible' in system_support:
            if system_support['full'] & system_support['incompatible']:
                raise err.ParameterContradiction(
                    self._("Contradiction: System cannot have full support AND be incompatible!"))

    def __classify_running_system(self,
                                  system_support: SystemSupport,
                                  running: str) -> None:
        """Log the support status of the running OS and raise if incompatible.

        Args:
            system_support: The system support dictionary.
            running: The name of the running operating system.

        Raises:
            RuntimeError: If the running OS is in the 'incompatible' set.
        """
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
            self.__handle_incompatible(
                self._("This version of %s is incompatible with %s!")
                % (self.package_name, running))
            return None

        # the running system does not appear
        logger.info(self._("%s's support for %s is unknown!"),
                    self.package_name, running)
        return None

    def __handle_incompatible(self, msg: str) -> None:
        """Act on an incompatible Python version or OS per ``on_incompatible``.

        Args:
            msg: The fully formatted, translated message describing the
                incompatibility.

        Raises:
            RuntimeError: If ``on_incompatible`` is 'raise' (the default).
        """
        if self.on_incompatible == 'raise':
            logger.error(msg)
            raise RuntimeError(msg)
        if self.on_incompatible == 'warn':
            logger.warning(msg)
            return
        # 'ignore': stay silent at the user-visible levels, but leave a trace.
        logger.debug(msg)

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
            ValueError: If a key is missing, if a value is not an int, if
                nag_days_after_release is negative, or if nag_in_hundred is
                not between 0 and 100.
        """
        nag_days_after_release, nag_in_hundred = self.__validate_nag_over_update(
            nag_over_update)
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

    def __validate_nag_over_update(
            self, nag_over_update: NagOverUpdate) -> tuple[int, int]:
        """Validate nag_over_update and return its two integer fields.

        Args:
            nag_over_update: The dict to validate.

        Returns:
            A tuple of (nag_days_after_release, nag_in_hundred).

        Raises:
            ValueError: If a key is missing, if a value is not an int (floats
                and strings are rejected rather than coerced), if
                nag_days_after_release is negative, or if nag_in_hundred is
                not between 0 and 100.
        """
        required = {'nag_days_after_release', 'nag_in_hundred'}
        if required - nag_over_update.keys():
            raise ValueError(self._('A key in nag_over_update is missing.'))
        nag_days_after_release = nag_over_update['nag_days_after_release']
        nag_in_hundred = nag_over_update['nag_in_hundred']
        # Reject non-int values explicitly: int() would silently truncate a
        # float (3.7 -> 3) or accept a numeric string.
        if (not isinstance(nag_days_after_release, int)
                or not isinstance(nag_in_hundred, int)):
            raise ValueError(self._('Some key in nag_over_update has wrong type!'))
        if nag_days_after_release < 0:
            raise ValueError(self._('nag_days_after_release must not be negative.'))
        if nag_in_hundred < 0 or nag_in_hundred > 100:
            raise ValueError(self._('nag_in_hundred must be int between 0 and 100.'))
        return nag_days_after_release, nag_in_hundred
