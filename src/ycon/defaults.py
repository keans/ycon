"""Merge a config file over a shared defaults file."""

from ycon.merge import deep_merge


def load_with_defaults(path: str, defaults: str, *, strict: bool = False):
    """Load `path`, deep-merged on top of the YAML file at `defaults`.

    Empty YAML documents contribute no values to the merge. If
    `strict` is True, a key in `path` absent from `defaults` (at any
    nesting level) raises `ValueError`.
    """
    from ycon.loader import load_yaml

    base = load_yaml(defaults)
    data = load_yaml(path)
    return deep_merge(
        {} if base is None else base,
        {} if data is None else data,
        strict=strict,
    )
