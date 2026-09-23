"""
Entry point for `python -m compatibility` and a deprecated import alias.

The library code lives in `compatibility.core`. This module used to hold it,
so its public names are re-exported here to keep old imports such as
`from compatibility.__main__ import Check` working. Importing this module
emits a DeprecationWarning; import from `compatibility` instead.

Copyright (c) 2021-2026 Rüdiger Voigt and contributors
Released under the Apache License 2.0
"""

import warnings

from compatibility import NAME, __version__
from compatibility.core import (  # noqa: F401 (re-exported for old imports)
    SUPPORTED_LANGUAGES,
    Check,
    NagOverUpdate,
    PythonVersionSupport,
    SystemSupport,
    logger,
)

if __name__ == '__main__':
    print(f'{NAME} {__version__}')
else:
    warnings.warn(
        'Importing from compatibility.__main__ is deprecated and will be '
        'removed in version 3. Import from compatibility instead '
        '(e.g. "from compatibility import Check").',
        DeprecationWarning,
        stacklevel=2)
