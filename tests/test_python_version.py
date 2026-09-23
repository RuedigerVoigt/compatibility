"""
Python version checks: version string parsing, python_version_support
validation, incompatible and untested versions.

~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/compatibility
Copyright (c) 2021-2026 Rüdiger Voigt and contributors
Released under the Apache License 2.0
"""

from datetime import date
import logging
import re
import sys
from unittest.mock import patch

import compatibility
import pytest

from compatibility import err


# Version strings built relative to the running interpreter, so the version
# tests stay correct on whatever Python actually runs them.
_MAJOR = sys.version_info.major
_MINOR = sys.version_info.minor
_RELEASELEVEL = sys.version_info.releaselevel
_RUNNING_SHORT = f"{_MAJOR}.{_MINOR}"
_RUNNING_LONG = f"{_MAJOR}.{_MINOR}.{_RELEASELEVEL}"
_MINOR_ABOVE = f"{_MAJOR}.{_MINOR + 1}"
_MAJOR_ABOVE = f"{_MAJOR + 1}.{_MINOR}"


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

    # Test release level capture groups
    match_short = re.fullmatch(reg_ex, '3.10')
    assert match_short.group('major') == '3'
    assert match_short.group('minor') == '10'
    assert match_short.group('releaselevel') is None

    match_alpha = re.fullmatch(reg_ex, '3.9.alpha')
    assert match_alpha.group('major') == '3'
    assert match_alpha.group('minor') == '9'
    assert match_alpha.group('releaselevel') == 'alpha'

    match_beta = re.fullmatch(reg_ex, '3.10.beta')
    assert match_beta.group('major') == '3'
    assert match_beta.group('minor') == '10'
    assert match_beta.group('releaselevel') == 'beta'

    match_candidate = re.fullmatch(reg_ex, '3.11.candidate')
    assert match_candidate.group('major') == '3'
    assert match_candidate.group('minor') == '11'
    assert match_candidate.group('releaselevel') == 'candidate'

    match_final = re.fullmatch(reg_ex, '3.12.final')
    assert match_final.group('major') == '3'
    assert match_final.group('minor') == '12'
    assert match_final.group('releaselevel') == 'final'


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
    assert 'Value for key min_version is incorrect.' in str(excinfo.value)

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


def test_min_version_higher_than_max_tested():
    # min_version above max_tested_version is a contradictory configuration and
    # must be reported as such (not blamed on the running environment), even
    # with on_incompatible='ignore'.
    with pytest.raises(err.ParameterContradiction) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            python_version_support={
                'min_version': '3.17',
                'incompatible_versions': [],
                'max_tested_version': '3.14'},
            on_incompatible='ignore')
    assert 'higher than max_tested_version' in str(excinfo.value)


def test_python_version_support_not_dict():
    # A non-dict python_version_support gets a clear ValueError, not a raw
    # AttributeError from calling .keys() on the wrong type.
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            python_version_support=['3.10'])
    assert 'python_version_support must be a dictionary' in str(excinfo.value)


@pytest.mark.parametrize("incompatible", ['3.9', ''],
                         ids=['bare-string', 'empty-string'])
def test_incompatible_versions_must_be_a_list(incompatible):
    # A bare string where a list is expected is rejected with a clear message,
    # instead of iterating characters (misleading "cannot be parsed") or, for
    # an empty string, passing silently.
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            python_version_support={
                'min_version': '3.10',
                'incompatible_versions': incompatible,
                'max_tested_version': '3.14'})
    assert 'incompatible_versions must be a list' in str(excinfo.value)


@pytest.mark.parametrize("support, fragment", [
    pytest.param(
        {'min_version': _MAJOR_ABOVE, 'incompatible_versions': [],
         'max_tested_version': '9.100'},
        'need at least', id='major-below-min'),
    pytest.param(
        {'min_version': _MINOR_ABOVE, 'incompatible_versions': [],
         'max_tested_version': '9.100'},
        'need at least', id='minor-below-min'),
    pytest.param(
        {'min_version': '0.0', 'incompatible_versions': [_RUNNING_SHORT],
         'max_tested_version': '9.100'},
        'not compatible', id='short-form-in-incompatible'),
    pytest.param(
        {'min_version': '0.0', 'incompatible_versions': [_RUNNING_LONG],
         'max_tested_version': '9.100'},
        'not compatible', id='long-form-in-incompatible'),
])
def test_incompatible_python_raises(support, fragment):
    """An unmet min_version, or a running version listed in
    incompatible_versions, raises RuntimeError. Versions are built relative to
    the running interpreter so the test holds on any Python."""
    with pytest.raises(RuntimeError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            python_version_support=support)
    assert fragment in str(excinfo.value)


def test_running_above_max_tested_is_allowed():
    """min and max both 3.0: the running interpreter is >= 3.0, so the check
    passes (it only warns about being newer than tested)."""
    assert compatibility.Check(
        package_name='test',
        package_version='1',
        release_date=date(2021, 1, 1),
        python_version_support={
            'min_version': '3.0',
            'incompatible_versions': [],
            'max_tested_version': '3.0'})


@pytest.mark.parametrize("running_minor, expect_warning", [
    pytest.param(14, True, id='newer-than-tested-warns'),
    pytest.param(10, False, id='not-newer-no-warning'),
])
def test_max_tested_version_warning(caplog, running_minor, expect_warning):
    """Running a Python newer than max_tested_version warns; an equal or older
    version does not."""
    caplog.set_level(logging.WARNING)
    with patch('sys.version_info') as mock_version:
        mock_version.major = 3
        mock_version.minor = running_minor
        mock_version.releaselevel = 'final'
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            python_version_support={
                'min_version': '3.10',
                'incompatible_versions': [],
                'max_tested_version': '3.12'})
    if expect_warning:
        assert 'only tested up to 3.12' in caplog.text
        assert 'Please check for updates' in caplog.text
    else:
        assert 'only tested up to' not in caplog.text


def test_on_incompatible_warn_python(caplog):
    # 'warn' also covers an incompatible Python version instead of raising
    caplog.set_level(logging.WARNING)
    major = sys.version_info.major
    version_major_above = f"{major + 1}.0"
    check = compatibility.Check(
        package_name='test',
        package_version='1',
        release_date=date(2021, 1, 1),
        python_version_support={
            'min_version': version_major_above,
            'incompatible_versions': [],
            'max_tested_version': '99.100'},
        on_incompatible='warn')
    assert check
    assert 'need at least' in caplog.text
