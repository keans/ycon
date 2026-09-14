"""Transparent gzip support for paths ending in `.gz`."""

import gzip
from contextlib import contextmanager


@contextmanager
def open_text(path: str, mode: str, encoding: str = "utf-8"):
    """Open `path` for text I/O, gzip-compressed if it ends in `.gz`."""
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, mode, encoding=encoding) as f:
        yield f
