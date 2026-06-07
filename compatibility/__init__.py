"""
A library that checks whether the running version of Python is compatible and
tested. Remind the user to check for updates of the library.
"""

import importlib.metadata

from compatibility.__main__ import (
    Check,
    NagOverUpdate,
    PythonVersionSupport,
    SystemSupport,
)
from compatibility import err

__all__ = [
    "Check",
    "NagOverUpdate",
    "PythonVersionSupport",
    "SystemSupport",
    "err",
]


def _get_version() -> str:
    # Reading the version from installed package metadata fails on a fresh
    # source checkout (before `pip install -e .` / `poetry install`). Fall back
    # to a placeholder so importing straight from the source tree still works.
    try:
        return importlib.metadata.version("compatibility")
    except importlib.metadata.PackageNotFoundError:
        return "0+unknown"


NAME = "compatibility"
__version__ = _get_version()
__author__ = "Rüdiger Voigt"
