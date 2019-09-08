r"""*pytest configuration for the* ``stdio_mgr`` *test suite*.

``stdio_mgr`` provides a context manager for convenient
mocking and/or wrapping of ``stdin``/``stdout``/``stderr``
interactions.

**Author**
    Brian Skinn (bskinn@alum.mit.edu)

**File Created**
    6 Feb 2019

**Copyright**
    \(c) Brian Skinn 2018-2019

**Source Repository**
    http://www.github.com/bskinn/stdio-mgr

**Documentation**
    See README.rst at the GitHub repository

**License**
    The MIT License; see |license_txt|_ for full license terms

**Members**

"""

import os
import sys
import warnings

import _pytest.warnings
import pytest

from stdio_mgr import stdio_mgr


def is_stdout_buffered():
    """Check if stdout is buffered.

    Copied from https://stackoverflow.com/a/49736559
    Licensed CC-BY-SA 4.0
    Author https://stackoverflow.com/users/528711/sparrowt
    """
    # Print a single space + carriage return but no new-line
    # (should have no visible effect)
    print(" \r")
    # If the file position is a positive integer then stdout is buffered
    try:
        pos = sys.stdout.tell()
        if pos > 0:
            return True
    except IOError:  # In some terminals tell() throws IOError if stdout is unbuffered
        pass
    return False


@pytest.fixture(scope="session")
def warnings_are_errors(pytestconfig):
    """Provide concise access to '-W error::Warning' CLI option."""
    try:
        cmdline_filters = pytestconfig.getoption("pythonwarnings")
    except ValueError:
        return False

    return cmdline_filters and "error::Warning" in cmdline_filters


@pytest.fixture
def check_warnings_plugin_enabled():
    """Check the warnings module is enabled."""
    # Check pytest was not invoked with -p no:warnings.
    try:
        impl = warnings._showwarnmsg_impl
    except AttributeError:
        # Python < 3.6
        impl = warnings.showwarning

    return impl.__name__ == "append"


@pytest.fixture
def enable_warnings_plugin(request):
    """Enable warnings for a single test."""
    assert check_warnings_plugin_enabled
    with _pytest.warnings.catch_warnings_for_item(
        config=request.config,
        ihook=request.node.ihook,
        when="runtest",
        item=request.node,
    ):
        yield


@pytest.fixture(scope="session")
def unbufferedio():
    """Provide concise access to PYTHONUNBUFFERED envvar."""
    return os.environ.get("PYTHONUNBUFFERED") or not is_stdout_buffered()


@pytest.fixture(autouse=True)
def add_stdio_mgr(doctest_namespace):
    """Add stdio_mgr to doctest namespace."""
    doctest_namespace["stdio_mgr"] = stdio_mgr
    doctest_namespace["os"] = os


@pytest.fixture(scope="session")
def convert_newlines():
    """Supply platform-dependent newline transform function."""
    if sys.platform == "win32":
        return lambda s: s.replace("\n", "\r\n")
    else:
        return lambda s: s
