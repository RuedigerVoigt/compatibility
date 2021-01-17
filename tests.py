#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Automatic Tests for the Compatibility library

~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/compatibility
(c) 2021: Released under the Apache License 2.0
"""

from datetime import date, timedelta
import re
import sys

import compatibility
import pytest


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
    assert 'Missing release date!' in str(excinfo.value)


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
    # not a date object
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='0.1',
            release_date=(2021, 1, 1))
    assert 'Parameter release_date must be a date object!' in str(excinfo.value)


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
    with pytest.raises(RuntimeError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            python_version_support={
                'min_version': '0.0',
                'incompatible_versions': [running_version_long],
                'max_tested_version': '9.100'})


def test_check_version_age():
    # value is None
    compatibility.Check(
        package_name='test',
        package_version='1',
        release_date=date(2021, 1, 1),
        nag_days_after_release=None)

    # negative value
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            nag_days_after_release=-42)
    assert 'Use value None to switch off' in str(excinfo.value)

    # non integer value
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            nag_days_after_release='foo')
    assert 'must be int or None' in str(excinfo.value)

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
        nag_days_after_release=100)

    # days since release above threshold
    compatibility.Check(
        package_name='test',
        package_version='1',
        release_date=a_week_ago,
        nag_days_after_release=3)
