"""Resolve `!ref` placeholders against the fully-loaded document."""

from ycon._tracking import track_active


class Ref:
    """A `!ref <dot.path>` placeholder pending resolution."""

    __slots__ = ("path",)

    def __init__(self, path: str):
        self.path = path


def resolve_refs(data, root):
    """Recursively replace `Ref`s in `data` with values from `root`.

    Detects circular references and reuses already-resolved values
    shared via YAML aliases.
    """
    # Active objects detect cycles; completed objects may be safely reused.
    active = set()
    resolved = {}

    def dereference(value, visiting):
        # Follow paths without resolving unrelated children of a container.
        if not isinstance(value, Ref):
            return value
        identity = id(value)
        with track_active(visiting, identity, "Circular reference"):
            target = root
            seen = []
            for key in value.path.split("."):
                target = dereference(target, visiting)
                seen.append(key)
                try:
                    target = target[key]
                except (KeyError, TypeError) as exc:
                    raise type(exc)(
                        f"!ref {value.path!r} failed at "
                        f"{'.'.join(seen)!r}: {exc}"
                    ) from None
            return dereference(target, visiting)

    def resolve(value):
        """Resolve one value, caching by identity to handle aliases."""
        if not isinstance(value, (Ref, dict, list)):
            return value
        identity = id(value)
        with track_active(
            active, identity, "Circular reference or YAML alias"
        ):
            if identity in resolved:
                return resolved[identity]
            if isinstance(value, Ref):
                result = resolve(dereference(value, set()))
            elif isinstance(value, dict):
                result = {k: resolve(v) for k, v in value.items()}
            else:
                result = [resolve(v) for v in value]
            resolved[identity] = result
            return result

    return resolve(data)
