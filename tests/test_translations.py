"""
Message languages: explicit codes, 'auto' locale detection and catalogs.

~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/compatibility
Copyright (c) 2021-2026 Rüdiger Voigt and contributors
Released under the Apache License 2.0
"""

from datetime import date

import compatibility
import pytest


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
