import pytest

from ycon import load
from ycon.includes import MissingEnvVarError


@pytest.fixture
def config_dir(tmp_path):
    (tmp_path / "child.yaml").write_text("nested:\n  key: hello-from-child\n")
    return tmp_path


def write_base(config_dir, content):
    path = config_dir / "base.yaml"
    path.write_text(content)
    return path


def test_include_file(config_dir):
    path = write_base(config_dir, "child: !include child.yaml\n")
    result = load(str(path))
    assert result == {"child": {"nested": {"key": "hello-from-child"}}}


def test_include_env(config_dir, monkeypatch):
    monkeypatch.setenv("MY_VAR", "world")
    path = write_base(config_dir, "some_env: !include env://MY_VAR\n")
    result = load(str(path))
    assert result == {"some_env": {"value": "world"}}


def test_include_env_missing(config_dir, monkeypatch):
    monkeypatch.delenv("DOES_NOT_EXIST", raising=False)
    path = write_base(config_dir, "x: !include env://DOES_NOT_EXIST\n")
    with pytest.raises(MissingEnvVarError, match="DOES_NOT_EXIST"):
        load(str(path))


def test_include_unsupported_scheme(config_dir):
    path = write_base(config_dir, "x: !include ftp://foo\n")
    with pytest.raises(ValueError, match="Unsupported scheme: ftp"):
        load(str(path))


def test_include_db_not_implemented(config_dir):
    path = write_base(config_dir, "x: !include db://record1\n")
    with pytest.raises(NotImplementedError):
        load(str(path))


def test_ref_within_top_level(config_dir):
    path = write_base(
        config_dir,
        "value: hello\nreferenced: !ref value\n",
    )
    result = load(str(path))
    assert result == {"value": "hello", "referenced": "hello"}


def test_ref_into_included_file(config_dir):
    path = write_base(
        config_dir,
        "child: !include child.yaml\nreferenced: !ref child.nested.key\n",
    )
    result = load(str(path))
    assert result["referenced"] == "hello-from-child"


def test_ref_missing_key_raises(config_dir):
    path = write_base(config_dir, "referenced: !ref does.not.exist\n")
    with pytest.raises(KeyError):
        load(str(path))


def test_nested_include(config_dir):
    (config_dir / "grandchild.yaml").write_text("value: deep\n")
    (config_dir / "child.yaml").write_text(
        "nested:\n  key: hello-from-child\ngrandchild: !include grandchild.yaml\n"
    )
    path = write_base(config_dir, "child: !include child.yaml\n")
    result = load(str(path))
    assert result["child"]["grandchild"] == {"value": "deep"}


def test_reload_observes_file_changes(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("value: first\n")
    assert load(path) == {"value": "first"}
    path.write_text("value: second\n")
    assert load(path) == {"value": "second"}


def test_reload_observes_env_changes(tmp_path, monkeypatch):
    path = tmp_path / "config.yaml"
    path.write_text("value: !include env://MY_VAR\n")
    monkeypatch.setenv("MY_VAR", "first")
    assert load(path)["value"] == {"value": "first"}
    monkeypatch.setenv("MY_VAR", "second")
    assert load(path)["value"] == {"value": "second"}


def test_chained_and_container_refs(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text(
        "first: !ref second\nsecond: !ref value\nvalue: hello\n"
        "group:\n  item: !ref first\ncopy: !ref group\n"
        "nested: !ref copy.item\n"
    )
    assert load(path) == {
        "first": "hello",
        "second": "hello",
        "value": "hello",
        "group": {"item": "hello"},
        "copy": {"item": "hello"},
        "nested": "hello",
    }


@pytest.mark.parametrize(
    "content",
    [
        "a: !ref a\n",
        "a: !ref b\nb: !ref a\n",
        "a:\n  b: !ref a\n",
        "a: &loop [*loop]\n",
    ],
)
def test_reference_cycles(tmp_path, content):
    path = tmp_path / "config.yaml"
    path.write_text(content)
    with pytest.raises(ValueError, match="Circular"):
        load(path)


def test_include_cycle_and_recovery(tmp_path):
    path = tmp_path / "config.yaml"
    child = tmp_path / "child.yaml"
    path.write_text("child: !include child.yaml\n")
    child.write_text("parent: !include config.yaml\n")
    with pytest.raises(ValueError, match="Circular include"):
        load(path)
    child.write_text("value: ok\n")
    assert load(path) == {"child": {"value": "ok"}}


def test_file_uri_and_plain_filename(tmp_path):
    child = tmp_path / "child #1.yaml"
    child.write_text("value: ok\n")
    path = tmp_path / "config.yaml"
    path.write_text(
        f"a: !include '{child.as_uri()}'\nb: !include 'child #1.yaml'\n"
    )
    assert load(path) == {"a": {"value": "ok"}, "b": {"value": "ok"}}


def test_repeated_includes_and_aliases_are_not_cycles(tmp_path):
    (tmp_path / "child.yaml").write_text("value: hello\n")
    path = tmp_path / "config.yaml"
    path.write_text(
        "a: !include child.yaml\nb: !include child.yaml\n"
        "c: &shared {value: hello}\nd: *shared\n"
        "e: !ref c\nf: !ref c.value\n"
    )
    result = load(path)
    for key in "abcde":
        assert result[key] == {"value": "hello"}
    assert result["f"] == "hello"


def test_file_uri_rejects_remote_host(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("value: !include file://remote/config.yaml\n")
    with pytest.raises(ValueError, match="Unsupported file URI host"):
        load(path)


def test_load_merges_over_defaults(tmp_path):
    defaults = tmp_path / "defaults.yaml"
    defaults.write_text("host: localhost\nport: 5432\n")
    path = tmp_path / "config.yaml"
    path.write_text("port: 6543\n")
    assert load(path, defaults=defaults) == {
        "host": "localhost",
        "port": 6543,
    }


def test_load_without_defaults_ignores_defaults_file(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("port: 6543\n")
    assert load(path) == {"port": 6543}


def test_load_refs_can_point_into_defaults(tmp_path):
    defaults = tmp_path / "defaults.yaml"
    defaults.write_text("host: localhost\n")
    path = tmp_path / "config.yaml"
    path.write_text("db_host: !ref host\n")
    result = load(path, defaults=defaults)
    assert result["db_host"] == "localhost"
