#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import date

from compatibility.__main__ import Check

NAME = "compatibility"
__version__ = "0.8"
__author__ = "Rüdiger Voigt"

Check(
    package_name=NAME,
    package_version=__version__,
    release_date=date(2021, 1, 17),
    python_version_support={
        'min_version': '3.6',
        'incompatible_versions': [],
        'max_tested_version': '3.9'
    },
    nag_over_update=None,
    language_messages='en'
    )
