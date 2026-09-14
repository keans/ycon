"""Write a fully-resolved config value out as plain YAML."""

import yaml

from ycon.compression import open_text


class _DumperIgnoreAliases(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


class _DumperKeepAliases(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return False


def dump_yaml(data, path: str, *, ignore_aliases: bool = True) -> None:
    """Write `data` to `path` as plain YAML (no custom tags).

    Paths ending in `.gz` are written gzip-compressed. By default,
    values shared via YAML aliases are written out in full at each
    location (no anchors/aliases in the output); pass
    `ignore_aliases=False` to keep them as YAML anchors/aliases instead.
    """
    dumper = _DumperIgnoreAliases if ignore_aliases else _DumperKeepAliases
    with open_text(path, "wt") as f:
        yaml.dump(data, f, Dumper=dumper, sort_keys=False)
