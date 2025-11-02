"""
Custom Exceptions for the Compatibility Python Package

Source: https://github.com/RuedigerVoigt/compatibility
Copyright (c) 2021-2025 Rüdiger Voigt and contributors
Released under the Apache License 2.0
"""


class CompatibilityException(Exception):
    "An exception occured"
    def __init__(self, *args: object, **kwargs: object) -> None:
        Exception.__init__(self, *args, **kwargs)


class ParameterContradition(ValueError, CompatibilityException):
    "Two or more parameters contradict each other."


class BadDate(ValueError, CompatibilityException):
    "The provided date is malformed / nonexistent."
