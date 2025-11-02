"""
A library that checks whether the running version of Python is compatible and
tested. Remind the user to check for updates of the library.
"""

import importlib.metadata

from compatibility.__main__ import Check
from compatibility import err

NAME = "compatibility"
__version__ = importlib.metadata.version("compatibility")
__author__ = "Rüdiger Voigt"
