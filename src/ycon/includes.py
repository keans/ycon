"""Resolve non-file `!include` URIs (env/db) to their content.

File-scheme includes are resolved by `loader.py`, which owns YAML
parsing and is the only module that needs to recurse back into it.
"""

import os
from contextlib import contextmanager
from urllib.parse import urlparse

from ycon._uri import reject_extra_parts


class MissingEnvVarError(KeyError):
    """Raised when an `env://` include names an unset variable."""


def _resolve_env(uri: str):
    parsed = urlparse(uri)
    name = parsed.netloc
    reject_extra_parts(uri, parsed, "env:// include")
    try:
        value = os.environ[name]
    except KeyError:
        raise MissingEnvVarError(
            f"Environment variable '{name}' referenced by "
            f"!include env://{name} is not set"
        ) from None
    return {"value": value}


def load_from_db(uri: str):
    """Load a config record from a database. Not yet implemented."""
    raise NotImplementedError("db:// includes are not yet supported")


# Built-in schemes, checked only when a scheme isn't in `_scheme_handlers`,
# so `register_scheme`/`unregister_scheme` can shadow and restore them.
_default_handlers = {"env": _resolve_env, "db": load_from_db}
_scheme_handlers = {}


def register_scheme(scheme: str, handler):
    """Register a handler for `!include <scheme>://...` URIs.

    `handler` receives the full URI string and returns the resolved
    value. This also lets a caller supply a real `db://` handler
    without forking the package. Registration is process-global and
    persists until `unregister_scheme` is called; see `using_scheme`
    for a scoped alternative.
    """
    _scheme_handlers[scheme] = handler


def unregister_scheme(scheme: str):
    """Remove a handler previously registered with `register_scheme`."""
    del _scheme_handlers[scheme]


@contextmanager
def using_scheme(scheme: str, handler):
    """Register `handler` for `scheme` only within this `with` block.

    Restores whatever was registered for `scheme` beforehand (or
    leaves it unregistered) on exit, even if the block raises.
    """
    previous = _scheme_handlers.get(scheme)
    register_scheme(scheme, handler)
    try:
        yield
    finally:
        if previous is None:
            _scheme_handlers.pop(scheme, None)
        else:
            _scheme_handlers[scheme] = previous


def resolve_include(uri: str):
    """Resolve a non-file `!include` URI (env/db scheme) to a value."""
    scheme = urlparse(uri).scheme
    handler = _scheme_handlers.get(scheme) or _default_handlers.get(scheme)
    if handler is None:
        raise ValueError(f"Unsupported scheme: {scheme}")
    return handler(uri)
