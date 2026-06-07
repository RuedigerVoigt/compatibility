"""
Custom Exceptions for the Compatibility Python Package

Source: https://github.com/RuedigerVoigt/compatibility
Copyright (c) 2021-2026 Rüdiger Voigt and contributors
Released under the Apache License 2.0
"""


class CompatibilityException(Exception):
    """Base exception for all compatibility package errors.

    Inherits from Exception and serves as the parent class for all
    custom exceptions in this package.
    """


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


class BadDateType(TypeError, CompatibilityException):
    """Exception raised when a date argument has an unsupported type.

    Raised when release_date is neither a datetime.date object nor a
    string. Subclasses TypeError (the conventional error for a wrong
    argument type) so it can be caught either as a TypeError or as a
    CompatibilityException.
    """
