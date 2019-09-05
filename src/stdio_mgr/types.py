r"""``stdio_mgr.types`` *code module*.

``stdio_mgr.types`` provides context managers for convenient
interaction with ``stdin``/``stdout``/``stderr`` as a tuple.

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
import abc
import sys
from contextlib import ExitStack, suppress
from io import TextIOBase

import _collections_abc

# AbstractContextManager was introduced in Python 3.6
# and may be used with typing.ContextManager.
try:
    from contextlib import AbstractContextManager
except ImportError:  # pragma: no cover

    class AbstractContextManager(abc.ABC):
        """An abstract base class for context managers."""

        def __enter__(self):
            """Return `self` upon entering the runtime context."""
            return self

        @abc.abstractmethod
        def __exit__(self, exc_type, exc_value, traceback):
            """Raise any exception triggered within the runtime context."""
            return None

        @classmethod
        def __subclasshook__(cls, subclass):
            """Check whether subclass is considered a subclass of this ABC."""
            if cls is AbstractContextManager:
                return _collections_abc._check_methods(
                    subclass, "__enter__", "__exit__"
                )
            return NotImplemented


class TupleContextManager(tuple, AbstractContextManager):
    """Base for context managers that are also a tuple."""

    # This is needed to establish a workable MRO.


class StdioTuple(TupleContextManager):
    """Tuple context manager of stdin, stdout and stderr stream-like objects."""

    def __new__(cls, iterable):
        """Instantiate new tuple from iterable containing three streams."""
        items = list(iterable)
        assert len(items) == 3, "iterable must be three items"  # noqa: S101

        return super(StdioTuple, cls).__new__(cls, items)

    @property
    def stdin(self):
        """Return capturing stdin stream."""
        return self[0]

    @property
    def stdout(self):
        """Return capturing stdout stream."""
        return self[1]

    @property
    def stderr(self):
        """Return capturing stderr stream."""
        return self[2]

    def _map_method(self, method: str):
        """Perform method on all streams."""
        for item in self:
            yield item.__dict__[method](item)

    def _map(self, op):
        """Return generator for performing op on all streams."""
        if isinstance(op, str):
            return self._map_method(op)

        return map(op, self)

    def suppress_map(self, ex, op):
        """Return generator for performing op on all streams, suppressing ex."""
        for item in self:
            with suppress(ex):
                op_inner = item.__dict__[op] if isinstance(op, str) else op
                yield op_inner(item)

    def _all(self, op):
        """Perform op on all streams, returning True when all were successful."""
        return all(self._map(op))

    def suppress_all(self, ex, op):
        """Perform op on all streams, suppressing ex."""
        return all(self.suppress_map(ex, op))

    def close(self):
        """Close all streams."""
        return self._all("close")


class TextIOTuple(StdioTuple):
    """Tuple context manager of stdin, stdout and stderr TextIOBase objects."""

    # pytest and colorama inject objects into sys.std* that are not real TextIOBase
    # and fail the assertion of this class

    def __new__(cls, iterable):
        """Instantiate new tuple from iterable containing three TextIOBase streams."""
        self = super(StdioTuple, cls).__new__(cls, iterable)
        assert self._all(  # noqa: S101
            lambda item: isinstance(item, TextIOBase)
        ), "iterable must contain only TextIOBase"
        return self


class _MultiCloseContextManager(StdioTuple):
    """Manage multiple closable members of a tuple."""

    def __enter__(self):
        """Enter context of all members."""
        with ExitStack() as stack:
            # If not all items are TextIOBase, they may not have __exit__
            self.suppress_all(AttributeError, stack.enter_context)

            self._close_files = stack.pop_all().close

        return super().__enter__()

    def close(self):
        self._close_files()

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit context, closing all members."""
        self.close()
        return super().__exit__(exc_type, exc_value, traceback)
