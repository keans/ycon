"""Shared validation for `!include` URI parsing."""

from urllib.parse import ParseResult


def reject_extra_parts(
    uri: str, parsed: ParseResult, label: str, *, allow_path=False
):
    """Raise ValueError if `parsed` has parts `label`'s scheme doesn't
    expect: a query, a fragment, or (unless `allow_path`) a path.
    """
    if parsed.query or parsed.fragment or (parsed.path and not allow_path):
        raise ValueError(f"Unsupported {label}: {uri!r}")
