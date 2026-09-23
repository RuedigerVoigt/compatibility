"""
Package surface: exports, exceptions, version metadata and the
`python -m compatibility` entry point.

~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/compatibility
Copyright (c) 2021-2026 Rüdiger Voigt and contributors
Released under the Apache License 2.0
"""

import sys

import compatibility
import pytest

from compatibility import err


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


def test_deprecated_main_import_alias():
    """The library code moved from compatibility/__main__.py to
    compatibility/core.py. Old imports from compatibility.__main__ keep
    working but emit a DeprecationWarning."""
    import importlib
    sys.modules.pop('compatibility.__main__', None)
    with pytest.warns(DeprecationWarning, match='compatibility.__main__'):
        legacy = importlib.import_module('compatibility.__main__')
    assert legacy.Check is compatibility.Check
    assert legacy.SUPPORTED_LANGUAGES == compatibility.core.SUPPORTED_LANGUAGES
    assert legacy.PythonVersionSupport is compatibility.PythonVersionSupport
    assert legacy.NagOverUpdate is compatibility.NagOverUpdate
    assert legacy.SystemSupport is compatibility.SystemSupport
    assert legacy.logger is compatibility.core.logger


def test_run_as_module(capsys, recwarn):
    """`python -m compatibility` prints name and version, without the
    DeprecationWarning meant for importers."""
    import runpy
    runpy.run_module('compatibility', run_name='__main__', alter_sys=False)
    assert capsys.readouterr().out == (
        f"{compatibility.NAME} {compatibility.__version__}\n")
    assert not [w for w in recwarn if w.category is DeprecationWarning]
