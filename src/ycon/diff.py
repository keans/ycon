"""Structurally compare two resolved config values or files."""

from math import isnan

from ycon.loader import load


def _join(prefix: str, key) -> str:
    # Brackets distinguish literal dots, empty keys, and non-string keys.
    if not isinstance(key, str) or not key or any(c in key for c in ".[]"):
        return f"{prefix}[{key!r}]"
    return f"{prefix}.{key}" if prefix else key


def _typed_items(mapping):
    # Python otherwise treats True, 1, and 1.0 as the same mapping key.
    return {(type(key), key): value for key, value in mapping.items()}


def _equal(a, b):
    """Compare values without conflating booleans, integers, and floats."""
    if type(a) is not type(b):
        return False
    if isinstance(a, float) and isnan(a) and isnan(b):
        return True
    if isinstance(a, list):
        return len(a) == len(b) and all(
            _equal(left, right) for left, right in zip(a, b)
        )
    if isinstance(a, dict):
        left, right = _typed_items(a), _typed_items(b)
        return left.keys() == right.keys() and all(
            _equal(value, right[key]) for key, value in left.items()
        )
    return a == b


def diff_configs(a, b, *, _prefix: str = ""):
    """Return how `b` differs from `a` as dotted-path mappings.

    The result has three keys: `added` (present only in `b`),
    `removed` (present only in `a`), and `changed` (present in both,
    with different values, as `{path: (old, new)}`). Dict values are
    compared key by key recursively; types are significant. Keys that
    cannot use dotted notation are represented with brackets and repr().
    Any other differing values (including whole lists) are reported as
    a single change. NaN values compare equal for configuration diffs.
    """
    added, removed, changed = {}, {}, {}

    if isinstance(a, dict) and isinstance(b, dict):
        left, right = _typed_items(a), _typed_items(b)
        for token in left.keys() - right.keys():
            removed[_join(_prefix, token[1])] = left[token]
        for token in right.keys() - left.keys():
            added[_join(_prefix, token[1])] = right[token]
        for token in left.keys() & right.keys():
            sub = diff_configs(
                left[token], right[token], _prefix=_join(_prefix, token[1])
            )
            added.update(sub["added"])
            removed.update(sub["removed"])
            changed.update(sub["changed"])
    elif not _equal(a, b):
        changed[_prefix or "."] = (a, b)

    return {"added": added, "removed": removed, "changed": changed}


def compare_files(path_a: str, path_b: str, *, defaults: str | None = None):
    """Load and fully resolve `path_a` and `path_b`, then diff them.

    `defaults` (if given) is applied to both files, as in `load()`.
    """
    a = load(path_a, defaults=defaults)
    b = load(path_b, defaults=defaults)
    return diff_configs(a, b)
