import pytest

from ycon import load


def load_pair(tmp_path, base, override):
    defaults = tmp_path / "defaults.yaml"
    path = tmp_path / "config.yaml"
    defaults.write_text(base)
    path.write_text(override)
    return load(path, defaults=defaults)


def test_deep_defaults_and_refs_use_final_values(tmp_path):
    assert load_pair(
        tmp_path,
        "db:\n  connection:\n    host: localhost\n    port: 5432\n"
        "host_copy: !ref db.connection.host\n",
        "db:\n  connection:\n    host: production\n"
        "port_copy: !ref db.connection.port\n",
    ) == {
        "db": {"connection": {"host": "production", "port": 5432}},
        "host_copy": "production",
        "port_copy": 5432,
    }


@pytest.mark.parametrize(
    ("override", "expected"),
    [
        ("null", None),
        ("false", False),
        ("0", 0),
        ("''", ""),
        ("[]", []),
        ("{}", {"nested": "default"}),
    ],
)
def test_explicit_overrides(tmp_path, override, expected):
    assert load_pair(
        tmp_path, "value: {nested: default}\n", f"value: {override}\n"
    ) == {"value": expected}


@pytest.mark.parametrize("empty", ["", "# no overrides\n", "null\n", "{}\n"])
def test_empty_config_uses_defaults(tmp_path, empty):
    assert load_pair(tmp_path, "value: default\n", empty) == {
        "value": "default"
    }


def test_empty_defaults(tmp_path):
    assert load_pair(tmp_path, "", "value: configured\n") == {
        "value": "configured"
    }


@pytest.mark.parametrize("invalid", ["[]\n", "42\n", "hello\n"])
@pytest.mark.parametrize("side", ["defaults", "config"])
def test_non_mapping_documents_raise_clear_error(tmp_path, invalid, side):
    base, override = (invalid, "{}") if side == "defaults" else ("{}", invalid)
    with pytest.raises(TypeError, match="mapping"):
        load_pair(tmp_path, base, override)


def test_overlapping_recursive_aliases_raise_clear_error(tmp_path):
    with pytest.raises(ValueError, match="Circular"):
        load_pair(tmp_path, "&loop {self: *loop}", "&loop {self: *loop}")


def test_defaults_includes_merge_with_config_includes(tmp_path):
    shared = tmp_path / "shared"
    shared.mkdir()
    (shared / "db.yaml").write_text("host: localhost\nport: 5432\n")
    defaults = shared / "defaults.yaml"
    defaults.write_text("db: !include db.yaml\n")
    (tmp_path / "db.yaml").write_text("port: 6543\n")
    path = tmp_path / "config.yaml"
    path.write_text("db: !include db.yaml\n")
    assert load(path, defaults=defaults) == {
        "db": {"host": "localhost", "port": 6543}
    }


def test_empty_defaults_path_is_not_silently_ignored(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("value: hello\n")
    with pytest.raises(OSError):
        load(path, defaults="")


def test_strict_rejects_unknown_top_level_key(tmp_path):
    defaults = tmp_path / "defaults.yaml"
    defaults.write_text("host: localhost\n")
    path = tmp_path / "config.yaml"
    path.write_text("typo_host: production\n")
    with pytest.raises(ValueError, match="typo_host"):
        load(path, defaults=defaults, strict=True)


def test_strict_rejects_unknown_nested_key(tmp_path):
    defaults = tmp_path / "defaults.yaml"
    defaults.write_text("database:\n  host: localhost\n")
    path = tmp_path / "config.yaml"
    path.write_text("database:\n  hots: production\n")
    with pytest.raises(ValueError, match=r"database\.hots"):
        load(path, defaults=defaults, strict=True)


def test_strict_allows_known_keys(tmp_path):
    defaults = tmp_path / "defaults.yaml"
    defaults.write_text("host: localhost\nport: 5432\n")
    path = tmp_path / "config.yaml"
    path.write_text("port: 6543\n")
    assert load(path, defaults=defaults, strict=True) == {
        "host": "localhost",
        "port": 6543,
    }


def test_strict_defaults_to_false(tmp_path):
    defaults = tmp_path / "defaults.yaml"
    defaults.write_text("host: localhost\n")
    path = tmp_path / "config.yaml"
    path.write_text("typo_host: production\n")
    assert load(path, defaults=defaults) == {
        "host": "localhost",
        "typo_host": "production",
    }
