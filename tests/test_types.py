r"""*Submodule for test suite of the* ``stdio_mgr.types`` components.

**Author**
    John Vandenberg (jayvdb@gmail.com)

**File Created**
    6 Sep 2019

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

import io

import pytest

from stdio_mgr.stdio_mgr import _IMPORT_SYS_STREAMS, _RUNTIME_SYS_STREAMS, _Tee
from stdio_mgr.types import _MultiCloseContextManager, FakeIOTuple, TextIOTuple


def test_sys_module(request):
    """Confirm sys module objects are of expected types."""
    assert isinstance(_RUNTIME_SYS_STREAMS, TextIOTuple)

    # This probably isnt enough, due to capture.py _py36_windowsconsoleio_workaround
    if request.config.known_args_namespace.capture == "no":
        assert isinstance(_RUNTIME_SYS_STREAMS, TextIOTuple)
    else:
        assert isinstance(_IMPORT_SYS_STREAMS, FakeIOTuple)


def test_tee_type():
    """Test that incorrect type for Tee.tee raises ValueError."""
    with pytest.raises(ValueError) as err:
        _Tee(tee="str", buffer=io.StringIO())

    assert str(err.value) == "tee must be a TextIOBase."


def test_non_closing_type():
    """Test that incorrect type doesnt raise exceptions."""
    empty_string = ""
    empty_string_tuple = (empty_string, empty_string, empty_string)

    # Ensure empty_string used has no __exit__ or close()
    assert not hasattr(empty_string, "__exit__")
    assert not hasattr(empty_string, "close")

    with FakeIOTuple(empty_string_tuple):
        pass

    class MultiClosseFakeIOTuple(_MultiCloseContextManager, FakeIOTuple):
        pass

    with MultiClosseFakeIOTuple(empty_string_tuple):
        pass

    with pytest.raises(ValueError) as err:
        TextIOTuple((empty_string, empty_string, empty_string))

    assert str(err.value) == "iterable must contain only TextIOBase"
