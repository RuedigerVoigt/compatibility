"""
Automatic Tests for the Compatibility library

~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/compatibility
Copyright (c) 2021-2026 Rüdiger Voigt and contributors
Released under the Apache License 2.0
"""

from datetime import date, timedelta
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

    # all shipped languages plus 'auto' are accepted
    for lang in ('en', 'de', 'fr', 'nl', 'es', 'auto'):
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            language_messages=lang)


def test_language_auto_uses_environment_locale(monkeypatch):
    """language_messages='auto' picks the language from the environment."""
    for var in ('LC_ALL', 'LC_MESSAGES', 'LANG'):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv('LANGUAGE', 'de')
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='',
            package_version='1',
            release_date=date(2021, 1, 1),
            language_messages='auto')
    assert 'Fehlender Paketname' in str(excinfo.value)


def test_language_auto_falls_back_to_english(monkeypatch):
    """language_messages='auto' falls back to English when no catalog matches."""
    for var in ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
        monkeypatch.setenv(var, 'xx')
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='',
            package_version='1',
            release_date=date(2021, 1, 1),
            language_messages='auto')
    assert 'Missing package name!' in str(excinfo.value)


def test_translations_load():
    """Every non-source catalog resolves a known message to its language."""
    expected = {
        'de': 'Fehlender Paketname',
        'fr': 'Nom de paquet manquant',
        'nl': 'Ontbrekende pakketnaam',
        'es': 'Falta el nombre del paquete',
    }
    for lang, fragment in expected.items():
        with pytest.raises(ValueError) as excinfo:
            compatibility.Check(
                package_name='',
                package_version='1',
                release_date=date(2021, 1, 1),
                language_messages=lang)
        assert fragment in str(excinfo.value)


def test_language_messages_actually_work():
    """Verify that language_messages parameter actually selects the correct translations."""
    # Test English messages
    with pytest.raises(ValueError) as excinfo_en:
        compatibility.Check(
            package_name='',  # Empty name triggers error
            package_version='1',
            release_date=date(2021, 1, 1),
            language_messages='en')
    assert 'Missing package name!' in str(excinfo_en.value)

    # Test German messages
    with pytest.raises(ValueError) as excinfo_de:
        compatibility.Check(
            package_name='',  # Empty name triggers error
            package_version='1',
            release_date=date(2021, 1, 1),
            language_messages='de')
    # German translation for "Missing package name!"
    assert 'Fehlender Paketname!' in str(excinfo_de.value)

    # Test that two instances with different languages work independently
    # Create instance with English
    check_en = compatibility.Check(
        package_name='test_en',
        package_version='1.0',
        release_date=date(2021, 1, 1),
        language_messages='en')
    # Create instance with German
    check_de = compatibility.Check(
        package_name='test_de',
        package_version='1.0',
        release_date=date(2021, 1, 1),
        language_messages='de')

    # Verify each instance uses its own language
    # Test by triggering an error from each instance's methods
    with pytest.raises(ValueError) as excinfo_en2:
        check_en.check_params.__self__.package_name = ''
        check_en.check_params()
    assert 'Missing package name!' in str(excinfo_en2.value)

    with pytest.raises(ValueError) as excinfo_de2:
        check_de.check_params.__self__.package_name = ''
        check_de.check_params()
    assert 'Fehlender Paketname!' in str(excinfo_de2.value)


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


def test_on_incompatible_invalid_value():
    # on_incompatible must be one of 'raise', 'warn', 'ignore'
    with pytest.raises(ValueError) as excinfo:
        compatibility.Check(
            package_name='test',
            package_version='1',
            release_date=date(2021, 1, 1),
            on_incompatible='explode')
    assert 'Invalid value for on_incompatible!' in str(excinfo.value)


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


def test_compatibility_exception_message():
    """Base compatibility exceptions preserve the given error message."""
    exception = err.CompatibilityException('base failure')

    assert str(exception) == 'base failure'


def test_config_typeddicts_exported():
    """The config TypedDicts are exported from the package root so consumers
    can annotate their configuration dictionaries."""
    from compatibility import (
        NagOverUpdate,
        PythonVersionSupport,
        SystemSupport,
    )

    for name in ('PythonVersionSupport', 'NagOverUpdate', 'SystemSupport'):
        assert name in compatibility.__all__
        assert hasattr(compatibility, name)

    # At runtime a TypedDict value is a plain dict; annotating with it is valid.
    versions: PythonVersionSupport = {
        'min_version': '3.10',
        'incompatible_versions': [],
        'max_tested_version': '3.14',
    }
    nag: NagOverUpdate = {'nag_days_after_release': 30, 'nag_in_hundred': 50}
    systems: SystemSupport = {'full': {'Linux'}}
    assert versions['min_version'] == '3.10'
    assert nag['nag_in_hundred'] == 50
    assert systems['full'] == {'Linux'}


def test_version_fallback(monkeypatch):
    """_get_version falls back to a placeholder when package metadata is absent
    (e.g. importing from a fresh source checkout that was never installed)."""
    import importlib.metadata

    def raise_not_found(name):
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(importlib.metadata, 'version', raise_not_found)
    assert compatibility._get_version() == '0+unknown'
