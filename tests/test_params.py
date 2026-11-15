"""
Constructor parameters: required values, string types and on_incompatible.

~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/compatibility
Copyright (c) 2021-2026 Rüdiger Voigt and contributors
Released under the Apache License 2.0
"""

from datetime import date
import logging

import compatibility
import pytest


def test_missing_or_empty_parameters():
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


@pytest.mark.parametrize("param", ['package_name', 'package_version',
                                   'language_messages'])
@pytest.mark.parametrize("bad_value, type_name", [
    (None, 'NoneType'),
    (1.0, 'float'),
    (['test'], 'list'),
])
def test_string_parameters_must_be_strings(param, bad_value, type_name):
    """A non-string raises a clear TypeError naming the parameter and the
    received type, instead of a raw AttributeError from .strip()."""
    kwargs = {'package_name': 'test', 'package_version': '1',
              'release_date': date(2021, 1, 1)}
    kwargs[param] = bad_value
    with pytest.raises(TypeError) as excinfo:
        compatibility.Check(**kwargs)
    assert str(excinfo.value) == (
        f'Parameter {param} must be a string, not {type_name}.')


def test_on_incompatible_invalid_value():
    # on_incompatible must be one of 'raise', 'warn', 'ignore'
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            on_incompatible='explode')
    assert 'Invalid value for on_incompatible!' in str(excinfo.value)


@pytest.mark.parametrize("bad_value", ['no', 1, None])
def test_warn_eol_must_be_bool(bad_value):
    # A truthy non-bool such as 'no' would otherwise enable the warning.
    with pytest.raises(TypeError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            warn_eol=bad_value)
    assert 'Parameter warn_eol must be True or False.' in str(excinfo.value)


@pytest.mark.parametrize("param", ['python_version_support', 'system_support',
                                   'nag_over_update'])
@pytest.mark.parametrize("falsy", [[], 0, False, ''])
def test_falsy_non_dict_is_rejected(param, falsy):
    """A falsy value that is not a dict is a wrong type like any other and
    must not silently disable the check."""
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            **{param: falsy})
    assert f'Parameter {param} must be a dictionary' in str(excinfo.value)


@pytest.mark.parametrize("param", ['python_version_support', 'system_support',
                                   'nag_over_update'])
def test_empty_dict_means_not_set(param, caplog):
    """An empty dict is accepted and behaves like None: the check is skipped."""
    caplog.set_level(logging.DEBUG, logger='compatibility')
    compatibility.Check(
        package_name='test',
        package_version='1',
        release_date=date(2021, 1, 1),
        **{param: {}})
    # Only the version info is logged; no check produced a message.
    assert [r.getMessage() for r in caplog.records] == [
        'You are using test 1 (released: 2021-01-01)']
