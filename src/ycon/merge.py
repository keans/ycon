"""Deep-merge nested dicts, e.g. config values over defaults."""

from ycon._tracking import track_active


def deep_merge(base: dict, override: dict, *, strict: bool = False) -> dict:
    """Merge `override` onto `base`, recursing into nested dicts.

    Non-dict values (including lists) in `override` replace the
    corresponding value in `base` outright. Neither input is modified.
    If `strict` is True, an override key absent from the corresponding
    level of `base` raises `ValueError`.
    """
    if not isinstance(base, dict) or not isinstance(override, dict):
        raise TypeError(
            "Defaults and config must be mappings, got "
            f"{type(base).__name__} and {type(override).__name__}"
        )
    active = set()

    def merge(left, right, path):
        # Only pairs on the current branch are cycles; aliases may repeat.
        pair = (id(left), id(right))
        with track_active(
            active, pair, "Circular YAML alias while merging defaults"
        ):
            result = dict(left)
            for key, value in right.items():
                key_path = f"{path}.{key}" if path else str(key)
                if strict and key not in left:
                    raise ValueError(
                        f"Unknown override key not present in "
                        f"defaults: {key_path!r}"
                    )
                existing = result.get(key)
                if isinstance(existing, dict) and isinstance(value, dict):
                    result[key] = merge(existing, value, key_path)
                else:
                    result[key] = value
            return result

    return merge(base, override, "")
