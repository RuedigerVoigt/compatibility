"""
README examples: every Python block marked as tested runs without error, and
prints the output the README shows for it.

~~~~~~~~~~~~~~~~~~~~~
Source: https://github.com/RuedigerVoigt/compatibility
Copyright (c) 2021-2026 Rüdiger Voigt and contributors
Released under the Apache License 2.0
"""

from pathlib import Path
import re
import subprocess
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
README = (REPO_ROOT / 'README.md').read_text(encoding='utf-8')

# A tested example is a ```python block directly after a "<!-- tested -->"
# line (invisible on GitHub). If "Output:" and a ```text block follow, that is
# the exact output the example must log.
TESTED_BLOCK = re.compile(
    r'<!-- tested -->\n```python\n(?P<code>.*?)```\n'
    r'(?:\s*Output:\s*```text\n(?P<output>.*?)```)?',
    re.DOTALL)


def _heading_before(position):
    """The README heading an example belongs to, used as the test id."""
    return re.findall(r'^#+ (.+)$', README[:position], re.MULTILINE)[-1]


EXAMPLES = [pytest.param(m.group('code'), m.group('output'),
                         id=_heading_before(m.start()))
            for m in TESTED_BLOCK.finditer(README)]


def test_readme_has_tested_examples():
    """Guard against a changed marker or pattern silently testing nothing:
    Quick Start, Extended Example, and three recipes; two show their output."""
    assert [example.id for example in EXAMPLES] == [
        'Quick Start', 'Extended Example',
        'Command-Line Tool: Configure Logging First',
        'Warn Instead of Raising', 'Typed Configuration']
    assert sum(example.values[1] is not None for example in EXAMPLES) == 2


@pytest.mark.parametrize("code, expected_output", EXAMPLES)
def test_readme_example_runs(code, expected_output):
    """Run the example in a fresh interpreter, as a user would, so its
    logging setup does not interfere with the test session. Its log output
    goes to stderr."""
    result = subprocess.run(
        [sys.executable, '-c', code], cwd=REPO_ROOT,
        capture_output=True, text=True, encoding='utf-8', timeout=60)
    assert result.returncode == 0, result.stderr
    if expected_output is not None:
        assert result.stderr.strip() == expected_output.strip()
