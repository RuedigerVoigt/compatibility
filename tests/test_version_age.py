"""
Update nagging and version info: nag_over_update validation, nag
probability and the logged package version.

~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/compatibility
Copyright (c) 2021-2026 Rüdiger Voigt and contributors
Released under the Apache License 2.0
"""

from datetime import date, timedelta
import logging
from unittest.mock import patch

import compatibility
import pytest


def test_nag_over_update_not_dict():
    # A non-dict nag_over_update gets a clear ValueError, not a raw
    # AttributeError from calling .keys() on the wrong type.
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            nag_over_update=['nag'])
    assert 'nag_over_update must be a dictionary' in str(excinfo.value)


@pytest.mark.parametrize("nag, fragment", [
    pytest.param({'nag_days_after_release': -42, 'nag_in_hundred': 100},
                 'nag_days_after_release must not be negative.',
                 id='negative-days'),
    pytest.param({'nag_in_hundred': 50},
                 'missing', id='missing-key'),
    pytest.param({'nag_days_after_release': 'foo', 'nag_in_hundred': 100},
                 'Some key in nag_over_update has wrong type!',
                 id='string-days'),
    pytest.param({'nag_days_after_release': 3.7, 'nag_in_hundred': 50},
                 'Some key in nag_over_update has wrong type!',
                 id='float-days-rejected-not-truncated'),
    pytest.param({'nag_days_after_release': 3, 'nag_in_hundred': True},
                 'Some key in nag_over_update has wrong type!',
                 id='bool-rejected-not-treated-as-int'),
    pytest.param({'nag_days_after_release': 3, 'nag_in_hundred': -100},
                 'must be int between 0 and 100', id='nag-in-hundred-negative'),
    pytest.param({'nag_days_after_release': 3, 'nag_in_hundred': 101},
                 'must be int between 0 and 100', id='nag-in-hundred-above-100'),
])
def test_nag_over_update_invalid(nag, fragment):
    """Malformed nag_over_update values raise ValueError with a clear message."""
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            nag_over_update=nag)
    assert fragment in str(excinfo.value)


# Note: datetime cannot be mocked directly (it is C code), so the release date
# is calculated relative to today instead. See:
# https://docs.python.org/3/library/unittest.mock-examples.html#partial-mocking
@pytest.mark.parametrize("release, nag", [
    pytest.param(date(2021, 1, 1),
                 {'nag_days_after_release': 1, 'nag_in_hundred': 0},
                 id='nag-in-hundred-zero'),
    pytest.param(date.today() - timedelta(days=7),
                 {'nag_days_after_release': 100, 'nag_in_hundred': 100},
                 id='below-threshold'),
    pytest.param(date.today() - timedelta(days=7),
                 {'nag_days_after_release': 3, 'nag_in_hundred': 100},
                 id='above-threshold'),
])
def test_nag_over_update_valid(release, nag):
    """Valid nag_over_update configurations are accepted: zero probability,
    age below the threshold, and age above the threshold."""
    assert compatibility.Check(
        package_name='test',
        package_version='1',
        release_date=release,
        nag_over_update=nag)


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
    assert 'Please check for updates' in caplog.text


def test_check_version_age_random_above_probability(caplog):
    """Past the threshold, but the random draw lands above the probability:
    no nag should be logged."""
    caplog.set_level(logging.INFO)
    # probability is 0.5; force random.random() to return a value >= 0.5 so the
    # nag is skipped deterministically.
    with patch('random.random', return_value=0.9):
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            nag_over_update={
                    'nag_days_after_release': 3,
                    'nag_in_hundred': 50
                })
    assert 'Please check for updates' not in caplog.text


def test_version_info_logging(caplog):
    """Test that version info is logged for packages other than 'compatibility' itself."""
    caplog.set_level(logging.INFO)
    compatibility.Check(
        package_name='my_package',
        package_version='2.5.0',
        release_date=date(2024, 6, 15)
    )
    # Verify version info is logged
    assert 'You are using my_package 2.5.0' in caplog.text
    assert '2024-06-15' in caplog.text

    # Verify compatibility itself doesn't log its own version
    caplog.clear()
    compatibility.Check(
        package_name='compatibility',
        package_version='2.0.0',
        release_date=date(2025, 1, 1)
    )
    assert 'You are using compatibility' not in caplog.text
