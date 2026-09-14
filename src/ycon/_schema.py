"""Restrict a PyYAML loader to YAML 1.2 Core Schema scalar resolution.

PyYAML's built-in resolvers follow YAML 1.1, which has surprises for
config files: `yes`/`no`/`on`/`off` resolve to booleans, colon-separated
numbers like `12:34` resolve to sexagesimal integers, and bare
leading-zero digits like `017` resolve to octal. YAML 1.2's Core Schema
drops all of that: only `true`/`false` (in a few cases) are booleans,
and octal/hex integers require an explicit `0o`/`0x` prefix.
"""

import re

_BOOL_TAG = "tag:yaml.org,2002:bool"
_INT_TAG = "tag:yaml.org,2002:int"
_FLOAT_TAG = "tag:yaml.org,2002:float"

_BOOL_RE = re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$")
_INT_RE = re.compile(r"^[-+]?(?:0|[1-9][0-9]*|0o[0-7]+|0x[0-9a-fA-F]+)$")
_FLOAT_RE = re.compile(
    # A dot or exponent must be present, or this is an int, not a float.
    r"^[-+]?(?:[0-9]+\.[0-9]*|\.[0-9]+|[0-9]+[eE][-+]?[0-9]+"
    r"|[0-9]+\.[0-9]*[eE][-+]?[0-9]+|\.[0-9]+[eE][-+]?[0-9]+)$"
    r"|^[-+]?\.(?:inf|Inf|INF)$"
    r"|^\.(?:nan|NaN|NAN)$"
)


def use_core_schema(loader_cls):
    """Replace `loader_cls`'s bool/int/float resolvers with YAML 1.2's.

    Mutates `loader_cls` in place; other resolvers (null, timestamp,
    merge, ...) are left untouched.
    """
    restricted = {_BOOL_TAG, _INT_TAG, _FLOAT_TAG}
    loader_cls.yaml_implicit_resolvers = {
        first: [
            (tag, regex) for tag, regex in resolvers if tag not in restricted
        ]
        for first, resolvers in loader_cls.yaml_implicit_resolvers.items()
    }
    loader_cls.add_implicit_resolver(_BOOL_TAG, _BOOL_RE, list("tTfF"))
    loader_cls.add_implicit_resolver(_INT_TAG, _INT_RE, list("-+0123456789"))
    loader_cls.add_implicit_resolver(
        _FLOAT_TAG, _FLOAT_RE, list("-+0123456789.")
    )
