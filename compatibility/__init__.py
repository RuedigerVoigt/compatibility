#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
A library that checks whether the running version of Python is compatible and
tested. Remind the user to check for updates of the library.
"""

from compatibility.__main__ import Check
from compatibility import _version

NAME = "compatibility"
__version__ = _version.__version__
__author__ = "Rüdiger Voigt"
