"""Scoped cycle tracking for recursive traversals."""

from contextlib import contextmanager


@contextmanager
def track_active(active: set, key, message: str):
    """Track a key on the current branch, removing it even on failure."""
    if key in active:
        raise ValueError(message)
    active.add(key)
    try:
        yield
    finally:
        active.remove(key)
