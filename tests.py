#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Automatic Tests for the Compatibility library

To run these tests with coverage:
coverage run --source compatibility -m pytest tests.py
To generate a report afterwards.
coverage html

~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/compatibility
(c) 2021 Rüdiger Voigt
Released under the Apache License 2.0
"""

from datetime import date, timedelta
import logging
import platform
import re
import sys
from unittest.mock import patch

import compatibility
import pytest

from compatibility import err


def test_missing_or_empty_paramameters():
    "3 parameters are required, the other 3 have defaults."
    # package name missing
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='',
            package_version='1',
            release_date=date(2021, 1, 1))
    assert 'Missing package name!' in str(excinfo.value)

    # package name whitespace only
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='        ',
            package_version='1',
            release_date=date(2021, 1, 1))
    assert 'Missing package name!' in str(excinfo.value)

    # missing version
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='',
            release_date=date(2021, 1, 1))
    assert 'Missing package version!' in str(excinfo.value)

    # missing release date
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date='')


def test_languages():
    # not supported language
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            language_messages='not-a-language')
    assert 'Invalid value for language_messages!' in str(excinfo.value)

    # supported language: en
    compatibility.Check(
        package_name='test',
        package_version='1',
        release_date=date(2021, 1, 1),
        language_messages='en')

    # supported language: de
    compatibility.Check(
        package_name='test',
        package_version='1',
        release_date=date(2021, 1, 1),
        language_messages='de')


def test_release_date():
    # Neither a date object nor a string
    with pytest.raises(AttributeError):
        compatibility.Check(
            package_name='test',
            package_version='0.1',
            release_date=(2021, 1, 1))
    # valid date object
    assert compatibility.Check(
        package_name='test',
        package_version='0.1',
        release_date=date(2021, 1, 1))
    # valid string
    assert compatibility.Check(
        package_name='test',
        package_version='0.1',
        release_date='2021-01-01')
    # malformed date string
    with pytest.raises(err.BadDate):
        compatibility.Check(
            package_name='test',
            package_version='0.1',
            release_date='2021-Jan-10')
    # valid string format, but invalid date
    with pytest.raises(err.BadDate):
        compatibility.Check(
            package_name='test',
            package_version='0.1',
            release_date='2021-13-01')


def test_python_versions_regex():
    reg_ex = compatibility.Check.VERSION_REGEX
    valid_short = '3.8'
    valid_short_b = '3.10'
    valid_short_c = '10.0'
    valid_long = '3.8.final'
    invalid_short = '3.x'
    invalid_long = '3.8.x'
    assert re.fullmatch(reg_ex, valid_short)
    assert re.fullmatch(reg_ex, valid_short_b)
    assert re.fullmatch(reg_ex, valid_short_c)
    assert re.fullmatch(reg_ex, valid_long)
    assert not (re.fullmatch(reg_ex, invalid_short))
    assert not (re.fullmatch(reg_ex, invalid_long))


def test_python_versions_as_parameters():
    # python_version_support: missing key
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            python_version_support={
                'min_version': '3.7',
                'incompatible_versions': []
            })
    assert 'Parameter python_version_support incomplete!' in str(excinfo.value)

    # python_version_support: additional key
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            python_version_support={
                'min_version': '3.8',
                'incompatible_versions': [],
                'max_tested_version': '3.9',
                'additional_key': '1.2'
            })
    assert 'Parameter python_version_support: too many keys!' in str(excinfo.value)

    # python_version_support: right number of keys but contains unknown key
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            python_version_support={
                'min_version': '3.8',
                'incompatible_versions': [],
                'unknown_key': '3.9'
            })
    assert 'Parameter python_version_support contains unknown keys.' in str(excinfo.value)

    # python_version_support: wrong value for min_version
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            python_version_support={
                'min_version': 'x.y',
                'incompatible_versions': [],
                'max_tested_version': '3.9'
            })
    assert 'Value for key min_version incorrect.' in str(excinfo.value)

    # python_version_support: wrong value for max_tested_version
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            python_version_support={
                'min_version': '3.8',
                'incompatible_versions': [],
                'max_tested_version': '3.x'
            })
    assert 'Value for key max_tested_version incorrect.' in str(excinfo.value)

    # python_version_support: wrong version strings in incompatible_versions
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            python_version_support={
                'min_version': '3.6',
                'incompatible_versions': ['100.7.alpha', '100.8', 'foo'],
                'max_tested_version': '3.9'
            })
    assert 'cannot be parsed.' in str(excinfo.value)


def test_running_wrong_python():
    # Instead of mocking, create a version string
    # relative to the one running this test:
    major = sys.version_info.major
    minor = sys.version_info.minor
    releaselevel = sys.version_info.releaselevel
    running_version_short = f"{major}.{minor}"
    running_version_long = f"{major}.{minor}.{releaselevel}"
    version_minor_above = f"{major}.{minor + 1}"
    version_major_above = f"{major + 1}.{minor}"
    # running version is above max tested version
    # TO Do : check if logging is called
    # Minimal test version is 3.6, so 3.0
    compatibility.Check(
        package_name='test',
        package_version='1',
        release_date=date(2021, 1, 1),
        python_version_support={
            'min_version': '3.0',
            'incompatible_versions': [],
            'max_tested_version': '3.0'})
    # major version required is larger than version running
    with pytest.raises(RuntimeError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            python_version_support={
                'min_version': version_major_above,
                'incompatible_versions': [],
                'max_tested_version': '9.100'})
    # minor version above is required
    with pytest.raises(RuntimeError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            python_version_support={
                'min_version': version_minor_above,
                'incompatible_versions': [],
                'max_tested_version': '9.100'})
    # short form of running  version is in list of incompatible versions
    with pytest.raises(RuntimeError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            python_version_support={
                'min_version': '0.0',
                'incompatible_versions': [running_version_short],
                'max_tested_version': '9.100'})
    # long form of running  version is in list of incompatible versions
    with pytest.raises(RuntimeError):
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            python_version_support={
                'min_version': '0.0',
                'incompatible_versions': [running_version_long],
                'max_tested_version': '9.100'})


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
    assert 'Use a set to hold values' in str(excinfo.value)
    # Unknown system
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            system_support={'full': {'foo'}})
    assert 'Invalid system' in str(excinfo.value)


def test_check_system_incompatible_systems():
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


def test_check_system_CONTRADICTIONS():
    with patch('platform.system') as system:
        system.return_value = 'Windows'
        # Cannot be incompatible and have full support
        with pytest.raises(err.ParameterContradition) as excinfo:
            compatibility.Check(
                package_name='test',
                package_version='1',
                release_date=date(2021, 1, 1),
                system_support={'full': {'Windows'},
                                'incompatible': {'Windows'}}
                )
        assert 'support AND be incompatible' in str(excinfo.value)
        # cannot be fully and partialy supported
        with pytest.raises(err.ParameterContradition) as excinfo:
            compatibility.Check(
                package_name='test',
                package_version='1',
                release_date=date(2021, 1, 1),
                system_support={'full': {'Windows'},
                                'partial': {'Windows'}}
                )
        assert 'fully AND only partially supported' in str(excinfo.value)


def test_check_version_age():

# Test *temporarily* disabled because if the guard clause is there, the mypy unreachable
# code check, cannot be silenced and there is always an error.
    # value of nag_over_update is None
#    my_check = compatibility.Check(
#        package_name='test',
#        package_version='1',
#        release_date=date(2021, 1, 1),
#        nag_over_update=None)
#    my_check.check_version_age(None)

    # nag_in_hundred is 0
    compatibility.Check(
        package_name='test',
        package_version='1',
        release_date=date(2021, 1, 1),
        nag_over_update={
            'nag_days_after_release': 1,
            'nag_in_hundred': 0
        })

    # negative value
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            nag_over_update={
                'nag_days_after_release': -42,
                'nag_in_hundred': 100
            })
    assert 'nag_days_after_release must not be negative.' in str(excinfo.value)

    # non integer value
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            nag_over_update={
                'nag_days_after_release': 'foo',
                'nag_in_hundred': 100
            })
    assert 'Some key im nag_over_update has wrong type!' in str(excinfo.value)

    # Note: Directly mocking datetime will fail, because it is C-Code !
    # Solution could be partial mocking, see.
    # https://docs.python.org/3/library/unittest.mock-examples.html#partial-mocking
    # However, it is simpler to calculate the release date:
    a_week_ago = date.today() - timedelta(days=7)

    # days since release below threshold
    compatibility.Check(
        package_name='test',
        package_version='1',
        release_date=a_week_ago,
        nag_over_update={
                'nag_days_after_release': 100,
                'nag_in_hundred': 100
            })

    # days since release above threshold
    compatibility.Check(
        package_name='test',
        package_version='1',
        release_date=a_week_ago,
        nag_over_update={
                'nag_days_after_release': 3,
                'nag_in_hundred': 100
            })

    # nag_in_hundred negative
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=a_week_ago,
            nag_over_update={
                    'nag_days_after_release': 3,
                    'nag_in_hundred': -100
                })
    assert 'must be int between 0 and 100' in str(excinfo.value)

    # nag_in_hundred above 100
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=a_week_ago,
            nag_over_update={
                    'nag_days_after_release': 3,
                    'nag_in_hundred': 101
                })
    assert 'must be int between 0 and 100' in str(excinfo.value)


def test_check_version_age_logging(caplog):
    caplog.set_level(logging.INFO)
    # always nag
    compatibility.Check(
        package_name='test',
        package_version='1',
        release_date=date(2021, 1, 1),
        nag_over_update={
                'nag_days_after_release': 3,
                'nag_in_hundred': 100
            })
    assert 'There could be updates and security fixes' in caplog.text
