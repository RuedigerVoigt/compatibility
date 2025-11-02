"""
Custom Exceptions for the Compatibility Python Package

Source: https://github.com/RuedigerVoigt/compatibility
Copyright (c) 2021-2025 Rüdiger Voigt and contributors
Released under the Apache License 2.0
"""


class CompatibilityException(Exception):
    """Base exception for all compatibility package errors.

    Inherits from Exception and serves as the parent class for all
    custom exceptions in this package.
    """
    def __init__(self, *args: object, **kwargs: object) -> None:
        Exception.__init__(self, *args, **kwargs)


class ParameterContradiction(ValueError, CompatibilityException):
    """Exception raised when parameters contain contradictory values.

    Raised when system_support contains the same OS in conflicting
    categories (e.g., both 'full' and 'incompatible').
    """


class BadDate(ValueError, CompatibilityException):
    """Exception raised when a date is invalid or malformed.

    Raised when release_date cannot be parsed or represents a
    non-existent date (e.g., "2021-02-30").
    """
