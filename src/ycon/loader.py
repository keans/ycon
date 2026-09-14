"""Load YAML config files with `!include` and `!ref` support."""

import os
from contextvars import ContextVar
from functools import partial
from urllib.parse import unquote, urlparse

import yaml

from ycon._schema import use_core_schema
from ycon._uri import reject_extra_parts
from ycon.compression import open_text
from ycon.defaults import load_with_defaults
from ycon.dump import dump_yaml
from ycon.includes import resolve_include
from ycon.refs import Ref, resolve_refs


class IncludeLoader(yaml.SafeLoader):
    """SafeLoader that knows the base directory of the file it's parsing.

    Resolves scalars using YAML 1.2 Core Schema rules for bool/int/float
    rather than PyYAML's default YAML 1.1 rules, so e.g. `yes`/`no`/`on`/
    `off` stay strings, `017` stays the string `"017"` (not octal 15),
    and `12:34` stays a string (not sexagesimal 754).
    """

    def __init__(self, stream, base_dir="."):
        super().__init__(stream)
        self._base_dir = base_dir


use_core_schema(IncludeLoader)


def _resolve_file_path(uri: str, base_dir: str) -> str | None:
    """Resolve a `!include` URI to a local path, or None if not a file."""
    parsed = urlparse(uri)
    if parsed.scheme == "file":
        if parsed.netloc not in ("", "localhost"):
            raise ValueError(f"Unsupported file URI host: {parsed.netloc}")
        reject_extra_parts(uri, parsed, "file URI", allow_path=True)
        return os.path.join(base_dir, unquote(parsed.path))
    if parsed.scheme == "":
        # Plain filenames keep literal URI characters such as # and %.
        return os.path.join(base_dir, uri)
    return None


def _construct_include(loader: IncludeLoader, node: yaml.Node):
    """YAML constructor for `!include`."""
    uri = loader.construct_scalar(node)
    path = _resolve_file_path(uri, loader._base_dir)
    if path is not None:
        return load_yaml(path)
    return resolve_include(uri)


def _construct_ref(loader: IncludeLoader, node: yaml.Node):
    """YAML constructor for `!ref`."""
    return Ref(loader.construct_scalar(node))


IncludeLoader.add_constructor("!include", _construct_include)
IncludeLoader.add_constructor("!ref", _construct_ref)


# Keep include chains isolated between concurrent loads.
_include_stack = ContextVar("include_stack", default=())


def load_yaml(path: str):
    """Parse a YAML file, expanding `!include`s. Raises on include cycles.

    Transparently reads gzip-compressed files when `path` ends in `.gz`.
    """
    path = os.path.abspath(path)
    base_dir = os.path.dirname(path)
    # Resolve symlinks so alternate paths cannot hide an include cycle.
    canonical_path = os.path.realpath(path)
    stack = _include_stack.get()
    if canonical_path in stack:
        raise ValueError(
            "Circular include: " + " -> ".join((*stack, canonical_path))
        )
    # The token restores the parent chain even when parsing fails.
    token = _include_stack.set((*stack, canonical_path))
    try:
        with open_text(path, "rt") as f:
            return yaml.load(
                f, Loader=partial(IncludeLoader, base_dir=base_dir)
            )
    finally:
        _include_stack.reset(token)


def load(path: str, defaults: str | None = None, *, strict: bool = False):
    """Load a YAML config file, resolving `!include`s and `!ref`s.

    If `defaults` is given, it is loaded as a YAML file first and the
    config at `path` is deep-merged on top of it, so `path` only needs
    to specify values that differ from the defaults. If `strict` is
    True, a key in `path` absent from `defaults` raises `ValueError`
    (ignored when `defaults` is not given).
    """
    data = (
        load_with_defaults(path, defaults, strict=strict)
        if defaults is not None
        else load_yaml(path)
    )
    # References use the complete document after all includes are expanded.
    return resolve_refs(data, data)


def resolve_to_file(
    path: str,
    output: str,
    defaults: str | None = None,
    *,
    strict: bool = False,
    ignore_aliases: bool = True,
):
    """Load `path` (see `load`) and write the resolved result to `output`.

    The written file contains plain YAML with no `!include`/`!ref`
    tags left in it. By default, values shared via YAML aliases are
    written out in full at each location; pass `ignore_aliases=False`
    to keep them as YAML anchors/aliases instead.
    """
    dump_yaml(
        load(path, defaults=defaults, strict=strict),
        output,
        ignore_aliases=ignore_aliases,
    )
