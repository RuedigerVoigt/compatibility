"""
release_date: coercion, validation and plausibility warnings.

~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/compatibility
Copyright (c) 2021-2026 Rüdiger Voigt and contributors
Released under the Apache License 2.0
"""

from datetime import date, timedelta
import logging

import compatibility
import pytest

from compatibility import err


def test_release_date():
    # Neither a date object nor a string
    with pytest.raises(err.BadDateType):
        compatibility.Check(
            package_name='test',
            package_version='0.1',
            release_date=(2021, 1, 1))
    # BadDateType is also catchable as a plain TypeError and as the library base
    with pytest.raises(TypeError):
        compatibility.Check(
            package_name='test',
            package_version='0.1',
            release_date=(2021, 1, 1))
    with pytest.raises(err.CompatibilityException):
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


def test_release_date_far_future_warns(caplog):
    """A release_date more than 60 days ahead is almost certainly a typo and
    should log a warning (but not raise)."""
    caplog.set_level(logging.WARNING)
    far_future = date.today() + timedelta(days=61)
    compatibility.Check(
        package_name='test',
        package_version='1',
        release_date=far_future)
    assert 'in the future' in caplog.text


def test_release_date_near_future_no_warning(caplog):
    """A release_date within 60 days ahead (developing toward a planned
    release) must not warn."""
    caplog.set_level(logging.WARNING)
    near_future = date.today() + timedelta(days=30)
    compatibility.Check(
        package_name='test',
        package_version='1',
        release_date=near_future)
    assert 'in the future' not in caplog.text


def test_release_date_far_past_warns(caplog):
    """A release_date more than 8 years old suggests it was never updated and
    should log a warning (but not raise)."""
    caplog.set_level(logging.WARNING)
    far_past = date.today() - timedelta(days=365 * 9)
    compatibility.Check(
        package_name='test',
        package_version='1',
        release_date=far_past)
    assert 'in the past' in caplog.text


def test_release_date_recent_past_no_warning(caplog):
    """A release_date within the last 8 years must not warn."""
    caplog.set_level(logging.WARNING)
    recent = date.today() - timedelta(days=365)
    compatibility.Check(
        package_name='test',
        package_version='1',
        release_date=recent)
    assert 'in the past' not in caplog.text
