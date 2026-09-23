"""
Message languages: explicit codes, 'auto' locale detection and catalogs.

~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/compatibility
Copyright (c) 2021-2026 Rüdiger Voigt and contributors
Released under the Apache License 2.0
"""

from datetime import date
import gettext
from pathlib import Path
import re

import compatibility
import compile_translations
import pytest

from compatibility.core import SUPPORTED_LANGUAGES


REPO_ROOT = Path(__file__).resolve().parent.parent
LOCALES = REPO_ROOT / 'compatibility' / 'locales'
POT_PATH = LOCALES / 'compatibility.pot'
TRANSLATED_LANGUAGES = [lang for lang in SUPPORTED_LANGUAGES if lang != 'en']
# printf-style placeholders: %s, %d, %(name)s, ... and the literal %%
PLACEHOLDER = re.compile(r'%(?:\([^)]*\))?[-#0 +]*\d*(?:\.\d+)?[diouxXeEfFgGcrsa%]')


def _without_locations(text):
    """Drop '#: file:line' comments, which shift whenever code moves."""
    return '\n'.join(line for line in text.splitlines()
                     if not line.startswith('#:'))


def _catalog(po_path):
    """Parse a .po/.pot file into {msgid: msgstr}, without the header."""
    catalog = compile_translations._parse_po(str(po_path))
    catalog.pop('', None)
    return catalog


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


def test_pot_template_is_up_to_date(monkeypatch):
    """The committed .pot template matches the messages in the source.
    If this fails, run: python compile_translations.py --extract"""
    monkeypatch.chdir(REPO_ROOT)
    expected = compile_translations.build_pot(
        compile_translations.extract_messages())
    actual = POT_PATH.read_text(encoding='utf-8')
    assert _without_locations(actual) == _without_locations(expected), (
        'compatibility.pot is out of date; '
        'run: python compile_translations.py --extract')


def test_every_supported_language_has_a_catalog():
    """Each non-English language code has a .po file, and vice versa."""
    on_disk = sorted(p.parent.parent.name
                     for p in LOCALES.glob('*/LC_MESSAGES/compatibility.po'))
    assert on_disk == sorted(TRANSLATED_LANGUAGES)


@pytest.mark.parametrize("lang", TRANSLATED_LANGUAGES)
def test_po_catalog_matches_template(lang):
    """Each .po has exactly the template's messages: nothing missing, nothing
    obsolete."""
    po = _catalog(LOCALES / lang / 'LC_MESSAGES' / 'compatibility.po')
    pot = _catalog(POT_PATH)
    assert sorted(set(pot) - set(po)) == [], 'messages missing from .po'
    assert sorted(set(po) - set(pot)) == [], 'obsolete messages in .po'


@pytest.mark.parametrize("lang", TRANSLATED_LANGUAGES)
def test_po_catalog_fully_translated(lang):
    """No message is left untranslated (gettext would silently show English)."""
    po = _catalog(LOCALES / lang / 'LC_MESSAGES' / 'compatibility.po')
    assert [msgid for msgid, msgstr in po.items() if not msgstr] == []


@pytest.mark.parametrize("lang", TRANSLATED_LANGUAGES)
def test_po_placeholders_match(lang):
    """Every translation keeps the placeholders of its message; a mismatch
    makes the % formatting of the log message fail at runtime."""
    po = _catalog(LOCALES / lang / 'LC_MESSAGES' / 'compatibility.po')
    mismatches = [
        msgid for msgid, msgstr in po.items()
        if sorted(PLACEHOLDER.findall(msgid)) != sorted(PLACEHOLDER.findall(msgstr))]
    assert mismatches == []


def test_extract_messages(tmp_path, monkeypatch):
    """Extraction finds self._() and _() calls in source order, records every
    location, and survives quotes, backslashes and newlines in a message."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'pkg').mkdir()
    (tmp_path / 'pkg' / 'mod.py').write_text(
        'def f(self, _):\n'
        '    self._("Second")\n'
        r"    _('First \"quoted\" \\ back\nslash')" '\n'
        '    self._("Second")\n'
        '    self.other("Not a message")\n', encoding='utf-8')
    messages = compile_translations.extract_messages('pkg')
    assert messages == {
        'Second': ['pkg/mod.py:2', 'pkg/mod.py:4'],
        'First "quoted" \\ back\nslash': ['pkg/mod.py:3'],
    }
    # Round trip: the rendered template parses back to the same messages.
    pot = tmp_path / 'test.pot'
    pot.write_text(compile_translations.build_pot(messages), encoding='utf-8')
    assert set(_catalog(pot)) == set(messages)


def test_extract_rejects_non_literal(tmp_path, monkeypatch):
    """A message that is not a single string literal cannot be extracted."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'pkg').mkdir()
    (tmp_path / 'pkg' / 'mod.py').write_text(
        'def f(self, text):\n    self._(text)\n', encoding='utf-8')
    with pytest.raises(ValueError, match='pkg/mod.py:2'):
        compile_translations.extract_messages('pkg')


def test_new_language_from_template(tmp_path):
    """The template works as the start of a new language: copy it, translate
    a message, compile it, and Python's gettext uses the translation."""
    po_text = POT_PATH.read_text(encoding='utf-8').replace(
        'msgid "Missing package name!"\nmsgstr ""',
        'msgid "Missing package name!"\nmsgstr "Nome del pacchetto mancante!"')
    assert 'Nome del pacchetto mancante!' in po_text
    po, mo = tmp_path / 'it.po', tmp_path / 'it.mo'
    po.write_text(po_text, encoding='utf-8')
    compile_translations.compile_po_to_mo(str(po), str(mo))
    with open(mo, 'rb') as f:
        translation = gettext.GNUTranslations(f)
    assert translation.gettext('Missing package name!') == 'Nome del pacchetto mancante!'
    # Untranslated messages fall back to English.
    assert translation.gettext('Missing package version!') == 'Missing package version!'
