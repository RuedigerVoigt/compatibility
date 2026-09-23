"""
Operating system checks: system_support validation, contradictions and
the on_incompatible modes for an incompatible OS.

~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/compatibility
Copyright (c) 2021-2026 Rüdiger Voigt and contributors
Released under the Apache License 2.0
"""

from datetime import date
import logging
from unittest.mock import patch

import compatibility
import pytest

from compatibility import err


def test_check_system(caplog):
    caplog.set_level(logging.DEBUG)
    # supported platform
    with patch('platform.system') as system:
        system.return_value = 'Linux'
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            system_support={'full': {'Linux'},
                            'partial': set(),
                            'incompatible': {'MacOS', 'Windows'}}
            )
    assert 'fully supports Linux' in caplog.text

    # Test Darwin is mapped to MacOS
    caplog.clear()
    with patch('platform.system') as system:
        system.return_value = 'Darwin'
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            system_support={'full': {'MacOS'}}
            )
    assert 'fully supports MacOS' in caplog.text


def test_check_system_UNKNOWN_SUPPORT(caplog):
    caplog.set_level(logging.DEBUG)
    # platform support unknown
    with patch('platform.system') as system:
        system.return_value = 'Linux'
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            system_support={'full': {'Windows'}}
            )
    assert 'support for Linux is unknown' in caplog.text


def test_check_system_partial(caplog):
    # platform is listed under partial
    with patch('platform.system') as system:
        system.return_value = 'Linux'
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            system_support={'partial': {'Linux'}}
            )
    assert 'has only partial support' in caplog.text


def test_check_system_exceptions():
    # not a dictionary
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            system_support='Linux')
    assert 'must be a dictionary' in str(excinfo.value)
    # unknown key in dict
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            system_support={'typo': {'foo'}})
    assert 'Unknown key' in str(excinfo.value)
    # value for key is not a set
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            system_support={'full': ['Linux']})
    assert 'Use a set to hold values for full' in str(excinfo.value)
    # Unknown system
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            system_support={'full': {'foo'}})
    assert 'Invalid system' in str(excinfo.value)


def test_check_system_incompatible_systems(caplog):
    caplog.set_level(logging.ERROR)
    with patch('platform.system') as system:
        system.return_value = 'Linux'
        with pytest.raises(RuntimeError) as excinfo:
            compatibility.Check(
                package_name='test',
                package_version='1',
                release_date=date(2021, 1, 1),
                system_support={'incompatible': {'Linux'}}
                )
        assert 'is incompatible' in str(excinfo.value)
        # Verify error was logged before exception was raised
        assert 'is incompatible with Linux' in caplog.text


def test_on_incompatible_warn_os(caplog):
    # 'warn' logs a warning instead of raising for an incompatible OS
    caplog.set_level(logging.WARNING)
    with patch('platform.system') as system:
        system.return_value = 'Linux'
        check = compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            system_support={'incompatible': {'Linux'}},
            on_incompatible='warn')
    assert check  # no exception raised
    assert 'is incompatible with Linux' in caplog.text


def test_on_incompatible_ignore_os(caplog):
    # 'ignore' neither raises nor logs at warning/error level
    caplog.set_level(logging.WARNING)
    with patch('platform.system') as system:
        system.return_value = 'Linux'
        check = compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            system_support={'incompatible': {'Linux'}},
            on_incompatible='ignore')
    assert check
    assert 'incompatible' not in caplog.text


def test_check_system_CONTRADICTIONS():
    with patch('platform.system') as system:
        system.return_value = 'Windows'
        # Cannot be incompatible and have full support
        with pytest.raises(err.ParameterContradiction) as excinfo:
            compatibility.Check(
                package_name='test',
                package_version='1',
                release_date=date(2021, 1, 1),
                system_support={'full': {'Windows'},
                                'incompatible': {'Windows'}}
                )
        assert 'support AND be incompatible' in str(excinfo.value)

        # cannot be fully and partialy supported
        with pytest.raises(err.ParameterContradiction) as excinfo:
            compatibility.Check(
                package_name='test',
                package_version='1',
                release_date=date(2021, 1, 1),
                system_support={'full': {'Windows'},
                                'partial': {'Windows'}}
                )
        assert 'fully AND only partially supported' in str(excinfo.value)

        # Multiple systems with overlap - full & incompatible
        with pytest.raises(err.ParameterContradiction) as excinfo:
            compatibility.Check(
                package_name='test',
                package_version='1',
                release_date=date(2021, 1, 1),
                system_support={'full': {'Linux', 'Windows'},
                                'incompatible': {'Windows', 'MacOS'}}
                )
        assert 'support AND be incompatible' in str(excinfo.value)

        # Multiple systems with overlap - full & partial
        with pytest.raises(err.ParameterContradiction) as excinfo:
            compatibility.Check(
                package_name='test',
                package_version='1',
                release_date=date(2021, 1, 1),
                system_support={'full': {'Linux', 'MacOS'},
                                'partial': {'Windows', 'MacOS'}}
                )
        assert 'fully AND only partially supported' in str(excinfo.value)


def test_check_system_no_contradictions():
    """Test that non-overlapping system sets work correctly."""
    with patch('platform.system') as system:
        system.return_value = 'Linux'

        # No overlap: full & partial are different systems - should succeed
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            system_support={'full': {'Linux'},
                            'partial': {'Windows'}}
        )

        # No overlap: full & incompatible are different systems - should succeed
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            system_support={'full': {'Linux', 'MacOS'},
                            'incompatible': {'Windows'}}
        )

        # All three categories, no overlap - should succeed
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            system_support={'full': {'Linux'},
                            'partial': {'MacOS'},
                            'incompatible': {'Windows'}}
        )

        # Empty sets - should succeed
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            system_support={'full': set(),
                            'partial': {'Linux'},
                            'incompatible': set()}
        )
