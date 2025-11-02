"""
Custom Exceptions for the Compatibility Python Package

Source: https://github.com/RuedigerVoigt/compatibility
(c) 2021 Rüdiger Voigt:
Released under the Apache License 2.0
"""


class CompatibilityException(Exception):
    "An exception occured"
    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        Exception.__init__(self, *args, **kwargs)


class ParameterContradition(ValueError, CompatibilityException):
    "Two or more parameters contradict each other."


class BadDate(ValueError, CompatibilityException):
    "The provided date is malformed / nonexistent."
