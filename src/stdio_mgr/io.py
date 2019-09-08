"""IO related functions and classes."""
import os
import sys


def is_stdout_buffered():
    """Check if stdout is buffered.

    Copied from https://stackoverflow.com/a/49736559
    Licensed CC-BY-SA 4.0
    Author https://stackoverflow.com/users/528711/sparrowt
    with a fix of the print for Python 3 compatibility
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


def is_stdio_unbufferedio():
    """Detect if PYTHONUNBUFFERED was set or if -u was used."""
    # Use of is_stdout_buffered is temporary, because -u is not reflected
    # anywhere in the python sys module, such as sys.flags.
    # It is undesirable as written, as it has side-effects, especially bad
    # side-effects as using a stream usually causes parts of the stream
    # state to get baked-in, preventing reconfiguration on Python 3.7.
    # Also temporary because of incompatible licensing.
    # It should be possible to detect unbuffered by the *initial* state of
    # sys.stdout and its buffers.
    # Also need to take into account PYTHONLEGACYWINDOWSSTDIO
    # And all this is quite unhelpful because the state of sys.stdio
    # may be very different by the time that a StdioManager is instantiated
    if os.environ.get("PYTHONUNBUFFERED"):
        return True
    if is_stdout_buffered():
        return False
    if sys.stdout.isatty():
        return False
    return True
