"""Smoke tests: verify the package imports and basic structure works."""

import lbe


def test_package_imports():
    """The lbe package can be imported without errors."""
    assert lbe is not None


def test_python_version():
    """Verify we're on Python 3.11+."""
    import sys

    assert sys.version_info >= (3, 11), f"Need Python 3.11+, got {sys.version_info}"
