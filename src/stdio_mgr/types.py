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
import collections.abc
import sys
from abc import ABC
from contextlib import ExitStack, suppress
from io import TextIOBase


# AbstractContextManager was introduced in Python 3.6
# and may be used with typing.ContextManager.
try:
    from contextlib import AbstractContextManager
except ImportError:  # pragma: no cover

    class AbstractContextManager(ABC):
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
                return collections.abc._check_methods(subclass, "__enter__", "__exit__")
            return NotImplemented


class MultiItemTuple(collections.abc.Iterable):
    """Iterable with methods that operate on all items."""

    def _map_method(self, method: str):
        """Perform method on all items."""
        for item in self:
            yield item.__dict__[method](item)

    def _map(self, op):
        """Return generator for performing op on all items."""
        if isinstance(op, str):
            return self._map_method(op)

        return map(op, self)

    def suppress_map(self, ex, op):
        """Return generator for performing op on all item, suppressing ex."""
        for item in self:
            with suppress(ex):
                op_inner = item.__dict__[op] if isinstance(op, str) else op
                yield op_inner(item)

    def _all(self, op):
        """Perform op on all items, returning True when all were successful."""
        return all(self._map(op))

    def suppress_all(self, ex, op):
        """Perform op on all items, suppressing ex."""
        return all(self.suppress_map(ex, op))


class TupleContextManager(tuple, AbstractContextManager):
    """Base for context managers that are also a tuple."""

    # This is needed to establish a workable MRO.


class StdioTupleBase(TupleContextManager, MultiItemTuple):
    """Tuple context manager of stdin, stdout and stderr stream-like objects."""

    def __new__(cls, iterable):
        """Instantiate new tuple from iterable containing three streams."""
        items = list(iterable)
        assert len(items) == 3, "iterable must be three items"  # noqa: S101

        return super(StdioTupleBase, cls).__new__(cls, items)

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

    def close(self):
        """Close all streams."""
        return self._all("close")


class TextIOTuple(StdioTupleBase):
    """Tuple context manager of stdin, stdout and stderr TextIOBase objects."""

    _ITEM_BASE = TextIOBase

    # pytest and colorama inject objects into sys.std* that are not real TextIOBase
    # and fail the assertion of this class

    def __new__(cls, iterable):
        """Instantiate new tuple from iterable containing three TextIOBase streams."""
        self = super(TextIOTuple, cls).__new__(cls, iterable)
        if not self._all(lambda item: isinstance(item, cls._ITEM_BASE)):
            raise ValueError(
                "iterable must contain only {}".format(cls._ITEM_BASE.__name__)
            )
        return self


class FakeIOTuple(StdioTupleBase):
    """Tuple context manager of stdin, stdout and stderr-like objects."""


class AnyIOTuple(StdioTupleBase):
    def __new__(cls, iterable):
        """Instantiate new TextIOTuple or StdioTuple from iterable."""
        items = list(iterable)
        if any(not isinstance(item, TextIOTuple._ITEM_BASE) for item in items):
            return FakeIOTuple(items)
        else:
            return TextIOTuple(items)


class _MultiCloseContextManager(AbstractContextManager, MultiItemTuple):
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


class ReplaceSysIoContextManager(StdioTupleBase):
    """Replace sys stdio with members of the tuple."""

    def __enter__(self):
        """Enter context, replacing sys stdio objects with streams from this tuple."""
        self._prior_streams = (sys.stdin, sys.stdout, sys.stderr)

        super().__enter__()

        (sys.stdin, sys.stdout, sys.stderr) = self

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit context, restoring state of sys module."""
        (sys.stdin, sys.stdout, sys.stderr) = self._prior_streams

        return super().__exit__(exc_type, exc_value, traceback)
